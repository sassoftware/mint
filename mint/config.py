#
# Copyright (c) 2005 rpath, Inc.
#
# All rights reserved
#
import os
import sys

import mint

import conarycfg
from conarycfg import ConfigFile
from conarycfg import STRINGDICT, BOOLEAN

templatePath = os.path.dirname(sys.modules['mint'].__file__)

class MintConfig(ConfigFile):
    defaults = {
        'staticUrl'         : '/conary-static/',
        'authRepo'          : [ STRINGDICT, {} ],
        'authRepoUrl'       : '',
        'templatePath'      : os.path.join(templatePath, 'web', 'templates'),
        'reposPath'         : '/data/mint/repos/',
        'dbPath'            : '/data/mint/data/db',
        'tmpPath'           : '/data/mint/tmp/',
        'domainName'        : '',
        'adminMail'         : 'mint@rpath.org',
        'xmlrpcEnabled'     : [ BOOLEAN, False ],
    }
