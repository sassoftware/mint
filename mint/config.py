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
        'authDbPath'        : '/data/authrepo/sqldb',
        'templatePath'      : os.path.join(templatePath, 'web', 'templates'),
        'reposPath'         : '/data/mint/repos/',
        'dbPath'            : '/data/mint/data/db',
        'tmpPath'           : '/data/mint/tmp/',
        'domainName'        : 'rpath.org',
        'siteHostname'      : 'www',
        'adminMail'         : 'mint@rpath.org',
        'xmlrpcAccess'      : [ BOOLEAN, False ],
        'imagetoolUrl'      : 'http://%s:%s@iso.rpath.org/images/',
        'authUser'          : '',
        'authPass'          : '',
        'newsRssFeed'       : '',
        'commitAction'      : None,
    }
