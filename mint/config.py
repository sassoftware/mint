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
from conary.lib import cfgtypes

RBUILDER_CONFIG = os.getenv('RBUILDER_CONFIG_PATH', '/srv/rbuilder/config/rbuilder.conf')
RBUILDER_GENERATED_CONFIG = "/srv/rbuilder/config/rbuilder-generated.conf"

# These are keys that are generated for the "generated" configuration file
# Note: this is *only* used for the product, as rBO doesn't get configured
# via "setup".
keysForGeneratedConfig = [ 'configured', 'hostName', 'siteDomainName',
                           'companyName', 'corpSite', 'namespace',
                           'projectDomainName', 'externalDomainName', 'SSL',
                           'secureHost', 'bugsEmail', 'adminMail',
                           'externalPasswordURL', 'authCacheTimeout',
                           'requireSigs', 'authPass', 'reposDBDriver', 
                           'reposDBPath']

templatePath = os.path.dirname(sys.modules['mint'].__file__)

# if this system is an x86_64 box, enable 64-bit bootable images.
# we can override this if we know for a fact that we have external
# 64-bit job servers handling jobs for this server.
x86_64 = os.uname()[4] == 'x86_64'

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

class CfgDownloadEnum(cfgtypes.CfgEnum):
    validValues = urltypes.urlTypes

class CfgBuildEnum(cfgtypes.CfgEnum):
    validValues = buildtypes.validBuildTypes
    deprecatedValues = buildtypes.deprecatedBuildTypes

    def parseString(self, val):
        if val in self.deprecatedValues:
            preferred = self.origName[self.deprecatedValues[val]]
            print >> sys.stderr, "Warning: %s is deprecated. Please use: %s" %\
                  (val, preferred)
            val = preferred
        return cfgtypes.CfgEnum.parseString(self, val)

