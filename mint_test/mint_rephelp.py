#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#
import os
import sha
import shutil
import pwd
import rephelp
import socket
import sys
import re
import testsuite
import time
import urlparse
from testutils import sqlharness
from SimpleXMLRPCServer import SimpleXMLRPCServer

# make webunit not so picky about input tags closed
from webunit import SimpleDOM
SimpleDOM.EMPTY_HTML_TAGS.remove('input')
SimpleDOM.EMPTY_HTML_TAGS.remove('img')
from webunit import webunittest

from mint.web import hooks
from mint import builds
import mint.client
from mint import config
from mint import cooktypes
from mint import jobs
from mint import server
from mint import shimclient
from mint import buildtypes
from mint import data
from mint import urltypes
from mint import mint_error

#from mint.distro import jobserver
from mint.flavors import stockFlavors

from conary import dbstore
from conary import sqlite3
from conary import versions
from conary.callbacks import UpdateCallback, ChangesetCallback
from conary.deps import deps
from conary.lib import util

from mcp_test import mcp_helper
from mcp import queue
from mcp_test.mcp_helper import MCPTestMixin

from testrunner.testhelp import SkipTestException, findPorts
from testrunner import resources

# Mock out the queues
queue.Queue = mcp_helper.DummyQueue
queue.Topic = mcp_helper.DummyQueue
queue.MultiplexedQueue = mcp_helper.DummyMultiplexedQueue
queue.MultiplexedTopic = mcp_helper.DummyMultiplexedQueue

# NOTE: make sure that test.rpath.local and test.rpath.local2 is in your
# system's /etc/hosts file (pointing to 127.0.0.1) before running this
# test suite.
MINT_HOST = 'test'
MINT_DOMAIN = 'rpath.local'
if bool(os.environ.get("MINT_TEST_SAMEDOMAINS", "")):
    hostname = socket.gethostname()
    MINT_DOMAIN = MINT_PROJECT_DOMAIN = ".".join(hostname.split('.')[1:])
    MINT_HOST = hostname.split('.')[0]
else:
    MINT_PROJECT_DOMAIN = 'rpath.local2'

FQDN = MINT_HOST + '.' + MINT_DOMAIN
PFQDN = MINT_HOST + '.' + MINT_PROJECT_DOMAIN

# Stop any redirection loops, if encountered, after 20 redirects.
MAX_REDIRECTS = 20


class EmptyCallback(UpdateCallback, ChangesetCallback):
    def setChangeSet(self, name):
        pass


class MintDatabase:
    def __init__(self, path):
        self.path = path
        self.driver = None
        self.db = None

    def connect(self):
        db = dbstore.connect(self.path, driver = self.driver)
        assert(db)
        return db

    def createSchema(self, db):
        from mint import schema
        schema.loadSchema(db)
        db.commit()

    def _reset(self):
        # there will often be better ways of implementing this
        db = self.connect()
        cu = db.cursor()
        for table in db.tables.keys():
            cu.execute("DROP TABLE %s" % table)
        return db

    def reset(self):
        db = self._reset()
        self.createSchema(db)
        db.commit()

    def start(self):
        pass


class SqliteMintDatabase(MintDatabase):

    def __init__(self, path):
        MintDatabase.__init__(self, path)
        self.driver = 'sqlite'

    def _reset(self):
        # this is faster than dropping tables, and forces a reopen
        # which avoids sqlite problems with changing the schema
        if os.path.exists(self.path):
            os.unlink(self.path)
        return self.connect()

    def start(self):
        self.reset()


class MySqlMintDatabase(MintDatabase):
    keepDbs = ['mysql', 'test', 'information_schema', 'testdb']

    def __init__(self, path):
        MintDatabase.__init__(self, path)
        self.driver = 'mysql'

    def _reset(self):
        db = self.connect()
        cu = db.transaction()
        try:
            cu.execute("DROP DATABASE minttest")
        except:
            pass
        cu.execute("CREATE DATABASE minttest")
        db.commit()
        db.use("minttest")
        return db

    def start(self):
        self.reset()


mintCfg = None

