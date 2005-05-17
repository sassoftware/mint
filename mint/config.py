#
# Copyright (c) 2005 rpath, Inc.
#
# All rights reserved
#
import os
import sys

import mint
import conary
import conarycfg

from conarycfg import ConfigFile

templatePath = os.path.dirname(sys.modules['mint'].__file__)

class MintConfig(ConfigFile):
    defaults = {
        'staticUrl'         : '/conary-static/',
        'authRepo'          : '',
        'templatePath'      : os.path.join(templatePath, 'web', 'templates'),
        'reposPath'         : '/data/mint/repos/',
        'dbPath'            : '/data/mint/data/db',
    }
