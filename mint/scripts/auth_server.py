#
# Copyright (c) 2011 rPath, Inc.
#

import pam
from twisted.internet import protocol as ti_protocol
from twisted.protocols import basic as tp_basic
from twisted.python import log as tp_log

from mint.lib.auth_client import AuthCache

"""
A simple authentication protocol based loosely on the Dovecot auth protocol
v1.1. It does away with all the handshaking and supports only the AUTH command
with the PLAIN mechanism. However, the protocol is sufficiently similar that
the server could also support the full auth protocol.
"""


class AuthServerProtocol(tp_basic.LineReceiver):

    delimiter = '\n'

    def lineReceived(self, line):
        words = line.split('\t')
        command, words = words[0], words[1:]
        command = command.upper()
        method = getattr(self, 'command_' + command, None)
        if method is None:
            return self.bailOut("Got unknown command %r" % (command,))
        try:
            method(words)
        except:
            tp_log.err(None, "Unhandled exception in command %r" % (command,))
            self.transport.loseConnection()

    def bailOut(self, msg):
        tp_log.msg(msg)
        self.transport.loseConnection()

    def sendWords(self, *words):
        self.sendLine('\t'.join(words))

    def command_AUTH(self, words):
        if len(words) < 2:
            return self.bailOut("Not enough arguments to AUTH command")
        requestId, mechanism, words = words[0], words[1], words[2:]
        params = {}
        for word in words:
            if '=' in word:
                key, value = word.split('=', 1)
            else:
                key, value = word, True
            params[key] = value

        if mechanism != 'PLAIN':
            return self.sendWords('FAIL', requestId,
                    'reason=unsupported mechanism')
        if 'resp' not in params:
            return self.sendWords('FAIL', requestId,
                    'reason=expected initial resp')
        try:
            payload = params['resp'].decode('base64')
        except:
            return self.sendWords('FAIL', requestId,
                    'reason=invalid base64 data')
        if payload.count('\0') != 2:
            return self.sendWords('FAIL', requestId,
                    'reason=invalid PLAIN data')
        authzid, authcid, password = payload.split('\0')
        if authzid and authzid != authcid:
            # authorization different from authentication not allowed
            return self.sendWords('FAIL', requestId)

        if self.factory.checkPassword(authcid, password):
            return self.sendWords('OK', requestId)
        else:
            return self.sendWords('FAIL', requestId)


class AuthServerFactory(ti_protocol.ServerFactory):

    protocol = AuthServerProtocol
    pamService = 'rbuilder'

    def __init__(self):
        self._cache = AuthCache()

    def checkPassword(self, username, password):
        result = self._cache.get((username, password))
        if result is None:
            result = self._checkPAM(username, password)
            self._cache.put((username, password), result)
        tp_log.msg("checkPassword(%r) = %r" % (username, result))
        return result

    def _checkPAM(self, username, password):
        if '\\' in username:
            domain, user = username.split('\\')
            username = '%s@%s' % (user, domain.upper())
        elif '@' in username:
            user, domain = username.split('@')
            username = '%s@%s' % (user, domain.upper())
        return pam.authenticate(username, password, self.pamService)