class MintApacheServer(rephelp.ApacheServer):
    def __init__(self, name, reposDB, contents, server, serverDir, reposDir,
            conaryPath, repMap, useCache = False, requireSigs = False,
            authCheck = None, entCheck = None, useProxy = True, readOnlyRepository = False, serverIdx = 0, **kwargs):
        self.mintPath = os.environ.get("MINT_PATH", "")
        self.useCache = useCache
        self.name = name

        self.sslDisabled = bool(os.environ.get("MINT_TEST_NOSSL", ""))
        self.useProxy = useProxy

        self.securePort = findPorts(num = 1)[0]
        rephelp.ApacheServer.__init__(self, name, reposDB, contents, server,
                                      serverDir, reposDir, conaryPath, repMap,
                                      requireSigs, authCheck = authCheck, entCheck = entCheck, serverIdx = serverIdx)

        self.needsPGPKey = False


        mintDb = os.environ.get('CONARY_REPOS_DB', 'sqlite')
        if mintDb == "sqlite" or mintDb == 'postgresql':
            self.mintDb = SqliteMintDatabase(self.reposDir + "/mintdb")
        elif mintDb == "mysql":
            self.mintDb = MySqlMintDatabase(reposDB.path)


    def createConfig(self):
        rephelp.ApacheServer.createConfig(self)
        # Add dynamic images path to apache settings if necessary
        f = open("%s/httpd.conf" % self.serverRoot)
        if 'finished-images' not in f.read():
            os.rename("%s/httpd.conf" % self.serverRoot,
                      "%s/httpd.conf.in" % self.serverRoot)
            cmd = ("sed -e 's|@IMAGESPATH@|%s|g' -e 's|@MINTPATH@|%s|g'"
                    " -e 's|@MCPPATH@|%s|g'"
                    " -e 's|@PRODDEFPATH@|%s|g'"
                    " -e 's|@CONARYPATH@|%s|g'"
                    " -e 's|@PCREATORPATH@|%s|g'"
                    " -e 's|@CATALOGSERVICEPATH@|%s|g'"
                    " -e 's|@RESTLIBPATH@|%s|g'"
                    " < %s/httpd.conf.in > %s/httpd.conf" % \
                      (os.path.join(self.reposDir, "jobserver",
                                    "finished-images"),
                       os.environ['MINT_PATH'],
                       os.environ['MCP_PATH'], os.environ['PRODUCT_DEFINITION_PATH'],
                       os.environ['CONARY_PATH'], 
                       os.environ['PACKAGE_CREATOR_SERVICE_PATH'],
                       os.environ['CATALOG_SERVICE_PATH'],
                       os.environ['RESTLIB_PATH'],
                       self.serverRoot, self.serverRoot))
            os.system(cmd)
            os.system("sed -i 's|@CONTENTPATH@|%s|g' %s/httpd.conf" % \
                (os.path.join(self.mintPath, "mint", "web", "content"),
                 self.serverRoot))
            scriptPath = os.path.join( \
                    os.path.dirname(os.path.dirname(__file__)), 'scripts')
            os.system("sed -i 's|@SCRIPTSPATH@|%s|g' %s/httpd.conf" % \
                    (scriptPath, self.serverRoot))
        f.close()

        if not self.sslDisabled:

            # Reserve SSL port

            # SSL testing: tack on an include directive in the httpd.conf 
            # file generated by rephelp.ApacheServer.__init__
            f = open("%s/httpd.conf" % self.serverRoot, "a")
            print >> f, 'Include ssl.conf'
            f.close()

            # Make sure the secure port is configured in the SSL confirguration
            os.system("sed 's|@SECURE_PORT@|%s|g'"
                    " < %s/server/ssl.conf.in > %s/ssl.conf"
                    % (str(self.securePort), self.getTestDir(),
                    self.serverRoot))

            # Copy over the certificates
            for ext in ('key', 'crt'):
                shutil.copy("%s/server/test.%s" % (self.getTestDir(), ext),
                        "%s" % self.serverRoot)

        # point every mint server at the same database
        # we don't need completely separate mint instances
        # in the current test suite, but we do need multiple
        # apache servers serving up the same instance.
        global mintCfg
        if not mintCfg:
            self.getMintCfg()
            mintCfg = self.mintCfg
        else:
            self.mintCfg = mintCfg

        f = file(self.serverRoot + "/rbuilder.conf", "w")
        self.mintCfg.display(f)
        f.close()

    def start(self, resetDir=True):
        rephelp.ApacheServer.start(self, resetDir)
        if self.reposDB:
            if self.reposDB.driver == 'postgresql':
                os.system('createlang -U %s -p %s plpgsql template1' % (self.reposDB.user, self.reposDB.port))

        self.mintDb.start()
    
    def reset(self):
        if os.path.exists(self.reposDir + "/repos/"):
            util.rmtree(self.reposDir + "/repos/")
        if os.path.exists(self.reposDir + "/entitlements/"):
            util.rmtree(self.reposDir + "/entitlements/")

        rephelp.ApacheServer.reset(self)
        shutil.rmtree(os.path.join(self.serverRoot, 'cscache'))
        os.mkdir(os.path.join(self.serverRoot, 'cscache'))

        self.needsPGPKey = False
        self.mintDb.reset()

    def getTestDir(self):
        return os.environ.get("MINT_TEST_PATH", "") + '/'

    def getMap(self):
        # by default, there's no repository associated w/ a mint database.
        # we could make this return the entire map for all projects
        # in this rbuilder...but I'm not sure that's worth it.
        return {}

    def getIpAddresses(self):
        # get my local IP addresses
        ifconfig = os.popen('/sbin/ifconfig')
        x = ifconfig.read()
        ifconfig.close()

        ips = []
        addrMatch = re.compile(".*inet addr:([\d\.]+)\s+.*")
        for l in x.split("\n"):
            m = addrMatch.match(l)
            if m:
                ips.append(m.groups()[0])

        return ips

    def getMintCfg(self):
        # write Mint configuration
        conaryPath = os.path.abspath(os.environ.get("CONARY_PATH", ""))
        mintPath = os.path.abspath(os.environ.get("MINT_PATH", ""))

        cfg = config.MintConfig()

        cfg.siteDomainName = "%s:%i" % (MINT_DOMAIN, self.port)
        cfg.projectDomainName = "%s:%i" % (MINT_PROJECT_DOMAIN,
                self.sslDisabled and self.port or self.securePort)
        cfg.externalDomainName = "%s:%i" % (MINT_DOMAIN, self.port)
        cfg.hostName = MINT_HOST
        cfg.basePath = '/'

        sqldriver = os.environ.get('CONARY_REPOS_DB', 'sqlite')
        if sqldriver == 'sqlite' or sqldriver == 'postgresql':
            cfg.dbPath = self.reposDir + '/mintdb'
        elif sqldriver == 'mysql':
            cfg.dbPath = 'root@localhost.localdomain:%d/minttest' % self.reposDB.port
        else:
            raise AssertionError("Invalid database type")

        if sqldriver == 'postgresql':
            cfg.dbDriver = 'sqlite'
        else:
            cfg.dbDriver = sqldriver

        reposdriver = os.environ.get('CONARY_REPOS_DB', 'sqlite')
        if reposdriver == 'sqlite':
            cfg.reposDBPath = self.reposDir + "/repos/%s/sqldb"
        elif reposdriver == 'mysql':
            cfg.reposDBPath = 'root@localhost.localdomain:%d/%%s' % self.reposDB.port
        elif sqldriver == 'postgresql':
            cfg.reposDBPath = '%s@localhost.localdomain:%s/%%s' % ( pwd.getpwuid(os.getuid())[0], self.reposDB.port)
        cfg.reposDBDriver = reposdriver
        cfg.reposPath = self.reposDir + "/repos/"
        cfg.reposContentsDir = " ".join([self.reposDir + "/contents1/%s/", self.reposDir + "/contents2/%s/"])

        cfg.dataPath = self.reposDir
        cfg.logPath = self.reposDir + '/logs'
        cfg.imagesPath = self.reposDir + '/images/'
        cfg.authUser = 'mintauth'
        cfg.authPass = 'mintpass'
        cfg.localAddrs = self.getIpAddresses()
        cfg.availablePlatforms = ['localhost@rpl:plat']
        if self.useProxy:
            cfg.useInternalConaryProxy = True
            cfg.proxyContentsDir = self.reposDir + '/proxy'
            cfg.proxyChangesetCacheDir = self.reposDir + '/proxycs'
            cfg.proxyTmpDir = self.reposDir + '/proxytmp'


