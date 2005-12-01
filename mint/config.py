#
# Copyright (c) 2005 rPath, Inc.
#
# All rights reserved
#
import os
import sys

import mint

from conary import conarycfg
from conary.conarycfg import ConfigFile
from conary.conarycfg import CfgString, CfgDict, CfgBool

from urlparse import urlsplit

templatePath = os.path.dirname(sys.modules['mint'].__file__)

class MintConfig(ConfigFile):
    companyName             = 'rPath Inc.'
    productName             = 'rBuilder at rpath.org'
    defaultRedirect         = 'http://rpath.com'
    corpSite                = 'http://www.rpath.com/corp/'
    defaultBranch           = 'rpl:devel'
    supportContactHTML      = 'Contact information in HTML.'
    supportContactTXT       = 'Contact information in text.'
    staticPath              = '/conary-static/'
    authRepoMap             = CfgDict(CfgString)
    authDbPath              = '/srv/authrepo/repos/sqldb'
    templatePath            = os.path.join(templatePath, 'web', 'templates')
    reposPath               = '/srv/mint/repos/'
    reposContentsPath       = None
    dbPath                  = '/srv/mint/data/db'
    dbDriver                = 'sqlite'
    imagesPath              = '/srv/mint/images/'
    logPath                 = '/srv/mint/logs/'
    siteDomainName          = 'rpath.com'
    projectDomainName       = None
    externalDomainName      = None
    secureHost              = None
    hostName                = None # optional domain name for main site
    SSL                     = (CfgBool, False)
    adminMail               = 'mint@rpath.org'
    newsRssFeed             = ''
    commitAction            = None
    commitEmail             = None
    EnableMailLists         = (CfgBool, False)
    MailListBaseURL         = 'http://lists.rpath.org/mailman/'
    MailListPass            = 'adminpass'
    basePath                = '/'
    cookieSecretKey         = None
    bugsEmail               = None
    bugsEmailName           = 'rBuilder Bugs'
    bugsEmailSubject        = 'Mint Unhandled Exception Report'
    smallBugsEmail          = None
    debugMode               = (CfgBool, False)
    sendNotificationEmails  = (CfgBool, True)
    profiling               = (CfgBool, False)

    # don't set these yourself; they will be automatically generated 
    # from authRepoMap:
    authUser                = ''
    authPass                = ''
    authRepoUrl             = ''

    def read(self, path, exception = False):
        ConfigFile.read(self, path, exception)

        repoName, repoMap = self.authRepoMap.items()[0]
        urlparts = urlsplit(repoMap)
        auth, hostname = urlparts[1].split("@")
        username, password = auth.split(":")

        self.setValue('authUser', username)
        self.setValue('authPass', password)

        repoUrl = '%s://%s/' % (urlparts[0], hostname)
        repoUrl += "".join(urlparts[2:])
        
        self.setValue('authRepoUrl', repoUrl)
        #Make sure MailListBaseURL has a slash on the end of it
        if self.MailListBaseURL[-1:] != '/':
            self.setValue('MailListBaseURL', self.MailListBaseURL + '/')

        if not self.projectDomainName:
            self.projectDomainName = self.siteDomainName
        if not self.externalDomainName:
            self.externalDomainName = self.siteDomainName

        if self.hostName:
            self.siteHost = self.hostName + "." + self.siteDomainName
            self.projectSiteHost = self.hostName + "." + self.projectDomainName
            self.externalSiteHost = self.hostName + "." + self.externalDomainName
        else:
            self.siteHost = self.siteDomainName
            self.projectSiteHost = self.projectDomainName
            self.externalSiteHost = self.externalDomainName

        if not self.SSL:
            self.secureHost = self.siteHost

        if not self.reposContentsPath:
            self.reposContentsPath = self.reposPath

        if not self.commitEmail:
            self.commitEmail = "rBuilder@%s" % self.siteDomainName

        if not self.bugsEmail:
            self.bugsEmail = "rBuilder-tracebacks@%s" % self.siteDomainName
