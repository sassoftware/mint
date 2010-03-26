#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#
import os
import sys

from mint import buildtypes
from mint import urltypes
from mint import mint_error

from conary.conarycfg import ConfigFile, CfgProxy
from conary.dbstore import CfgDriver
from conary.lib.cfgtypes import (CfgBool, CfgDict, CfgEnum, CfgInt,
        CfgList, CfgPath, CfgString)


RBUILDER_DATA = os.getenv('RBUILDER_DATA', '/srv/rbuilder/')
RBUILDER_CONFIG = os.getenv('RBUILDER_CONFIG_PATH', RBUILDER_DATA + 'config/rbuilder.conf')
RBUILDER_GENERATED_CONFIG = RBUILDER_DATA + 'config/rbuilder-generated.conf'
RBUILDER_RMAKE_CONFIG = "/etc/rmake/server.d/25_rbuilder-rapa.conf"

CONARY_CONFIG = os.getenv('CONARY_CONFIG_PATH', '/etc/conaryrc')

# These are keys that are generated for the "generated" configuration file
# Note: this is *only* used for the product, as rBO doesn't get configured
# via "setup".
keysForGeneratedConfig = [ 'configured', 'hostName', 'siteDomainName',
                           'companyName', 'corpSite', 'namespace',
                           'projectDomainName', 'SSL',
                           'secureHost', 'bugsEmail', 'adminMail',
                           'externalPasswordURL', 'authCacheTimeout',
                           'requireSigs', 'authPass', 'dbDriver', 'dbPath',
                           ]

_templatePath = os.path.dirname(sys.modules['mint'].__file__)

__isRBO = None

def getConfig(path=RBUILDER_CONFIG):
    """
    Used as *the* way to get the current rBuilder configuration.

    Raises ConfigurationMissing if not found.
    """
    mintCfg = MintConfig()
    try:
        mintCfg.read(path)
    except:
        raise mint_error.ConfigurationMissing
    else:
        return mintCfg

def isRBO():
    """
    Use this to determine at runtime whether or not this code is running
    on rBuilder Online. We'll check the configuration file first,
    but barring that, we'll assume it's not rBuilder Online.

    FIXME: This will only pull the rBuilderOnline setting from 
    /srv/rbuilder/config/rbuilder.conf; thus, you can not set the
    value of rBuilderOnline for running in the testsuite.
    """
    global __isRBO
    if __isRBO is None:
        try:
            mintCfg = getConfig()
            __isRBO = mintCfg.rBuilderOnline
        except mint_error.ConfigurationMissing:
            __isRBO = False
    return __isRBO

class CfgDownloadEnum(CfgEnum):
    validValues = urltypes.urlTypes

class CfgBuildEnum(CfgEnum):
    validValues = buildtypes.validBuildTypes
    deprecatedValues = buildtypes.deprecatedBuildTypes

    def parseString(self, val):
        if val in self.deprecatedValues:
            preferred = self.origName[self.deprecatedValues[val]]
            print >> sys.stderr, "Warning: %s is deprecated. Please use: %s" %\
                  (val, preferred)
            val = preferred
        return CfgEnum.parseString(self, val)