#        cfg.newsRssFeed = 'file://' +mintPath + '/test/archive/news.xml'
        cfg.configured = True
        cfg.debugMode = True
        cfg.sendNotificationEmails = False
        cfg.commitAction = """%s/scripts/commitaction --username=mintauth --password=mintpass --repmap='%%(repMap)s' --build-label=%%(buildLabel)s --module=\'%s/mint/rbuilderaction.py --user=%%%%(user)s --url=http://mintauth:mintpass@%s:%d/xmlrpc-private/'""" % (conaryPath, mintPath, MINT_HOST + '.' + \
                MINT_PROJECT_DOMAIN, self.port)
        cfg.postCfg()

        cfg.hideFledgling = True

        # SSL Testing
        if not self.sslDisabled:
            dom = MINT_PROJECT_DOMAIN
            port = self.securePort
        else:
            dom = MINT_DOMAIN
            port = self.port
        cfg.secureHost = "%s.%s:%i" % (MINT_HOST, dom, port)
        cfg.SSL = (not self.sslDisabled)

        cfg.visibleBuildTypes = [buildtypes.INSTALLABLE_ISO,
                                   buildtypes.RAW_HD_IMAGE,
                                   buildtypes.RAW_FS_IMAGE,
                                   buildtypes.LIVE_ISO,
                                   buildtypes.VMWARE_IMAGE,
                                   buildtypes.STUB_IMAGE]
        cfg.visibleUrlTypes   = [ x for x in urltypes.TYPES ]
        cfg.displaySha1 = True
        cfg.maintenanceLockPath  = os.path.join(cfg.dataPath,
                                                'maintenance.lock')

        cfg.conaryRcFile = os.path.join(cfg.dataPath, 'run', 'conaryrc')
        util.mkdirChain(os.path.join(cfg.dataPath, 'run'))
        util.mkdirChain(os.path.join(cfg.dataPath, 'cscache'))

        util.mkdirChain(cfg.logPath)

        cfg.reposLog = False

        cfg.bulletinPath = os.path.join(cfg.dataPath, 'bulletin.txt')
        cfg.frontPageBlock = os.path.join(cfg.dataPath, 'frontPageBlock.html')

        f = open(cfg.conaryRcFile, 'w')
        f.close()
        self.mintCfg = cfg

    def getMintServerDir(self):
        return os.path.join(os.path.dirname(sys.modules['mint_rephelp'].__file__), 'server')

    def getHttpdConfTemplate(self):
        return os.path.join(self.getMintServerDir(), 'httpd.conf.in')


