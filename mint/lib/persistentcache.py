#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


"""
Persistent on disk cache.

Stores a dictionary of data on disk in a pickle.
"""

import os
import time
import cPickle as pickle
from conary.lib.util import mkdirChain, fopenIfExists
from mint.lib.unixutils import hashFile
from mint.lib.unixutils import atomicOpen

class PersistentCache(object):
    # Time (in seconds) before a cached entry is considered stale, and
    # re-generated
    _expiration = 24 * 3600 # one day
    # Time (in seconds) before the cache will try to refresh a negative
    # cache entry.
    _negativeExpire = 5 * 60 # 5 Minutes
    _undefined = object()

    def __init__(self, cacheFile):
        self._cachefile = cacheFile
        self._data = dict()
        self._lastHash = None
        self._dirtyKeys = set()
        self._removedKeys = set()
        self._dirty = False

    def _load(self, create=True, truncate=False):
        """
        Load data from the cache file if the file has changed since the last
        time it was loaded.
        """

        fObj = fopenIfExists(self._cachefile, 'rb')
        if fObj is None:
            if truncate:
                self._data.clear()
                self._dirty = True
            if create:
                self._persist()
        else:
            self._loadFromFile(fObj)

    def _loadFromFile(self, fObj):
        # Hash the cache file 
        fileHash = hashFile(fObj)
        if self._lastHash == fileHash:
            self._dirty = bool(self._dirtyKeys) or bool(self._removedKeys)
            return
        self._lastHash = fileHash
        # Save dirty data
        dirty = [ (k, self._data[k]) for k in self._dirtyKeys ]
        self._data = pickle.load(fObj)
        # And add it back
        self._data.update(dirty)
        if not self._dirty:
            self._dirty = bool(dirty)
        for removed in self._removedKeys:
            val = self._data.pop(removed, self._undefined)
            if val is not self._undefined:
                self._dirty = True

    def _persist(self):
        """
        Write data to the cache file.
        """

        mkdirChain(os.path.dirname(self._cachefile))
        self._load(create=False)
        self._dirtyKeys.clear()
        self._removedKeys.clear()
        if not self._dirty:
            return

        fObj = atomicOpen(self._cachefile)
        pickle.dump(self._data, fObj)
        self._lastHash = fObj.commit()
        self._dirty = False

    def _update(self, key, value, timestamp=None, commit=True):
        """
        Update both the local dictionary and the on disk cache.
        """
        return self._updateMany([(key, value)], timestamp=timestamp,
            commit=commit)[0]

    def _updateMany(self, values, timestamp=None, commit=True):
        if timestamp is None:
            timestamp = time.time()
        ret = []
        for key, value in values:
            self._data[key] = (value, timestamp)
            ret.append(value)
            self._dirtyKeys.add(key)
        if commit:
            self._persist()
        return ret

    def _refresh(self, key, **kwargs):
        """
        Method to be implemented by sub classes for fetching data.
        """

        raise NotImplementedError

    def clear(self):
        """
        Clear all cached data.
        """
        self._load()
        self._removedKeys.update(self._data)
        self._data.clear()
        self._persist()

    def clearKey(self, key, commit=True):
        """
        Clear one specific key.
        """
        # No need to load data here, self._persist will reload
        self._removedKeys.add(key)
        self._data.pop(key, None)
        if commit:
            self._persist()

    def get(self, key, **kwargs):
        """
        Get the value for a given key.
        """

        self._load(truncate=True)
        if key in self._data:
            value = self._data[key]

            # Added for backwards compatability with already existing
            # cache files.
            if type(value) != tuple:
                self._update(key, value)
                return value
            value, timestamp = value[:2]
            now = time.time()
            if value is not None:
                if timestamp + self._expiration > now:
                    # Return positive cached item.
                    return value
            else:
                if timestamp + self._negativeExpire > now:
                    # Negative cache is still fresh.
                    return None

        return self.refresh(key, **kwargs)

    def refresh(self, key, **kwargs):
        """
        Fetch data for a given key that is not in the cache.
        """

        return self._update(key, self._refresh(key, **kwargs))
