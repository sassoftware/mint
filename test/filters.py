#!/usr/bin/python2.4
#
# Copyright (c) 2006 rPath, Inc.
#
from mint.shimclient import _ShimMethod
import __builtin__

def enforceBuiltin(result):
    failure = False
    if isinstance(result, (list, tuple)):
        for item in result:
            failure = failure or enforceBuiltin(item)
    elif isinstance(result, dict):
        for item in result.values():
            failure = failure or enforceBuiltin(item)
    failure =  failure or (result.__class__.__name__ \
                           not in __builtin__.__dict__)
    return failure

class _FilteredShimMethod(_ShimMethod):
    def __call__(self, *args):
        r = _ShimMethod.__call__(self, *args)
        if enforceBuiltin(r):
            # if the return type appears to be correct, check the types
            # some items get cast to look like built-ins for str()
            # an extremely common example is sql result rows.
            raise AssertionError('XML cannot marshall return value: %s '
                                 'for method %s' % (str(result), self._name))
        return r