class MintServerCache(rephelp.ServerCache):
    serverType = 'mint'

    def getServerClass(self, envname, useSSL):
        name = "mint." + MINT_DOMAIN
        server = None
        serverDir = os.environ.get('CONARY_PATH') + '/conary/server'
        serverClass = MintApacheServer

        return server, serverClass, serverDir, None, None


_servers = MintServerCache()
rephelp.SERVER_HOSTNAME = "mint." + MINT_DOMAIN + "@rpl:devel"

rephelpCleanup = rephelp._cleanUp
def _cleanUp():
    _servers.stopAllServers(clean=not resources.cfg.isIndividual)
    rephelpCleanup()

rephelp._cleanUp = _cleanUp

_reposDir = None

class MintRepositoryHelper(rephelp.RepositoryHelper, MCPTestMixin):

    # Repository tests tend to be slow, so tag them with this context
    contexts = ('slow',)

    def _getReposDir(self):
        global _reposDir
        _reposDir = rephelp.getReposDir(_reposDir, 'rbuildertest')
        return _reposDir

    def openMintDatabase(self):
        return dbstore.connect(self.mintCfg.dbPath,
                               driver=self.mintCfg.dbDriver)

    def startMintServer(self, serverIdx = 0, useProxy=False):
        serverCache = self.mintServers
        server = serverCache.getCachedServer(serverIdx)
        SQLserver = sqlharness.start(self.topDir)
        reposDir = self._getReposDir() + '-mint'
        if not server:
            server = serverCache.startServer(reposDir, self.conaryDir,
                                          SQLserver,
                                          serverIdx, requireSigs=False, 
                                          serverName=None,
                                          readOnlyRepository=False,
                                          useSSL = False,
                                          sslCert = None,
                                          sslKey = None,
                                          authTimeout = None,
                                          forceSSL = False,
                                          closed = False,
                                          commitAction = None,
                                          deadlockRetry = None)


        else:
            server.setNeedsReset()
        if serverIdx == 0 and serverCache is self.mintServers:
            self.port = server.port
            self.mintCfg = server.mintCfg
            if self.mintCfg.SSL:
                self.securePort = server.securePort
            else:
                self.securePort = 0
        self.db = self.openMintDatabase()
        try:
            cli, userId = self.quickMintAdmin('intuser', 'intpass')
        except mint_error.UserAlreadyExists, e:
            pass
  
        if useProxy:
            self.cfg.configKey('conaryProxy',
                               'http http://localhost:%s' % server.port)
        cli = mint.client.MintClient('http://%s:%s@localhost:%s/xmlrpc-private' % ('intuser', 'intpass', server.port))
        auth = cli.checkAuth()
        assert(auth.authorized)
        return cli

    def openConaryRepository(self, *args, **kw):
        return self.openRepository(*args, **kw)

    def reset(self):
        self.mintServers.resetAllServersIfNeeded()
        return rephelp.RepositoryHelper.reset(self)

    def __init__(self, methodName):
        rephelp.RepositoryHelper.__init__(self, methodName)

        self.sslDisabled = bool(os.environ.get("MINT_TEST_NOSSL", ""))

    def openMintClient(self, authToken=('mintauth', 'mintpass')):
        """Return a mint client authenticated via authToken, defaults to 'mintauth', 'mintpass'"""
        client = shimclient.ShimMintClient(self.mintCfg, authToken)
        client.server._server.mcpClient = self.mcpClient
        return client

    def quickMintUser(self, username, password, email = "test@example.com"):
        """Retrieves a client, creates a user as specified by username and
        password, and returns a connection to mint as that new user, and the
        user ID.:"""
        client = self.openMintClient(('mintauth', 'mintpass'))
        try:
            userId = client.registerNewUser(username, password, "Test User",
                email, "test at example.com", "", active=True)
        except mint_error.UserAlreadyExists:
            userId = client.getUserIdByName(username)
        else:
            cu = self.db.cursor()
            cu.execute("DELETE FROM Confirmations WHERE userId=?", userId)
            self.db.commit()

        client = self.openMintClient((username, password))
        client.server._server.mcpClient = self.mcpClient
        return client, userId

    def quickMintAdmin(self, username, password, email = "test@example.com"):
        # manipulate the UserGroups and UserGroup
        cu = self.db.cursor()

        cu.execute("""SELECT COUNT(*) FROM UserGroups
                          WHERE UserGroup = 'MintAdmin'""")
        if cu.fetchone()[0] == 0:
            cu.execute("""SELECT COALESCE(MAX(userGroupId) + 1, 1)
                             FROM UserGroups""")
            groupId = cu.fetchone()[0]
            cu.execute("INSERT INTO UserGroups VALUES(?, 'MintAdmin')",
                       groupId)
            self.db.commit()
        else:
            cu.execute("""SELECT userGroupId FROM UserGroups
                              WHERE UserGroup = 'MintAdmin'""")
            groupId = cu.fetchone()[0]
        client, userId = self.quickMintUser(username, password, email = email)
        client.server._server.mcpClient = self.mcpClient

        cu.execute("SELECT userId from Users where username=?", username)
        authUserId = cu.fetchone()[0]

        cu.execute("INSERT INTO UserGroupMembers VALUES(?, ?)",
                   groupId, authUserId)
        self.db.commit()

        return client, userId

    def setupProject(self, client, hostname, domainname):
        self.cfg.buildLabel = versions.Label("%s.%s@rpl:devel" % \
                                             (hostname, domainname))
        if self.mintCfg.SSL:
            port = self.securePort
            protocol = 'https'
        else:
            port = self.port
            protocol = 'http'
        self.cfg.repositoryMap.update({"%s.%s" % (hostname, domainname):
            "%s://%s.%s:%d%srepos/%s/" % (protocol, MINT_HOST, 
                    MINT_PROJECT_DOMAIN, port, self.mintCfg.basePath, hostname)})

        self.cfg.user.insert(0, ("%s.%s" % (hostname, domainname),
                              (client.server._authToken[0],
                               client.server._authToken[1])))

    def newProject(self, client, name = "Test Project",
                   hostname = "testproject",
                   domainname = MINT_PROJECT_DOMAIN):
        """Create a new mint project and return that project ID."""
        projectId = client.newProject(name, hostname, domainname,
                        shortname=hostname, version="1.0", prodtype="Component")
        self.setupProject(client, hostname, domainname)

        return projectId

    def addBuild(self, client, projectId, imageType, userId, imageFiles=None,
                 name='Build', description='Build Description',
                 buildData=None, troveName = 'foo',
                 troveVersion = '/localhost@test:1/12345.67:0.1-1-1',
                 troveFlavor = None):
        db = self.openMintDatabase()
        buildTable = builds.BuildsTable(db)
        buildFilesTable = jobs.BuildFilesTable(db)
        dataTable = data.BuildDataTable(db)
        buildId = buildTable.new(projectId=projectId, 
                                 buildType=imageType, name=name,
                                 description=description, createdBy=userId,
                                 troveName=troveName,
                                 troveVersion=troveVersion,
                                 troveFlavor=troveFlavor)
        if imageFiles is None:
            sha1 = sha.new()
            sha1.update(str(buildId))
            sha1 = sha1.hexdigest()

            imageFiles = [('imageFile %s' % buildId, 'Image Title %s' % buildId,
                          1024 * buildId, sha1)]
        client.server._server._setBuildFilenames(buildId, imageFiles)
        if buildData:
            for key, value in buildData.items():
                if isinstance(value, str):
                    dataType = data.RDT_STRING
                elif isinstance(value, int):
                    dataType = data.RDT_INT
                elif isinstance(value, bool):
                    dataType = data.RDT_BOOL
                else:
                    raise NotImplementedError
                dataTable.setDataValue(buildId, key, value, dataType)


    def createTestGroupTrove(self, client, projectId,
                             name = 'group-test', upstreamVer = '1.0.0',
                             description = 'No Description'):
        return client.createGroupTrove(projectId, name, upstreamVer,
                                       description, False)

    def setUp(self):
        self.mintServers = _servers

        rephelp.RepositoryHelper.setUp(self)
        MCPTestMixin.setUp(self)
        if not os.path.exists(self.reposDir):
            util.mkdirChain(self.reposDir)
        self.imagePath = os.path.join(self.tmpDir, "images")
        if not os.path.exists(self.imagePath):
            os.mkdir(self.imagePath)
        self.startMintServer()

        util.mkdirChain(os.path.join(self.reposDir + '-mint', "tmp"))

        self.mintServer = server.MintServer(self.mintCfg, alwaysReload = True)
        self.mintServer.mcpClient = self.mcpClient

        self.db = self.mintServer.db

        # reset some caches
        hooks.repNameCache = {}
        hooks.domainNameCache = {}

    def tearDown(self):
        self.db.close()
        rephelp.RepositoryHelper.tearDown(self)
        MCPTestMixin.tearDown(self)

    def stockBuildFlavor(self, buildId, arch = "x86_64"):
        cu = self.db.cursor()
        flavor = deps.parseFlavor(stockFlavors['1#' + arch]).freeze()
        cu.execute("UPDATE Builds set troveFlavor=? WHERE buildId=?", flavor, buildId)
        self.db.commit()

    def hideOutput(self):
        self.oldFd = os.dup(sys.stderr.fileno())
        fd = os.open(os.devnull, os.W_OK)
        os.dup2(fd, sys.stderr.fileno())
        os.close(fd)

    def showOutput(self):
        os.dup2(self.oldFd, sys.stderr.fileno())
        os.close(self.oldFd)

    def captureAllOutput(self, func, *args, **kwargs):
        oldErr = os.dup(sys.stderr.fileno())
        oldOut = os.dup(sys.stdout.fileno())
        fd = os.open(os.devnull, os.W_OK)
        os.dup2(fd, sys.stderr.fileno())
        os.dup2(fd, sys.stdout.fileno())
        os.close(fd)
        try:
            return func(*args, **kwargs)
        finally:
            os.dup2(oldErr, sys.stderr.fileno())
            os.dup2(oldOut, sys.stdout.fileno())

    def getMirrorAcl(self, project, username):
        dbCon = project.server._server.projects.reposDB.getRepositoryDB( \
            project.getFQDN())
        db = dbstore.connect(dbCon[1], dbCon[0])

        cu = db.cursor()

        cu.execute("""SELECT canMirror
                          FROM Users
                          LEFT JOIN UserGroupMembers ON Users.userId =
                                  UserGroupMembers.userId
                          LEFT JOIN UserGroups ON UserGroups.userGroupId =
                                  UserGroupMembers.userGroupId
                          WHERE Users.username=?""", username)

        try:
            # nonexistent results trigger value error
            canMirror = max([x[0] for x in cu.fetchall()])
        except ValueError:
            canMirror = None
        db.close()
        return canMirror

    def userExists(self, project, username):
        dbCon = project.server._server.projects.reposDB.getRepositoryDB( \
            project.getFQDN())
        db = dbstore.connect(dbCon[1], dbCon[0])

        cu = db.cursor()

        cu.execute("""SELECT userId
                          FROM Users
                          WHERE userName=?""", username)

        try:
            # nonexistent results trigger value error
            id = cu.fetchall()
            if id:
                exists = True
            else:
                exists = False
        except ValueError:
            exists = False
    
        db.close()

        return exists

    def moveToServer(self, project, serverIdx = 1):
        """Call this to set up a project's Labels table to access a different
           serverIdx instead of 0. Useful for multi-repos tests."""
        self.startMintServer(serverIdx)

        defaultLabel = project.getLabelIdMap().keys()[0]
        labelId = project.getLabelIdMap()[defaultLabel]
        label = project.server.getLabel(labelId)

        port = self.mintCfg.SSL and \
                self.mintServers.getServer(serverIdx).securePort or \
                self.mintServers.getServer(serverIdx).port

        protocol = self.mintCfg.SSL and 'https' or 'http'
        project.editLabel(labelId, defaultLabel,
            '%s://localhost:%d/repos/%s/' % (protocol, port, project.hostname),
            label['authType'], label['username'], label['password'], label['entitlement'])

    def writeIsoGenCfg(self):
        raise SkipTestExeption('this test references deleted code')
        cfg = jobserver.IsoGenConfig()

        cfg.serverUrl       = "http://mintauth:mintpass@localhost:%d/xmlrpc-private/" % self.port
        cfg.supportedArch   = ['x86', 'x86_64']
        cfg.cookTypes       = [cooktypes.GROUP_BUILDER]
        cfg.buildTypes    = [buildtypes.STUB_IMAGE]
        cfg.logPath         = os.path.join(self.reposDir, "jobserver", "logs")
        cfg.imagesPath      = os.path.join(self.reposDir, "jobserver", "images")
        cfg.finishedPath    = os.path.join(self.reposDir, "jobserver", "finished-images")
        cfg.lockFile        = os.path.join(self.reposDir, "jobserver", "jobserver.pid")

        cfg.jobTypes        = {'cookTypes' : cfg.cookTypes,
                               'buildTypes' : cfg.buildTypes}

        for x in ["logs", "images", "finished-images"]:
            util.mkdirChain(os.path.join(self.reposDir, "jobserver", x))

        f = open(self.tmpDir + "/iso_gen.conf", "w")
        cfg.display(f)
        f.close()

        f = open(self.tmpDir + "/bootable_image.conf", "w")
        f.close()

        f = open(self.tmpDir + "/conaryrc", "w")
        self.cfg.display(f)
        f.close()

        cfg.configPath = self.tmpDir
        return cfg

    def verifyContentsInFile(self, fileName, contents):
        f = file(fileName)
        assert(contents in f.read())

    def __del__(self):
        try:
            self.stop()
        except:
            pass
        # HACK
        os.system("ipcs  -s  | awk '/^0x00000000/ {print $2}' | xargs -n1 -r ipcrm -s")


