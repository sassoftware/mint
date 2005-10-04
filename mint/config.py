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
        'corpSite'          : 'http://www.rpath.com/corp/',
        'defaultBranch'     : 'rpl:devel',
        'supportContactHTML': 'Contact information in HTML.',
        'supportContactTXT' : 'Contact information in text.',
        'staticPath'        : '/conary-static/',
        'authRepoMap'       : [ STRINGDICT, {} ],
        'authDbPath'        : '/srv/authrepo/repos/sqldb',
        'templatePath'      : os.path.join(templatePath, 'web', 'templates'),
        'reposPath'         : '/srv/mint/repos/',
        'reposContentsPath' : None,
        'dbPath'            : '/srv/mint/data/db',
        'tmpPath'           : '/srv/mint/tmp/',
        'imagesPath'        : '/srv/mint/images/',
        'logPath'           : '/srv/mint/logs/',
        'siteDomainName'    : 'rpath.com',
        'projectDomainName' : 'rpath.org',
        'externalDomainName': 'rpath.com',
        'hostName'          : None, # optional domain name for main site
        'SSL'               : [ BOOLEAN, False ],
        'adminMail'         : 'mint@rpath.org',
        'newsRssFeed'       : '',
        'commitAction'      : None,
        'commitEmail'       : None,
        'commitEmailName'   : 'rBuilder Commit Message',
        'EnableMailLists'   : [ BOOLEAN, False ],
        'MailListBaseURL'   : 'http://lists.rpath.org/mailman/',
        'MailListPass'      : 'adminpass',
        'basePath'          : '',
        'cookieSecretKey'   : None,
        'bugsEmail'     : None,
        'bugsEmailName' : 'rBuilder Bugs',
        'bugsEmailSubject'  : 'Mint Unhandled Exception Report',
        'debugMode'         : [ BOOLEAN, False ],
        'sendNotificationEmails': [ BOOLEAN, True ],

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
            self.siteHost = self.hostName + "." + self.siteDomainName
            self.projectSiteHost = self.hostName + "." + self.projectDomainName
            self.externalSiteHost = self.hostName + "." + self.externalDomainName
        else:
            self.siteHost = self.siteDomainName
            self.projectSiteHost = self.projectDomainName
            self.externalSiteHost = self.externalDomainName

        if not self.reposContentsPath:
            self.reposContentsPath = self.reposPath

        if not self.commitEmail:
            self.commitEmail = "rBuilder@%s" % self.siteDomainName

        if not self.bugsEmail:
            self.bugsEmail = "rBuilder-tracebacks@%s" % self.siteDomainName
