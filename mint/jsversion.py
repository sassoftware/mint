#
# Copyright (c) 2005-2007 rPath, Inc.
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

def getBasePath(cfg):
    if cfg:
        basePath = os.path.join(cfg.dataPath, 'jobserver')
    else:
        basePath = DEFAULT_BASEPATH
    return basePath

def getVersions(cfg):
    ret = None
    if cfg:
        basePath = getBasePath(cfg)
        if os.path.exists(basePath):
            ret = sorted([x for x in os.listdir(basePath) \
                           if re.match('\d*(\.\d*)+.*', x) \
                           and os.path.isdir(os.path.join(basePath, x))])
    return ret and ret or [constants.mintVersion]

def getDefaultVersion(cfg = None):
    try:
        ret = getVersions(cfg)[-1]
    except IndexError:
        ret = constants.mintVersion
    return ret
