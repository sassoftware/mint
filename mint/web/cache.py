#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
# An in-memory page cache for non-logged-in users

import time
import sys

def cache(func):
    func.cacheable = True
    return func 

class AgedDict:
    ages = {}
    values = {}

    def __init__(self, maxAge = 300):
        self.maxAge = maxAge

    def __setitem__(self, key, val):
        self.ages[key] = time.time()
        self.values[key] = val

    def __getitem__(self, key):
        if key not in self.values or key not in self.ages:
            raise AttributeError

        # value too old
        if time.time() > (self.ages[key] + self.maxAge):
            del self.ages[key]
            del self.values[key]
            raise AttributeError

        return self.values[key]

    def __contains__(self, key):
        contains = key in self.values and key in self.ages and time.time() < (self.ages[key] + self.maxAge)
        return contains

def reqHash(req):
    return (req.hostname, req.unparsed_uri, req.content_type)

global pageCache
pageCache = AgedDict(maxAge = 300)

