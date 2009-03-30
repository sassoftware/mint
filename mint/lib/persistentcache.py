#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#

import cPickle as pickle
import errno
import os
from conary.lib.util import mkdirChain
from mint.lib.unixutils import atomicOpen

class PersistentCache(object):

    def __init__(self, cacheFile):
        self._cachefile = cacheFile
        self._data = dict()
        self._load()

    def _load(self):
        fObj = None
        try:
            fObj = file(self._cachefile, 'rb')
        except IOError, ioe:
            if ioe.args[0] == errno.ENOENT:
                # No such file or directory
                self._persist()
            else:
                raise
        else:
            self._data = pickle.load(fObj)

    def _persist(self):
        if not os.path.exists(os.path.dirname(self._cachefile)):
            mkdirChain(os.path.dirname(self._cachefile))

        fObj = atomicOpen(self._cachefile)
        pickle.dump(self._data, fObj)
        fObj.commit()

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

