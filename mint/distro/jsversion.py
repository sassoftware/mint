#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#
import os
import re
from mint import mint_error

from conary.conaryclient.cmdline import parseTroveSpec

DEFAULT_BASEPATH = os.path.join(os.path.sep, 'srv', 'mint', 'jobserver')

def _getVersions(basePath = None):
    if basePath is None:
        basePath = DEFAULT_BASEPATH
    return sorted([x for x in os.listdir(basePath) \
                   if re.match('\d*(\.\d*)+.*', x) \
                   and os.path.isdir(os.path.join(basePath, x))])

def getVersions(basePath = None):
    if basePath is None:
        basePath = DEFAULT_BASEPATH
    try:
        f = open(os.path.join(basePath, 'versions'))
    except:
        return _getVersions(basePath)
    try:
        return [parseTroveSpec(x)[1].split('-')[0] for x in f.readlines()]
    finally:
        f.close()

def getDefaultVersion(basePath = None):
    try:
        return getVersions(basePath)[-1]
    except IndexError:
        raise mint_error.JobserverVersionMismatch("No job server versions available.")

