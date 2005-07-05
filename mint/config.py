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

from urlparse import urlsplit

templatePath = os.path.dirname(sys.modules['mint'].__file__)

class MintConfig(ConfigFile):
    defaults = {
        'staticUrl'         : '/conary-static/',
        'authRepoMap'       : [ STRINGDICT, {} ],
        'authDbPath'        : '/data/authrepo/sqldb',
        'templatePath'      : os.path.join(templatePath, 'web', 'templates'),
        'reposPath'         : '/data/mint/repos/',
        'dbPath'            : '/data/mint/data/db',
        'tmpPath'           : '/data/mint/tmp/',
        'imagesPath'        : '/data/mint/images/',
        'logPath'           : '/data/mint/logs/',
        'domainName'        : 'rpath.org',
        'adminMail'         : 'mint@rpath.org',
        'xmlrpcAccess'      : [ BOOLEAN, False ],
        'newsRssFeed'       : '',
        'commitAction'      : None,


        # don't set these yourself; they will be automatically generated 
        # from authRepoMap:
        'authUser'          : '',
        'authPass'          : '',
        'authRepoUrl'       : '',
    }

    def read(self, path, exception = False):
        ConfigFile.read(self, path, exception)

        repoName, repoMap = self.authRepoMap.items()[0]
        urlparts = urlsplit(repoMap)
        auth, hostname = urlparts[1].split("@")
        username, password = auth.split(":")

        self.setValue('authUser', username)
        self.setValue('authPass', password)

        repoUrl = '%s://%%s:%%s@%s/' % (urlparts[0], hostname)
        repoUrl += "".join(urlparts[2:])
        
        self.setValue('authRepoUrl', repoUrl)
