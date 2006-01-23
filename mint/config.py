#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
import os
import sys

import mint

from conary import conarycfg
from conary.conarycfg import ConfigFile

from conary.lib import cfgtypes
import releasetypes

from urlparse import urlsplit

templatePath = os.path.dirname(sys.modules['mint'].__file__)


class CfgImageEnum(cfgtypes.CfgEnum):
    validValues = releasetypes.validImageTypes


class MintConfig(ConfigFile):
    companyName             = (cfgtypes.CfgString, 'rPath, Inc.',
        "Name of your organization's rBuilder website: (Used in the registration and user settings pages)")

    productName             = (cfgtypes.CfgString, 'rBuilder at rpath.org',
        "Name by which you refer to the rBuilder service: (Used heavily throughout rBuilder)")

    corpSite                = (cfgtypes.CfgString, 'http://www.rpath.com/corp/',
        "A link to your corporate web site:")

    defaultBranch           = (cfgtypes.CfgString, 'rpl:devel',
        "<p>The Conary branch that all rBuilder projects will use by default:</p>"\
        "<p>(Used as the default branch label when projects are created and in Conary "\
        "configuration help text)</p>")

    supportContactHTML      = 'Contact information in HTML.'
    supportContactTXT       = 'Contact information in text.'
    staticPath              = '/conary-static/'
    authRepoMap             = cfgtypes.CfgDict(cfgtypes.CfgString)
    authUser                = None
    authPass                = None
    authDbPath              = None
    templatePath            = os.path.join(templatePath, 'web', 'templates')
    dataPath                = '/srv/mint/'
    reposPath               = None
    reposContentsPath       = (cfgtypes.CfgString, None)
    dbPath                  = None
    dbDriver                = 'sqlite'
    imagesPath              = None
    siteDomainName          = (cfgtypes.CfgString, 'rpath.com',
        "Domain of the rBuilder site. Eg., <tt>example.com</tt>")
    projectDomainName       = None
    externalDomainName      = None
    secureHost              = None
    hostName                = (cfgtypes.CfgString, None,
        "Hostname to access the rBuilder site. Eg., <tt>rbuilder</tt>. "\
        "The complete URL to access rBuilder is built up of "\
        "host name and site domain name. Eg., <tt>rbuilder.example.com</tt>")

    SSL                     = (cfgtypes.CfgBool, False, "SSL required for login and write access to rBuilder projects.")
    adminMail               = 'mint@rpath.org'
    newsRssFeed             = ''
    commitAction            = None
    commitEmail             = None
    EnableMailLists         = (cfgtypes.CfgBool, False)
    MailListBaseURL         = 'http://lists.rpath.org/mailman/'
    MailListPass            = 'adminpass'
    basePath                = '/'
    cookieSecretKey         = None
    bugsEmail               = None
    bugsEmailName           = 'rBuilder Bugs'
    bugsEmailSubject        = 'Mint Unhandled Exception Report'
    smallBugsEmail          = None
    debugMode               = (cfgtypes.CfgBool, False)
    sendNotificationEmails  = (cfgtypes.CfgBool, True)
    profiling               = (cfgtypes.CfgBool, False)
    configured              = (cfgtypes.CfgBool, True)
    hideFledgling           = (cfgtypes.CfgBool, False)

    reposDBDriver           = 'sqlite'
    reposDBPath             = '/srv/mint/repos/%s/sqldb'
    visibleImageTypes       = (cfgtypes.CfgList(CfgImageEnum))

    def read(self, path, exception = False):
        ConfigFile.read(self, path, exception)

        self.postCfg()

    def postCfg(self):
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

        if not self.secureHost:
            self.secureHost = self.siteHost

        if not self.reposContentsPath:
            self.reposContentsPath = self.reposPath

        if not self.commitEmail:
            self.commitEmail = "rBuilder@%s" % self.siteDomainName

        if not self.bugsEmail:
            self.bugsEmail = "rBuilder-tracebacks@%s" % self.siteDomainName

        if not self.reposPath: self.reposPath = os.path.join(self.dataPath, 'repos')
        if not self.reposContentsPath: self.reposContentsPath = self.reposPath
        if not self.dbPath: self.dbPath = os.path.join(self.dataPath, 'data/db')
        if not self.imagesPath: self.imagesPath = os.path.join(self.dataPath, 'finished-images')
