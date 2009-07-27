#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#

"""
Persistent on disk cache.

Stores a dictionary of data on disk in a pickle.
"""

import os
import time
import errno
import cPickle as pickle
from conary.lib.util import mkdirChain
from mint.lib.unixutils import hashFile
from mint.lib.unixutils import atomicOpen

class PersistentCache(object):
    def __init__(self, cacheFile):
        self._cachefile = cacheFile
        self._data = dict()
        self._lastHash = None

        # Time (in seconds) before a the cache will try to refresh a negative
        # cache entry.
        self._negativeExpire = 5 * 60 # 5 Minutes

        self._load()

    def _load(self):
        """
        Load data from the cache file if the file has changed since the last
        time it was loaded.
        """

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
            # Hash the cache file 
            if self._lastHash is None:
                self._lastHash = hashFile(fObj)

            # Only load data if the file has changed.
            elif self._lastHash == hashFile(fObj):
                return

            self._data = pickle.load(fObj)

    def _persist(self):
        """
        Write data to the cache file.
        """

        if not os.path.exists(os.path.dirname(self._cachefile)):
            mkdirChain(os.path.dirname(self._cachefile))

        fObj = atomicOpen(self._cachefile)
        pickle.dump(self._data, fObj)
        self._lastHash = fObj.commit()

    def _update(self, key, value):
        """
        Update both the local dictionary and the on disk cache.
        """

        self._data[key] = (value, time.time())
        self._persist()
        return value

    def _refresh(self, key):
        """
        Method to be implemented by sub classes for fetching data.
        """

        raise NotImplementedError

    def clear(self):
        """
        Clear all cached data.
        """

        self._data = dict()
        self._persist()

    def get(self, key):
        """
        Get the value for a given key.
        """

        if key in self._data:
            value = self._data[key]

            # Added for backwards compatability with already existing
            # cache files.
            if type(value) != tuple:
                return value

            # Return possitive cached item.
            elif value[0] is not None:
                return value[0]

            # Check to see if a negative cached item has expired, refresh
            # if expired
            elif (value[0] is None and
                  time.time() > self._value[1] + self._negativeExpire):
                return self.refresh(key)

        else:
            return self.refresh(key)

    def refresh(self, key):
        """
        Fetch data for a given key that is not in the cache.
        """

        self._load()
        return self._update(key, self._refresh(key))
