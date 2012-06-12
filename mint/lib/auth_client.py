#
# Copyright (c) 2011 rPath, Inc.
#

import hashlib
import socket
import time


_clientCache = {}


def getClient(path):
    if path in _clientCache:
        return _clientCache[path]
    if path:
        client = AuthClient(path)
    else:
        client = DummyAuth()
    _clientCache[path] = client
    return client


class DummyAuth(object):

    def checkPassword(self, username, password):
        return False


class AuthClient(object):

    def __init__(self, path):
        self.path = path
        self.sock = None
        self._ctr = 0
        self._cache = AuthCache()

    def checkPassword(self, username, password):
        # Check the local cache first.
        result = self._cache.get((username, password))
        if result is None:
            result = self._checkPassword(username, password)
            self._cache.put((username, password), result)
        return result

    def _connect(self):
        if self.sock:
            self.sock.close()
            self.sock = None
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.path)
        self.sock = sock

    def _checkPassword(self, username, password):
        if self.sock:
            # Recycle existing socket, but retry if it fails.
            try:
                return self._checkPasswordOnce(username, password)
            except socket.error:
                self._connect()
        else:
            self._connect()
        # Freshly opened socket
        return self._checkPasswordOnce(username, password)

    def _checkPasswordOnce(self, username, password):
        requestId, self._ctr = self._ctr, self._ctr + 1
        challenge = "\0%s\0%s" % (username, password)
        challenge = challenge.encode('base64').replace('\n', '')
        self.sock.sendall("AUTH\t%d\tPLAIN\tresp=%s\n"
                % (requestId, challenge))
        buf = ''
        while '\n' not in buf:
            data = self.sock.recv(4096)
            if not data:
                break
            buf += data
        line = buf.split('\n')[0]
        if not line:
            raise RuntimeError(
                    "Authentication server hung up without responding")
        words = line.split('\t')
        result, resultId, words = words[0], words[1], words[2:]
        if result == 'OK':
            return True
        return False


class AuthCache(object):

    # Timeout for caching a successful authentication
    successTimeout = 60
    # Timeout for caching a failed authentication
    failureTimeout = 3

    def __init__(self):
        self.cache = {}

    @staticmethod
    def _makeKey(key):
        key = '\0'.join(key)
        return hashlib.sha1(hashlib.sha1(key).digest()).digest()

    def get(self, key):
        key = self._makeKey(key)
        cached = self.cache.get(key)
        if not cached:
            return None
        expiry, value = cached
        if expiry < time.time():
            del self.cache[key]
            return None
        else:
            return value

    def put(self, key, value):
        key = self._makeKey(key)
        expiry = time.time()
        if value:
            expiry += self.successTimeout
        else:
            expiry += self.failureTimeout
        self.cache[key] = expiry, value

    def scrub(self):
        now = time.time()
        for key, (expiry, value) in self.cache.items():
            if expiry < now:
                del self.cache[key]