class MintConfig(ConfigFile):
    configured              = (CfgBool, False)
    dataPath                = (CfgPath, '/srv/rbuilder/')
    rBuilderOnline          = (CfgBool, False)

    # Backend configuration
    adminMail               = (CfgString, 'mint@rpath.org')
    authPass                = (CfgString, None)
    authUser                = (CfgString, None)
    bugsEmail               = (CfgString, None)
    bugsEmailName           = (CfgString, 'rBuilder Bugs')
    bugsEmailSubject        = (CfgString, 'rBuilder Unhandled Exception Report from %(hostname)s')
    commitActionEmail       = (CfgString, None)
    commitAction            = (CfgString, None)
    commitEmail             = (CfgString, None)
    conaryRcFile            = (CfgPath, '/srv/rbuilder/config/conaryrc.generated')
    createConaryRcFile      = (CfgBool, True)
    dbDriver                = (CfgString, 'sqlite')
    dbPath                  = (CfgString, None)
    debugMode               = (CfgBool, False)
    maintenanceLockPath     = (CfgPath, RBUILDER_DATA + '/run/maintenance.lock') 
    profiling               = (CfgBool, False)
    sendNotificationEmails  = (CfgBool, True)
    smallBugsEmail          = (CfgString, None)

    # Handler configuration
    basePath                = (CfgString, '/', "URI root for this rBuilder")
    cookieSecretKey         = (CfgString, None) # Not used in product
    hostName                = (CfgString, None,
        "Hostname to access the rBuilder site. For example, <b><tt>rbuilder</tt></b>. "
        "(The complete URL to access rBuilder is constructed from the "
        "host name and domain name.)")
    imagesPath              = (CfgString, None)
    language                = (CfgString, 'en')
    localeDir               = (CfgPath, '/usr/share/locale/')
    projectDomainName       = (CfgString, None)
    staticPath              = (CfgString, '/conary-static/')
    secureHost              = (CfgString, None)
    SSL                     = (CfgBool, False, "SSL required for login and write access to rBuilder-based products")
    siteDomainName          = (CfgString, 'rpath.com',
        "Domain of the rBuilder site. For example, <b><tt>example.com</tt></b>")
    templatePath            = (CfgPath, _templatePath + '/web/templates')

    # Web features
    diffCacheDir            = (CfgPath, RBUILDER_DATA + '/diffcache/')
    EnableMailLists         = (CfgBool, False)
    MailListBaseURL         = (CfgString, 'http://lists.rpath.org/mailman/')
    MailListPass            = (CfgString, 'adminpass')
    licenseCryptoReports    = (CfgBool, True)
    removeTrovesVisible     = (CfgBool, False)
    hideFledgling           = (CfgBool, False)
    allowTroveRefSearch     = (CfgBool, True)

    # User authentication
    authCacheTimeout        = (CfgInt, None,
                               "Number of seconds to cache authentication results")
    externalPasswordURL     = (CfgString, None,
                               "URL for external password verification, "
                               "required only for situations where you "
                               "wish to use an external URL to handle "
                               "authentication of rBuilder accounts.")

    # User authorization
    adminNewProjects        = (CfgBool, False, "Whether project creation is restricted to site admins")
    adminNewUsers           = (CfgBool, False, "Whether new users should have site admin privileges")

    # Downloads
    redirectUrlType         = (CfgInt, urltypes.AMAZONS3)
    torrentUrlType          = (CfgInt, urltypes.AMAZONS3TORRENT)
    visibleUrlTypes         = CfgList(CfgDownloadEnum)

    # Logging
    logPath                 = (CfgPath, '/var/log/rbuilder')
    xmlrpcLogFile           = (CfgPath, None)
    reposLog                = (CfgBool, True)

    # Repositories and built-in proxy
    database                = (CfgDict(CfgDriver),
            {'default': ('pgpool', 'postgres@localhost.localdomain:6432/%s')},
            "Aliases for repositoryDB connect string templates.")
    injectUserAuth          = (CfgBool, True,
                                "Inject user authentication into proxy requests")
    readOnlyRepositories    = (CfgBool, False)
    reposContentsDir        = (CfgString, '/srv/rbuilder/repos/%s/contents/')
    reposPath               = (CfgPath, None)
    requireSigs             = (CfgBool, None,
                               "Require that all commits to local "
                               "repositories be signed by an OpenPGP key.")
    useInternalConaryProxy  = (CfgBool, False)

    proxyContentsDir        = (CfgPath, RBUILDER_DATA + '/proxy-contents/')
    proxyTmpDir             = (CfgPath, RBUILDER_DATA + '/tmp/')
    proxyChangesetCacheDir  = (CfgPath, RBUILDER_DATA + '/cscache/')

    # Project defaults
    defaultDatabase         = (CfgString, 'default',
            "The default database pool for new projects")
    defaultBranch           = (CfgString, 'rpl:devel',
            "The default namespace and tag used by products you create in rBuilder") # mostly deprecated
    hideNewProjects         = (CfgBool, False)
    namespace               = (CfgString, '',
            "The default namespace used by products you create in rBuilder")
    groupApplianceLabel     = (CfgString, 'rap.rpath.com@rpath:linux-1',
            "The label that contains the group-appliance-platform superclass")

    # Upstream resources
    proxy                   = CfgProxy
    VAMUser                 = (CfgString, '')
    VAMPassword             = (CfgString, '')

    # Branding
    bulletinPath            = (CfgPath, '/srv/rbuilder/config/bulletin.txt')
    frontPageBlock          = (CfgPath, '/srv/rbuilder/config/frontPageBlock.html')
    legaleseLink            = (CfgString, '')
    tosLink                 = (CfgString, '')
    tosPostLoginLink        = (CfgString, '')
    privacyPolicyLink       = (CfgString, '')
    companyName             = (CfgString, 'rPath, Inc.',
        "Name of your organization's rBuilder website: (Used in the registration and user settings pages)")
    productName             = (CfgString, 'rBuilder at rpath.org',
        "Name by which you refer to the rBuilder service: (Used heavily throughout rBuilder)")
    corpSite                = (CfgString, 'http://www.rpath.com/corp/',
        "Your organization's intranet or public web site: (Used for the &quot;About&quot; links)")
    supportContactHTML      = (CfgString, 'Contact information in HTML.')
    supportContactTXT       = (CfgString, 'Contact information in text.')
    newsRssFeed             = (CfgString, '')
    noticesRssFeed          = (CfgList(CfgString), [])
    announceLink            = (CfgString, '')
    googleAnalyticsTracker  = (CfgBool, False)

    # Build system
    anacondaTemplatesFallback   = (CfgString, 'conary.rpath.com@rpl:1')
    packageCreatorConfiguration = (CfgPath, None)
    packageCreatorURL       = (CfgString, None)
    visibleBuildTypes       = (CfgList(CfgBuildEnum))
    excludeBuildTypes       = (CfgList(CfgBuildEnum))
    includeBuildTypes       = (CfgList(CfgBuildEnum))
    queueHost               = (CfgString, '127.0.0.1')
    queuePort               = (CfgInt, 50900)

    # Entitlement and authorization (of the rBuilder)
    availablePlatforms      = (CfgList(CfgString), [])
    # Parallel list to availablePlatforms, we need a name even when we don't
    # have an entitlement
    availablePlatformNames  = (CfgList(CfgString), [])
    availablePlatforms      = (CfgList(CfgString), [])
    configurablePlatforms   = (CfgList(CfgString), [])
    # Parallel lists of platform sources
    platformSourceNames      = (CfgList(CfgString), [])
    platformSourceUrls       = (CfgList(CfgString), [])
    platformSourceLabels     = (CfgList(CfgString), [])
    platformSources          = (CfgList(CfgString), [])
    platformSourceTypes          = (CfgList(CfgString), [])

    acceptablePlatforms     = (CfgList(CfgString), [])
    siteAuthCfgPath         = (CfgPath, RBUILDER_DATA + 'data/authorization.cfg')

    # Guided tours
    ec2GenerateTourPassword = (CfgBool, False,
                                "whether or not to generate a scrambled password for the "
                                "guided tour currently this is set to false (see WEB-354) "
                                "until further notice")


    # *** BEGIN DEPRECATED VALUES ***
    # These values are no longer in active use but must remain here so that
    # old configurations do not raise an error. Some of them may have their
    # values migrated elsewhere; most are simply ignored.

    # Ignored
    authRepoMap             = CfgDict(CfgString)
    awsPublicKey            = None
    awsPrivateKey           = None
    bootableX8664           = (CfgBool, True)
    ec2ProductCode          = (CfgString, None)
    localAddrs              = (CfgList(CfgString), ['127.0.0.1'])
    bannersPerPage          = (CfgInt, 5)
    displaySha1             = (CfgBool, True)
    serializeCommits        = (CfgBool, True)
    projectAdmin            = (CfgBool, True)
    externalDomainName      = (CfgString, None)

    # AMI configuration -- migrated in schema (45, 6)
    ec2PublicKey            = (CfgString, '', "The AWS account id")
    ec2PrivateKey           = (CfgString, '', "The AWS public key")
    ec2AccountId            = (CfgString, '', "The AWS private key")
    ec2S3Bucket             = None
    ec2CertificateFile      = os.path.join(RBUILDER_DATA, 'config', 'ec2.pem')
    ec2CertificateKeyFile   = os.path.join(RBUILDER_DATA, 'config', 'ec2.key')
    ec2LaunchUsers          = (CfgList(CfgString),)
    ec2LaunchGroups         = (CfgList(CfgString),)
    ec2ExposeTryItLink      = (CfgBool, False)
    ec2MaxInstancesPerIP    = 10
    ec2DefaultInstanceTTL   = 600
    ec2DefaultMayExtendTTLBy= 2700
    ec2UseNATAddressing     = (CfgBool, False)

    # Repository databases -- migrated in schema (47, 0)
    reposDBDriver           = CfgString
    reposDBPath             = CfgString

    # *** END DEPRECATED VALUES ***


    def read(self, path, exception = False):
        ConfigFile.read(self, path, exception)

        self.postCfg()

    def __setstate__(self, state):
        # Needed to reset calculated fields after copy or unpickle
        ConfigFile.__setstate__(self, state)
        self.postCfg()

    def postCfg(self):
        #Make sure MailListBaseURL has a slash on the end of it
        if self.MailListBaseURL[-1:] != '/':
            self.setValue('MailListBaseURL', self.MailListBaseURL + '/')

        if not self.projectDomainName:
            self.projectDomainName = self.siteDomainName

        if self.hostName:
            self.siteHost = self.hostName + "." + self.siteDomainName
        else:
            self.siteHost = self.siteDomainName

        if not self.secureHost:
            self.secureHost = self.siteHost

        if not self.reposPath: self.reposPath = os.path.join(self.dataPath, 'repos')
        if not self.dbPath: self.dbPath = os.path.join(self.dataPath, 'data/db')
        if not self.imagesPath: self.imagesPath = os.path.join(self.dataPath, 'finished-images')

    def getInternalProxies(self):
        # use localhost for the proxy due to a bug in proxy handling
        # (RBL-3822)
        if self.siteDomainName.startswith('rpath.local'):
            # FIXME: SICK HACK
            # if we're running under the test suite, we have to use
            # a hostname other than "localhost"
            return {'http' : 'http://%s.%s' %(self.hostName,
                                              self.siteDomainName),
                    'https' : 'https://%s' % (self.secureHost,)}

        return {'http': 'http://localhost',
                'https': 'https://localhost'}

    def writeGeneratedConfig(self, path=RBUILDER_GENERATED_CONFIG, fObj=None):
        """
        Write all the options in keysForGeneratedConfig to
        rbuilder-generated.conf
        """
        if not fObj:
            fObj = open(path, 'w')

        for key in keysForGeneratedConfig:
            self.displayKey(key, out=fObj)

        # Only write the 'default' database alias, anything
        # else came from somewhere else.
        if 'default' in self.database:
            self._options['database'].write(fObj,
                    {'default': self.database['default']}, {})