class BaseWebHelper(MintRepositoryHelper, webunittest.WebTestCase):
    def getServerData(self):
        server = self.getServerHostname()
        # spawn a server if needed, then point our code at it...
        if self.mintServers.servers[0] is None:
            self.startMintServer()
        return server, self.mintServers.servers[0].port

    def getServerHostname(self):
        return '%s.%s' % (MINT_HOST, MINT_DOMAIN)

    def getProjectServerHostname(self):
        return '%s.%s' % (MINT_HOST, MINT_PROJECT_DOMAIN)

    def getProjectHostname(self, projectHostname):
        return '%s.%s' % (projectHostname, MINT_PROJECT_DOMAIN)

    def getMintUrl(self):
        return 'http://%s:%d/' % (self.getServerData())

    def setUp(self):
        MintRepositoryHelper.setUp(self)
        self.setAcceptCookies(True)
        self.server, self.port = self.getServerData()
        self.URL = self.getMintUrl()

    def tearDown(self):
        MintRepositoryHelper.tearDown(self)

    def setOptIns(self, username, newsletter = False, insider = False):
        cu = self.db.cursor()
        cu.execute("SELECT userId FROM Users WHERE username=?", username)
        userId = cu.fetchone()[0]
        for optIn in ('newsletter', 'insider'):
            cu.execute("SELECT value FROM UserData WHERE name=? AND userId=?",
                       optIn, userId)
            if cu.fetchone():
                cu.execute("""UPDATE UserData SET VALUE=?
                                  WHERE userId=? AND name=?""",
                           int(optIn == 'newsletter' \
                               and newsletter or insider),
                          userId, optIn)
            else:
                cu.execute("""INSERT INTO UserData
                                  (userId, name, value, dataType)
                                  VALUES (?, ?, ?, ?)""",
                           userId, optIn,
                           int(optIn == 'newsletter' \
                               and newsletter or insider),
                           data.RDT_BOOL)
        self.db.commit()


