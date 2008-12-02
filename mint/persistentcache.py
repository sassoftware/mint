#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#

import cPickle as pickle
import os
import fcntl

from conary.lib.util import mkdirChain

class PersistentCache(object):

    def __init__(self, cacheFile):
        self._cachefile = cacheFile
        self._data = dict()
        self._load()

    def _load(self):
        f = None
        try:
            try:
                f = file(self._cachefile, 'rb')
            except IOError, ioe:
                if ioe.errno == 2: # file doesn't exist
                    self._persist()
                    return
                else:
                    raise
            fcntl.flock(f, fcntl.LOCK_SH)
            self._data = pickle.load(f)
        finally:
            if f: f.close()

    def _persist(self):
        if not os.path.exists(os.path.dirname(self._cachefile)):
            mkdirChain(os.path.dirname(self._cachefile))
        f = file(self._cachefile, 'wb')
        try:
            fcntl.flock(f, fcntl.LOCK_EX)
            pickle.dump(self._data, f)
        finally:
            if f: f.close()

    def _update(self, key, value):
        self._data[key] = value
        self._persist()
        return self._data[key]

    def _refresh(self, key):
        raise NotImplementedError

    def clear(self):
        self._data = dict()
        self._persist()

    def get(self, key):
        try:
            return self._data[key]
        except KeyError:
            newValue = self.refresh(key)
            self._persist()
            return newValue

    def refresh(self, key):
        return self._update(key, self._refresh(key))

