#
# Copyright (c) 2005 rPath, Inc.
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
        'companyName'       : 'rPath Inc.',
        'productName'       : 'rBuilder at rpath.org',
        'defaultRedirect'   : 'http://rpath.com',
        'defaultBranch'     : 'rpl:devel',
        'supportContactHTML': '<a href="mailto:custom@rpath.com">'
                              'custom@rpath.com</a> or join the IRC channel '
                              '<b>#conary</b> on the '
                              '<a href="http://www.freenode.net/">FreeNode</a> '
                              'IRC network',
        'supportContactTXT' : 'custom@rpath.com, or join the IRC channel #conary on the Freenode IRC network (http://www.freenode.net/)',
        'staticPath'        : '/conary-static/',
        'authRepoMap'       : [ STRINGDICT, {} ],
        'authDbPath'        : '/srv/authrepo/repos/sqldb',
        'templatePath'      : os.path.join(templatePath, 'web', 'templates'),
        'reposPath'         : '/srv/mint/repos/',
        'dbPath'            : '/srv/mint/data/db',
        'tmpPath'           : '/srv/mint/tmp/',
        'imagesPath'        : '/srv/mint/images/',
        'logPath'           : '/srv/mint/logs/',
        'domainName'        : 'rpath.org',
        'hostName'          : None, # optional domain name for main site
        'adminMail'         : 'mint@rpath.org',
        'newsRssFeed'       : '',
        'commitAction'      : None,
        'EnableMailLists'   : [ BOOLEAN, False ],
        'MailListBaseURL'   : 'http://lists.rpath.org/mailman/',
        'MailListPass'      : 'adminpass',
        'basePath'          : '/',
        'cookieSecretKey'   : None,
        'bugsEmailFrom'     : 'apache@rpath.com',
        'bugsEmailFromName' : 'Apache',
        'bugsEmailSubject'  : 'Mint Unhandled Exception Report',

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
            self.setValue('MailListBaseURL', self.MailListBaseURL + '/')

        if self.hostName:
            self.siteHost = self.hostName + "." + self.domainName
        else:
            self.siteHost = self.domainName