class WebRepositoryHelper(BaseWebHelper):

    # apply default context of 'web' to all children of this class
    # (also, since these tend to be slow, add 'slow' as well)
    contexts = ('web', 'slow')

    def __init__(self, methodName):
        webunittest.WebTestCase.__init__(self, methodName)
        MintRepositoryHelper.__init__(self, methodName)

    def setUp(self):
        BaseWebHelper.setUp(self)
        # add our redirect method into HTTPResponse
        webunittest.HTTPResponse.fetchWithRedirect = self.fetchWithRedirect
        webunittest.WebTestCase.setUp(self)
        # this is tortured, but webunit won't run without it.
        webunittest.HTTPResponse._TestCase__testMethodName = \
                                          self._TestCase__testMethodName

    def tearDown(self):
        BaseWebHelper.tearDown(self)
        self.clearCookies()
        webunittest.WebTestCase.tearDown(self)
        webunittest.HTTPResponse.fetchWithRedirect = None
        webunittest.HTTPResponse._TestCase__testMethodName = None

    # XXX: Override broken version of assertContent / assertNotContent
    # which doesn't pass along kwargs. This can be removed if webunittest
    # ever gets fixed. --sgp
    def assertContent(self, url, content, code=None, **kw):
        if code is None: self.expect_codes
        return self.postAssertContent(url, None, content, code, **kw)

    def assertNotContent(self, url, content, code=None, **kw):
        if code is None: self.expect_codes
        return self.postAssertNotContent(url, None, content, code, **kw)

    def fetchWithRedirect(self, url, params = None, code = None, **kwargs):
        if code is None: code = self.expect_codes
        else: code.extend([301, 302]) # must have these for redirection
        redirects = 0

        while True:
            try:
                if not redirects and params:
                    response = self.post(url, params, code, **kwargs)
                else:
                    response = self.get(url, code, **kwargs)
                if response.code not in (301, 302):
                    break
                redirects += 1
                if redirects >= MAX_REDIRECTS:
                    raise self.failureException, "Too many redirects"
                # Figure the location - which may be relative
                newurl = response.headers['Location']
                url = urlparse.urljoin(url, newurl)
            except webunittest.HTTPError, error:
                raise self.failureException, str(error)

        return response

    def webLogin(self, username, password):
        page = self.fetch(self.mintCfg.basePath)
        page = page.postForm(1, self.fetchWithRedirect,
                    {'username': username,
                     'password': password})
        self.failUnless('/logout' in page.body)
        return page


