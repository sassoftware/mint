#
# Copyright (c) 2005 rpath, Inc.
#
# All rights reserved
#
import time

TROVE_NAMES_CACHE_TIMEOUT = 300

class TroveNamesCache:
    troveNames = {}
    invalidateTime = 0

    def getTroveNames(self, label, netclient):
        if self.invalidateTime < time.time() or label not in self.troveNames:
            self.troveNames[label] = netclient.troveNames(label)
            self.invalidateTime = time.time() + TROVE_NAMES_CACHE_TIMEOUT
        return self.troveNames[label]
