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
from conarycfg import STRINGDICT, STRINGLIST, BOOLEAN

from urlparse import urlsplit

templatePath = os.path.dirname(sys.modules['mint'].__file__)

class MintConfig(ConfigFile):
    defaults = {
        'staticUrl'         : '/conary-static/',
        'authRepoMap'       : [ STRINGDICT, {} ],
        'authDbPath'        : '/srv/authrepo/repos/sqldb',
        'templatePath'      : os.path.join(templatePath, 'web', 'templates'),
        'reposPath'         : '/srv/mint/repos/',
        'dbPath'            : '/srv/mint/data/db',
        'tmpPath'           : '/srv/mint/tmp/',
        'imagesPath'        : '/srv/mint/images/',
        'logPath'           : '/srv/mint/logs/',
        'domainName'        : 'rpath.org',
        'cookieDomain'      : [ STRINGLIST, ['rpath.org'] ],
        'hostName'          : None, # optional domain name for main site
        'adminMail'         : 'mint@rpath.org',
        'xmlrpcAccess'      : [ BOOLEAN, False ],
        'newsRssFeed'       : '',
        'commitAction'      : None,
        'MailListBaseURL'   : 'http://lists.rpath.org/mailman/',
        'MailListPass'      : 'adminpass',


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
        #Make sure MailListBaseURL has a slash on the end of it
        if self.MailListBaseURL[-1:] != '/':
            self.MailListBaseURL += '/'
