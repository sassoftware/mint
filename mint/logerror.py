#
# Copyright (c) SAS Institute Inc.
#

"""
Methods for logging and reporting errors.
"""

import logging
import os
import socket
import sys
import tempfile
import time
import traceback
from conary.lib import util as conary_util

from mint.mint_error import MailError
from mint.lib import maillib

log = logging.getLogger(__name__)


def logWebErrorAndEmail(req, cfg, e_type, e_value, e_tb,
        location='web interface', doEmail=True):
    log.error('sending mail to %s and %s' % (cfg.bugsEmail, cfg.smallBugsEmail))
    try:
        logErrorAndEmail(cfg, e_type, e_value, e_tb, location, req.environ,
                doEmail=doEmail)
    except MailError, error:
        log.error("Failed to send e-mail to %s, reason: %s" %
            (cfg.bugsEmail, str(error)))


def logErrorAndEmail(cfg, e_type, e_value, e_tb, location, info_dict,
  prefix='mint-error-', smallStream=None, doEmail=True):
    timeStamp = time.ctime(time.time())
    realHostName = socket.getfqdn()

    if 'mint.authToken' in info_dict:
        info_dict['mint.authToken'] = repr(info_dict['mint.authToken'])
    if 'HTTP_AUTHORIZATION' in info_dict:
        info_dict['HTTP_AUTHORIZATION'] = info_dict['HTTP_AUTHORIZATION'].split()[0] + ' ******'

    # Format large traceback to file
    (tbFd, tbPath) = tempfile.mkstemp('.txt', prefix)
    large = os.fdopen(tbFd, 'w+')
    print >> large, ('Unhandled exception from %s on %s:'
        % (location, realHostName))
    print >> large, 'Time of occurrence: %s' % timeStamp
    print >> large, 'See also: %s' % tbPath
    print >> large
    conary_util.formatTrace(e_type, e_value, e_tb, stream=large,
        withLocals=False)
    print >> large
    print >> large, 'Full stack:'
    print >> large
    try:
        conary_util.formatTrace(e_type, e_value, e_tb, stream=large,
            withLocals=True)
    except:
        # The extended traceback formatter can crash when uncooperative
        # objects do something special when marshalled. For example,
        # derivatives of Thread may abort before Thread itself is
        # initialized, which causes __repr__ to crash, and
        # ServerProxy derivatives may crash when __safe_str__ is
        # improperly sent as a remote procedure call instead of
        # throwing an AttributeError.
        #
        # None of these conditions should prevent the original
        # exception from being logged and emailed, if only in their
        # short form.

        handlerErrorType, handlerErrorValue, handlerErrorTB = sys.exc_info()
        print >> large
        print >> large, '*** Traceback formatter crashed! ***'
        print >> large, 'Formatter crash follows:'
        conary_util.formatTrace(handlerErrorType, handlerErrorValue,
            handlerErrorTB, stream=large, withLocals=False)
        print >> large, '*** End formatter crash log ***'
    print >> large
    print >> large, 'Environment:'
    for key, val in sorted(info_dict.items()):
        try:
            print >> large, '%s: %s' % (key, val)
        except:
            pass

    # Format small traceback
    small = conary_util.BoundedStringIO()
    print >> small, ('Unhandled exception from %s on %s:'
        % (location, realHostName))
    conary_util.formatTrace(e_type, e_value, e_tb, stream=small,
        withLocals=False)
    print >> small, 'Extended traceback at %s' % tbPath

    if cfg and cfg.sentryDSN:
        from raven import Client
        from raven.utils import wsgi
        client = Client(cfg.sentryDSN)
        data = {}
        extra = {
                'environ': info_dict,
                'reference': '%s:%s' % (realHostName, tbPath),
                }
        if 'REQUEST_METHOD' in info_dict:
            # Looks like WSGI
            environ = info_dict
            data['sentry.interfaces.Http'] = {
                'method': environ.get('REQUEST_METHOD'),
                'url': wsgi.get_current_url(environ, strip_querystring=True),
                'query_string': environ.get('QUERY_STRING'),
                'headers': dict(wsgi.get_headers(environ)),
                'env': dict(wsgi.get_environ(environ)),
                }
        sentry_id = client.captureException(exc_info=(e_type, e_value, e_tb),
                data=data, extra=extra)
        print >> large, "Sentry event ID: ", sentry_id[0]
        print >> small, "Sentry event ID: ", sentry_id[0]

    small.seek(0)
    log.error(small.read())

    # send email
    if cfg and doEmail:
        base_exception = traceback.format_exception_only(
            e_type, e_value)[-1].strip()
        if cfg.rBuilderOnline:
            subject = '%s: %s' % (realHostName, base_exception)
        else:
            extra = {'hostname': realHostName}
            subject = cfg.bugsEmailSubject % extra

        if cfg.bugsEmail:
            large.seek(0)
            maillib.sendMailWithChecks(cfg.bugsEmail, cfg.bugsEmailName,
                                     cfg.bugsEmail, subject, large.read())
        if cfg.smallBugsEmail:
            small.seek(0)
            maillib.sendMailWithChecks(cfg.bugsEmail, cfg.bugsEmailName,
                cfg.smallBugsEmail, subject, small.read())

    large.close()
