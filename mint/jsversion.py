#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#
import os
import re

from mint import constants
from mint import mint_error

from conary import versions
from conary.conaryclient.cmdline import parseTroveSpec

DEFAULT_BASEPATH = os.path.join(os.path.sep, 'srv', 'rbuilder', 'jobserver')

def getVersions(basePath = None):
    if basePath is None:
        basePath = DEFAULT_BASEPATH
    if os.path.exists(basePath):
        ret = sorted([x for x in os.listdir(basePath) \
                       if re.match('\d*(\.\d*)+.*', x) \
                       and os.path.isdir(os.path.join(basePath, x))])
    else:
        ret = None
    return ret and ret or [constants.mintVersion]

def getDefaultVersion(basePath = None):
    try:
        return getVersions(basePath)[-1]
    except IndexError:
        raise mint_error.JobserverVersionMismatch("No job server versions available.")
