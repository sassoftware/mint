#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import os
import sys

from mint import buildtypes
from mint import urltypes
from mint import mint_error

from conary import conarycfg
from conary.dbstore import CfgDriver
from conary.lib.cfgtypes import (CfgBool, CfgDict, CfgEnum, CfgInt,
        CfgList, CfgPath, CfgString, CfgEnvironmentError)


RBUILDER_DATA = os.getenv('RBUILDER_DATA', '/srv/rbuilder/')
RBUILDER_CONFIG = os.getenv('RBUILDER_CONFIG_PATH', RBUILDER_DATA + 'config/rbuilder.conf')
RBUILDER_RMAKE_CONFIG = "/etc/rmake/server.d/25_rbuilder-rapa.conf"

CONARY_CONFIG = os.getenv('CONARY_CONFIG_PATH', '/etc/conaryrc')

_templatePath = os.path.dirname(sys.modules['mint'].__file__)

__isRBO = None

def getConfig(path=RBUILDER_CONFIG):
    """
    Used as *the* way to get the current rBuilder configuration.

    Raises ConfigurationMissing if not found.
    """
    mintCfg = MintConfig()
    try:
        mintCfg.read(path, exception=True)
    except CfgEnvironmentError:
        raise mint_error.ConfigurationMissing()
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