class FakeRequest(object):
    def __init__(self, hostname, methodname, filename):
        class Connection:
            pass

        self.method = methodname
        self.hostname = hostname
        self.headers_in = {'host': hostname}
        self.headers_out = {}
        self.err_headers_out = {}
        self.error_logged = False
        self.content_type = 'text/xhtml'
        self.options = {}
        self.connection = Connection()
        self.connection.local_addr = (0, '127.0.0.1')
        self.subprocess_env = {}
        self.uri = filename
        self.unparsed_uri = 'http://%s/%s' % (FQDN, filename)

        self.cmd = filename.split("/")[-1]
        self.apache_log = lambda x: sys.stdout.write(x + '\n')

    def log_error(self, msg):
        self.error_logged = True

    def get_options(self):
        return self.options

# Gleefully ripped off from Conary's testsuite
# Use to instantiate an XML-RPC server
class StubXMLRPCServerController:
    def __init__(self):
        self.port = findPorts(num = 1)[0]
        self.childPid = os.fork()
        if self.childPid > 0:
            rephelp.tryConnect('127.0.0.1', self.port)
            return

        server = SimpleXMLRPCServer(("127.0.0.1", self.port),
                                    logRequests=False)
        server.register_instance(self.handlerFactory())
        server.serve_forever()

    def handlerFactory(self):
        raise NotImplementedError

    def kill(self):
        if not self.childPid:
            return
        os.kill(self.childPid, 15)
        os.waitpid(self.childPid, 0)
        self.childPid = 0

    def url(self):
        return "http://%s:%d/" % (self.getHost(), self.getPort())

    def getHost(self):
        return "localhost"

    def getPort(self):
        return self.port

    def __del__(self):
        self.kill()

