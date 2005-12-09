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
    companyName             = (CfgString, 'rPath Inc.',
        "Name of your organization's rBuilder website (Used in the registration and user settings pages)")
        
    productName             = (CfgString, 'rBuilder at rpath.org',
        "Name by which you refer to the rBuilder service (Used heavily throughout rBuilder)")
        
    defaultRedirect         = (CfgString, 'http://rpath.com',
        "The site to which users are redirected when visiting an invalid site "\
        "(Used when a user tries to visit a project page that does not exist, or a "\
        "repository he does not have permissions to view)")
        
    corpSite                = (CfgString, 'http://www.rpath.com/corp/',
        "A link to your corporate web site.")
        
    defaultBranch           = (CfgString, 'rpl:devel',
        "<p>The Conary branch that all rBuilder projects will use by default:</p>"\
        "<p>(Used as the default branch label when projects are created and in Conary "\
        "configuration help text)</p>")

    supportContactHTML      = 'Contact information in HTML.'
    supportContactTXT       = 'Contact information in text.'
    staticPath              = '/conary-static/'
    authRepoMap             = CfgDict(CfgString)
    authUser                = None
    authPass                = None
    authDbPath              = '/srv/authrepo/repos/sqldb'
    templatePath            = os.path.join(templatePath, 'web', 'templates')
    reposPath               = '/srv/mint/repos/'
    reposContentsPath       = None
    dbPath                  = '/srv/mint/data/db'
    dbDriver                = 'sqlite'
    imagesPath              = '/srv/mint/images/'
    logPath                 = '/srv/mint/logs/'
    siteDomainName          = (CfgString, 'rpath.com',
        "Domain of the rBuilder site. Eg., <tt>example.com</tt>")
    projectDomainName       = None
    externalDomainName      = None
    secureHost              = None
    hostName                = (CfgString, None,
        "Hostname to access the rBuilder site. Eg., <tt>rbuilder</tt>. "\
        "The complete URL to access rBuilder is built up of "\
        "host name and site domain name. Eg., <tt>rbuilder.example.com</tt>")
    
    SSL                     = (CfgBool, False, "SSL required for login and write access to rBuilder projects.")
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

        self.setValue('authRepoUrl', self.authRepoMap.items()[0][1])
        
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