class MintConfig(conarycfg.ConfigFile):
    configured              = (CfgBool, False)
    dataPath                = (CfgPath, '/srv/rbuilder/')

    # Backend configuration
    adminMail               = (CfgString, 'mint@rpath.org')
    authPass                = (CfgString, None)
    authUser                = (CfgString, 'mintauth')
    bugsEmail               = (CfgString, None)
    bugsEmailName           = (CfgString, 'rBuilder Bugs')
    bugsEmailSubject        = (CfgString, 'rBuilder Unhandled Exception Report from %(hostname)s')
    commitActionModule      = CfgList(CfgString)
    commitEmail             = (CfgString, None)
    dbDriver                = (CfgString, 'pgpool')
    dbPath                  = (CfgString, 'postgres@localhost.localdomain:6432/mint')
    debugMode               = (CfgBool, False)
    disableAuthorization    = (CfgBool, False)
    entitlement             = conarycfg.CfgEntitlement
    profiling               = (CfgBool, False)
    sendNotificationEmails  = (CfgBool, True)
    smallBugsEmail          = (CfgString, None)
    memCache                = (CfgString, 'localhost:11211')
    memCacheTimeout         = (CfgInt, 86400)
    authSocket              = (CfgPath, '/tmp/mintauth.sock')
    sentryDSN               = (CfgString, None)

    # Handler configuration
    basePath                = (CfgString, '/', "URI root for this rBuilder")
    hostName                = (CfgString, None,
        "Hostname to access the rBuilder site. For example, <b><tt>rbuilder</tt></b>. "
        "(The complete URL to access rBuilder is constructed from the "
        "host name and domain name.)")
    imagesPath              = (CfgString, None)
    imagesUploadPath        = (CfgString, None)
    language                = (CfgString, 'en')
    localeDir               = (CfgPath, '/usr/share/locale/')
    projectDomainName       = (CfgString, None)
    staticPath              = (CfgString, '/conary-static/')
    secureHost              = (CfgString, None)
    SSL                     = (CfgBool, True, "SSL required for login and write access to rBuilder-based products")
    siteDomainName          = (CfgString, 'rpath.com',
        "Domain of the rBuilder site. For example, <b><tt>example.com</tt></b>")
    templatePath            = (CfgPath, _templatePath + '/web/templates')
    sessionTimeout          = (CfgInt, 3600 * 24 * 7)

    # Web features
    licenseCryptoReports    = (CfgBool, True)
    removeTrovesVisible     = (CfgBool, False)
    hideFledgling           = (CfgBool, False)
    allowTroveRefSearch     = (CfgBool, True)
    moduleHooksDir          = (CfgPath, '/usr/share/rbuilder-ui/modules/hooks/')
    moduleHooksExt          = (CfgString, '*.swf')

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
    adminNewUsers           = (CfgBool, False,
            "Whether user creation is restricted to site admins.")

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

    # Upstream resources
    proxy                   = conarycfg.CfgProxy
    proxyMap                = conarycfg.CfgProxyMap

    # Branding
    bulletinPath            = (CfgPath, '/srv/rbuilder/config/bulletin.txt')
    frontPageBlock          = (CfgPath, '/srv/rbuilder/config/frontPageBlock.html')
    legaleseLink            = (CfgString, '')
    tosLink                 = (CfgString, '')
    tosPostLoginLink        = (CfgString, '')
    privacyPolicyLink       = (CfgString, '')
    productName             = (CfgString, 'SAS App Engine',
        "Name by which you refer to the rBuilder service: (Used heavily throughout rBuilder)")
    supportContactHTML      = (CfgString, "your local system administrator")
    supportContactTXT       = (CfgString, "your local system administrator")
    announceLink            = (CfgString, '')
    googleAnalyticsTracker  = (CfgBool, False)

    # Build system
    anacondaTemplatesFallback   = (CfgString, 'conary.rpath.com@rpl:1')
    queueHost               = (CfgString, '127.0.0.1')
    queuePort               = (CfgInt, 50900)

    # Entitlement and authorization (of the rBuilder)
    availablePlatforms      = (CfgList(CfgString), [])
    # Parallel list to availablePlatforms, we need a name even when we don't
    # have an entitlement
    availablePlatformNames  = (CfgList(CfgString), [])
    availablePlatforms      = (CfgList(CfgString), [])
    configurablePlatforms   = (CfgList(CfgString), [])
    abstractPlatforms       = (CfgList(CfgString), [])

    acceptablePlatforms     = (CfgList(CfgString), [])

    # Guided tours
    ec2GenerateTourPassword = (CfgBool, False,
                                "whether or not to generate a scrambled password for the "
                                "guided tour currently this is set to false (see WEB-354) "
                                "until further notice")
    
    # inventory
    systemEventsNumToProcess = (CfgInt, 100,
                          "The number of asynchronous system events to dispatch at a time")
    systemEventsPollDelay = (CfgInt, 720,
                          "The number of minutes to wait before enabling a system's next polling task")
    deadStateTimeout = (CfgInt, 30,
                        "The number of days after which a non-responsive system is marked as dead")
    mothballedStateTimeout = (CfgInt, 30,
                        "The number of days after which a dead system is marked as mothballed")
    launchWaitTime = (CfgInt, 1200,
                        "The number of seconds to wait for a launched system's network information to become available")
    surveyMaxAge = (CfgInt, 30, "The number of days after which a removable survey is deleted")
    encryptCredentials = (CfgBool, False)

    # inventory - configuration
    inventoryConfigurationEnabled = (CfgBool, True, "Whether or not managed systems can be configured vai the API")

    rwbsLabel = (CfgString, 'pdt.cny.sas.com@sas:rwbs-8')

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
    packageCreatorURL       = (CfgString, None)
    cookieSecretKey         = (CfgString, None)
    VAMUser                 = (CfgString, '')
    VAMPassword             = (CfgString, '')
    newsRssFeed             = (CfgString, '')
    EnableMailLists         = None
    MailListBaseURL         = None
    MailListPass            = None
    conaryRcFile            = None
    createConaryRcFile      = None
    diffCacheDir            = None
    noticesRssFeed          = None
    commitActionEmail       = None
    commitAction            = None
    rBuilderOnline          = (CfgBool, False)
    rBuilderExternal        = (CfgBool, False)
    groupApplianceLabel     = None
    companyName             = None
    corpSite                = None
    visibleBuildTypes       = None
    excludeBuildTypes       = None
    includeBuildTypes       = None
    useInternalConaryProxy  = (CfgBool, True)
    packageCreatorConfiguration = None
    maintenanceLockPath     = None
    siteAuthCfgPath         = None
    platformSourceNames     = None
    platformSourceUrls      = None
    platformSourceLabels    = None
    platformSources         = None
    platformSourceTypes     = None
    metadataDescriptorPath  = None
    imageImportEnabled      = None

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
        conarycfg.ConfigFile.read(self, path, exception)

        self.postCfg()

    def __setstate__(self, state):
        # Needed to reset calculated fields after copy or unpickle
        conarycfg.ConfigFile.__setstate__(self, state)
        self.postCfg()

    def postCfg(self):
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
        if not self.imagesUploadPath: self.imagesUploadPath = os.path.join(self.dataPath, 'tmp')

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

    def getProxyMap(self):
        # Similar to conarycfg.getProxyMap, but only supports the 'proxy'
        # option.
        return conarycfg.getProxyMap(self)

    def getDBParams(self):
        """Return a dictionary of psycopg params needed to connect to mintdb."""
        if self.dbDriver not in ('postgresql', 'pgpool', 'psycopg2'):
            raise RuntimeError("Cannot convert %s database connection to "
                    "libpq format." % (self.dbDriver,))

        name = self.dbPath
        if '/' not in name:
            return dict(database=name)
        user = password = host = port = None

        host, name = name.split('/', 1)
        if '@' not in host:
            return dict(database=name, host=host)

        user, host = host.split('@', 1)
        if ':' in user:
            user, password = user.split(':', 1)

        # Parse bracketed IPv6 addresses
        i = host.rfind(':')
        j = host.rfind(']')
        if i > j:
            host, port = host[:i], int(host[i+1:])
        if host[0] == '[' and host[-1] == ']':
            host = host[1:-1]

        out = dict(database=name, host=host)
        if port:
            out['port'] = port
        if user:
            out['user'] = user
        if password:
            out['password'] = password
        return out

    def getSessionDir(self):
        return os.path.join(self.dataPath, 'sessions')