class MintConfig(ConfigFile):
    # By default, we are not rBuilder Online unless configured to be rBO
    rBuilderOnline          = (cfgtypes.CfgBool, False)

    companyName             = (cfgtypes.CfgString, 'rPath, Inc.',
        "Name of your organization's rBuilder website: (Used in the registration and user settings pages)")

    productName             = (cfgtypes.CfgString, 'rBuilder at rpath.org',
        "Name by which you refer to the rBuilder service: (Used heavily throughout rBuilder)")

    corpSite                = (cfgtypes.CfgString, 'http://www.rpath.com/corp/',
        "Your organization's intranet or public web site: (Used for the &quot;About&quot; links)")

    # deprecated by namespace; we generate the default branch now on a per-product (project) basis
    defaultBranch           = (cfgtypes.CfgString, 'rpl:devel',
       "The default namespace and tag used by products you create in rBuilder")

    namespace               = (cfgtypes.CfgString, 'yournamespace',
        "The default namespace used by products you create in rBuilder")

    groupApplianceLabel     = (cfgtypes.CfgString, 
            'rap.rpath.com@rpath:linux-1',
            "The label that contains the group-appliance-platform superclass")

    supportContactHTML      = 'Contact information in HTML.'
    supportContactTXT       = 'Contact information in text.'
    staticPath              = '/conary-static/'
    authRepoMap             = cfgtypes.CfgDict(cfgtypes.CfgString)
    authUser                = None
    authPass                = None
    templatePath            = os.path.join(templatePath, 'web', 'templates')
    dataPath                = os.path.join(os.path.sep, 'srv', 'rbuilder', '')
    logPath                 = os.path.join(os.path.sep, 'var', 'log', 'rbuilder')
    reposPath               = None
    reposContentsDir        = os.path.join(os.path.sep, 'srv', 'rbuilder', 'repos', '%s', 'contents', '')
    dbPath                  = None
    dbDriver                = 'sqlite'
    imagesPath              = None
    siteDomainName          = (cfgtypes.CfgString, 'rpath.com',
        "Domain of the rBuilder site. For example, <b><tt>example.com</tt></b>")
    projectDomainName       = None
    externalDomainName      = None
    secureHost              = None
    hostName                = (cfgtypes.CfgString, None,
        "Hostname to access the rBuilder site. For example, <b><tt>rbuilder</tt></b>. "\
        "(The complete URL to access rBuilder is constructed from the "\
        "host name and domain name.)")

    SSL                     = (cfgtypes.CfgBool, False, "SSL required for login and write access to rBuilder-based products")
    adminMail               = 'mint@rpath.org'
    newsRssFeed             = ''
    commitAction            = None
    commitActionEmail       = None
    commitEmail             = None
    EnableMailLists         = (cfgtypes.CfgBool, False)
    MailListBaseURL         = 'http://lists.rpath.org/mailman/'
    MailListPass            = 'adminpass'
    basePath                = '/'
    cookieSecretKey         = None
    bugsEmail               = None
    bugsEmailName           = 'rBuilder Bugs'
    bugsEmailSubject        = 'rBuilder Unhandled Exception Report from %(hostname)s'
    smallBugsEmail          = None
    debugMode               = (cfgtypes.CfgBool, False)
    sendNotificationEmails  = (cfgtypes.CfgBool, True)
    profiling               = (cfgtypes.CfgBool, False)
    configured              = (cfgtypes.CfgBool, False)
    hideFledgling           = (cfgtypes.CfgBool, False)

    reposDBDriver           = 'sqlite'
    reposDBPath             = os.path.join(os.path.sep, 'srv', 'rbuilder',
                                           'repos', '%s', 'sqldb')
    visibleBuildTypes       = (cfgtypes.CfgList(CfgBuildEnum))
    excludeBuildTypes       = (cfgtypes.CfgList(CfgBuildEnum))
    includeBuildTypes       = (cfgtypes.CfgList(CfgBuildEnum))
    bootableX8664           = (cfgtypes.CfgBool, x86_64)
    maintenanceLockPath     = os.path.join(dataPath, 'run', 'maintenance.lock')
    announceLink            = ''

    googleAnalyticsTracker  = (cfgtypes.CfgBool, False)
    projectAdmin            = (cfgtypes.CfgBool, True)
    adminNewProjects        = (cfgtypes.CfgBool, False)
    adminNewUsers           = (cfgtypes.CfgBool, False)

    conaryRcFile            = os.path.join(os.path.sep, 'srv', 'rbuilder', 'config',
                                            'conaryrc.generated')
    createConaryRcFile      = (cfgtypes.CfgBool, True)
    reposLog                = (cfgtypes.CfgBool, True)
    xmlrpcLogFile           = ''
    bannersPerPage          = (cfgtypes.CfgInt, 5)
    redirectUrlType         = (cfgtypes.CfgInt, urltypes.AMAZONS3)
    torrentUrlType          = (cfgtypes.CfgInt, urltypes.AMAZONS3TORRENT)
    displaySha1             = (cfgtypes.CfgBool, False)
    visibleUrlTypes         = (cfgtypes.CfgList(CfgDownloadEnum))

    # mimic exactly the conary server cfg items
    externalPasswordURL     = (cfgtypes.CfgString, None,
                               "URL for external password verification, "    \
                               "required only for situations where you "     \
                               "wish to use an external URL to handle "      \
                               "authentication of rBuilder accounts.")
    authCacheTimeout        = (cfgtypes.CfgInt, None,
                               "Number of seconds to cache authentication results")
    removeTrovesVisible     = (cfgtypes.CfgBool, False)
    serializeCommits        = (cfgtypes.CfgBool, True)
    hideNewProjects         = (cfgtypes.CfgBool, False)
    allowTroveRefSearch     = (cfgtypes.CfgBool, True)

    language                = 'en'
    localeDir               = '/usr/share/locale/'

    # AMI configuration data
    ec2PublicKey            = (cfgtypes.CfgString, '', "The AWS account id")
    ec2PrivateKey           = (cfgtypes.CfgString, '', "The AWS public key")
    ec2AccountId            = (cfgtypes.CfgString, '', "The AWS private key")
    ec2S3Bucket             = None
    ec2CertificateFile      = os.path.join(dataPath, 'config', 'ec2.pem')
    ec2CertificateKeyFile   = os.path.join(dataPath, 'config', 'ec2.key')
    ec2LaunchUsers          = (cfgtypes.CfgList(cfgtypes.CfgString),)
    ec2LaunchGroups         = (cfgtypes.CfgList(cfgtypes.CfgString),)

    # Try it now stuff (dark content)
    ec2ExposeTryItLink      = (cfgtypes.CfgBool, False)
    ec2MaxInstancesPerIP    = 10
    ec2DefaultInstanceTTL   = 600
    ec2DefaultMayExtendTTLBy= 2700
    ec2UseNATAddressing     = (cfgtypes.CfgBool, False)

    VAMUser                 = ''
    VAMPassword             = ''

    diffCacheDir            = os.path.join(dataPath, 'diffcache', '')

    licenseCryptoReports    = (cfgtypes.CfgBool, True)

    # By default this is set to OFF. Default configuration file
    # shipped with rBuilder will turn this on for rBuilder Appliances
    useInternalConaryProxy  = (cfgtypes.CfgBool, False)

    # Upstream proxy for all servers to use (i.e. to get beyond
    # the firewall -- not to be confused with the internal Conary
    # caching proxy)
    proxy                   = CfgProxy

    # Miscellany proxy configuration -- shouldn't ever change
    proxyContentsDir        = os.path.join(dataPath, 'proxy-contents', '')
    proxyTmpDir             = os.path.join(dataPath, 'tmp', '')
    proxyChangesetCacheDir  = os.path.join(dataPath, 'cscache', '')
    requireSigs             = (cfgtypes.CfgBool, None,
                               "Require that all commits to local "
                               "repositories be signed by an OpenPGP key.")
    localAddrs              = (cfgtypes.CfgList(cfgtypes.CfgString), ['127.0.0.1'])

    # bulletin file
    bulletinPath            = os.path.join(os.path.sep, 'srv', \
            'rbuilder', 'config', 'bulletin.txt')

    #marketing block file
    frontPageBlock          = os.path.join(os.path.sep, 'srv', \
            'rbuilder', 'config', 'frontPageBlock.html')

    # colo workarounds
    injectUserAuth          = (cfgtypes.CfgBool, True,
                                'Inject user authentication into proxy '
                                'requests')

    # whether or not to generate a scrambled password for the guided tour
    # currently this is set to false (see WEB-354) until further notice
    ec2GenerateTourPassword = (cfgtypes.CfgBool, False)

    # Link to Legal stuff (TOS, Privacy Policy, etc.)
    # Only needed for rBO
    legaleseLink            = (cfgtypes.CfgString, '')
    tosLink                 = (cfgtypes.CfgString, '')
    tosPostLoginLink        = (cfgtypes.CfgString, '')
    privacyPolicyLink       = (cfgtypes.CfgString, '')

    # anaconda-templates fallback label
    anacondaTemplatesFallback = (cfgtypes.CfgString, 'conary.rpath.com@rpl:1')

    # package creator related settings
    packageCreatorURL       = None

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

        if not self.commitEmail:
            self.commitEmail = "rBuilder@%s" % self.siteDomainName

        if not self.bugsEmail:
            self.bugsEmail = "rBuilder-tracebacks@%s" % self.siteDomainName

        if not self.reposPath: self.reposPath = os.path.join(self.dataPath, 'repos')
        if not self.dbPath: self.dbPath = os.path.join(self.dataPath, 'data/db')
        if not self.imagesPath: self.imagesPath = os.path.join(self.dataPath, 'finished-images')
