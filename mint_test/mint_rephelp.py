#
# Copyright (c) SAS Institute Inc.
#
import logging
import os
import pwd
import socket
import sys
import re
import urlparse
from testutils import sqlharness
from SimpleXMLRPCServer import SimpleXMLRPCServer,SimpleXMLRPCRequestHandler
from testutils import mock
# make webunit not so picky about input tags closed
from webunit import SimpleDOM
try:
    SimpleDOM.EMPTY_HTML_TAGS.remove('input')
    SimpleDOM.EMPTY_HTML_TAGS.remove('img')
except ValueError:
    pass
from webunit import webunittest

from mint.db import builds
from mint.db import jobs
import mint.db.database
from mint.lib import data
import mint.client
from mint.rest.db import reposmgr
from mint import config
from mint import jobstatus
from mint import server
from mint import shimclient
from mint import buildtypes
from mint import urltypes
from mint import mint_error
from mint.rest.api import models

#from mint.distro import jobserver
from mint.flavors import stockFlavors

from conary import dbstore
from conary import versions
from conary.callbacks import UpdateCallback, ChangesetCallback
from conary.deps import deps
from conary.lib import util
from conary.lib.digestlib import sha1
from conary_test import rephelp
from conary_test import resources

from testrunner.testhelp import findPorts
from mint_test import resources
from proddef_test import resources as proddef_resources

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
        from mint.db import schema
        schema.loadSchema(db)
        db.commit()

    def close(self):
        pass

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

    def __init__(self, path, initialized=False):
        MintDatabase.__init__(self, path)
        self.driver = 'sqlite'
        self.initialized = initialized

    def _reset(self):
        if not self.initialized:
            # this is faster than dropping tables, and forces a reopen
            # which avoids sqlite problems with changing the schema
            self.close()
        return self.connect()

    def start(self):
        self.reset()

    def close(self):
        if os.path.exists(self.path):
            os.unlink(self.path)


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


def getIpAddresses():
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

    
def getMintCfg(reposDir, serverRoot, port, securePort, reposDbPort, useProxy):
    cfg = config.MintConfig()

    sslDisabled = bool(os.environ.get("MINT_TEST_NOSSL", ""))

    cfg.namespace = 'yournamespace'
    cfg.siteDomainName = "%s:%i" % (MINT_DOMAIN, port)
    cfg.projectDomainName = "%s:%i" % (MINT_PROJECT_DOMAIN,
            sslDisabled and port or securePort)
    cfg.hostName = MINT_HOST
    cfg.basePath = '/'

    sqldriver = os.environ.get('CONARY_REPOS_DB', 'sqlite')
    if sqldriver == 'sqlite':
        cfg.dbPath = reposDir + '/mintdb'
    elif sqldriver == 'mysql':
        cfg.dbPath = 'root@localhost.localdomain:%d/minttest' % reposDbPort
    elif sqldriver == 'postgresql':
        cfg.dbPath = '%s@localhost.localdomain:%s/%%s' % ( pwd.getpwuid(os.getuid())[0], reposDbPort)
    else:
        raise AssertionError("Invalid database type")

    cfg.dbDriver = sqldriver

    reposdriver = os.environ.get('CONARY_REPOS_DB', 'sqlite')
    if reposdriver == 'sqlite':
        cfg.configLine('database default sqlite ' + reposDir + '/repos/%s/sqldb')
    elif sqldriver == 'postgresql':
        cfg.configLine('database default postgresql '
                '%s@localhost.localdomain:%s/%%s' % (
                    pwd.getpwuid(os.getuid())[0], reposDbPort))
    else:
        assert False
    cfg.reposPath = reposDir + "/repos/"
    cfg.reposContentsDir = " ".join([reposDir + "/contents1/%s/", reposDir + "/contents2/%s/"])

    cfg.dataPath = reposDir
    cfg.storagePath = reposDir + '/jobs'
    cfg.logPath = reposDir + '/logs'
    cfg.imagesPath = reposDir + '/images/'
    cfg.siteAuthCfgPath = reposDir + '/authorization.cfg'
    cfg.authUser = 'mintauth'
    cfg.authPass = 'mintpass'
    cfg.localAddrs = getIpAddresses()
    cfg.availablePlatforms = ['localhost@rpl:plat', ]
    cfg.availablePlatformNames = ['My Spiffy Platform', ]
    if useProxy:
        cfg.useInternalConaryProxy = True
        cfg.proxyContentsDir = reposDir + '/proxy'
        cfg.proxyChangesetCacheDir = reposDir + '/proxycs'
        cfg.proxyTmpDir = reposDir + '/proxytmp'


    cfg.configured = True
    cfg.debugMode = True
    cfg.sendNotificationEmails = False
    cfg.postCfg()

    cfg.hideFledgling = True

    # SSL Testing
    if not sslDisabled:
        dom = MINT_PROJECT_DOMAIN
        port = securePort
    else:
        dom = MINT_DOMAIN
        port = port
    cfg.secureHost = "%s.%s:%i" % (MINT_HOST, dom, port)
    cfg.SSL = (not sslDisabled)

    cfg.visibleBuildTypes = [buildtypes.INSTALLABLE_ISO,
                               buildtypes.RAW_HD_IMAGE,
                               buildtypes.RAW_FS_IMAGE,
                               buildtypes.LIVE_ISO,
                               buildtypes.VMWARE_IMAGE,
                               buildtypes.STUB_IMAGE]
    cfg.visibleUrlTypes   = [ x for x in urltypes.TYPES ]
    cfg.maintenanceLockPath  = os.path.join(cfg.dataPath,
                                            'maintenance.lock')

    util.mkdirChain(os.path.join(cfg.dataPath, 'run'))
    util.mkdirChain(os.path.join(cfg.dataPath, 'cscache'))

    util.mkdirChain(cfg.logPath)

    cfg.reposLog = False

    cfg.bulletinPath = os.path.join(cfg.dataPath, 'bulletin.txt')
    cfg.frontPageBlock = os.path.join(cfg.dataPath, 'frontPageBlock.html')
    return cfg

mintCfg = None
_reposDir = None


def resetCache():
    mint.db.database.dbConnection = None
    reposmgr._cachedCfg = None
    reposmgr._cachedServerCfgs = {}

class RestDBMixIn(object):
    def setUp(self):
        resetCache()
        self.mintDb = None
        self.mintCfg = None

    def setUpProductDefinition(self):
        from rpath_proddef import api1 as proddef
        schemaDir = proddef_resources.get_xsd()
        schemaFile = "rpd-%s.xsd" % proddef.ProductDefinition.version
        if not os.path.exists(os.path.join(schemaDir, schemaFile)):
            # Not running from a checkout
            schemaDir = os.path.join("/usr/share/rpath_proddef")
            assert(os.path.exists(os.path.join(schemaDir, schemaFile)))
        self.mock(proddef.ProductDefinition, 'schemaDir', schemaDir)
        self.mock(proddef.PlatformDefinition, 'schemaDir', schemaDir)
        self.mock(proddef.Platform, 'schemaDir', schemaDir)

    def tearDown(self):
        if self.mintDb:
            self.mintDb.close()
        mock.unmockAll()

    def openRestDatabase(self, createRepos=True, subscribers=None):
        if not self.mintDb:
            self._startDatabase()
        dbPort = getattr(self.mintDb, 'port', None)
        if not self.mintCfg:
            self.mintCfg = getMintCfg(self.workDir, None, 0, 0, dbPort, False)
        from mint.rest.db import database as restdb
        from mint.db import database
        db = database.Database(self.mintCfg)
        if subscribers is None:
            subscribers = []
        db = restdb.Database(self.mintCfg, db, subscribers=subscribers)
        db.auth.isAdmin = True
        # We should probably get a real user ID here, instead of hardcoding 2
        # which is generally the admin's
        db.auth.userId = 2
        if not createRepos:
            db.productMgr.reposMgr = mock.MockObject()
            db.productMgr._setProductVersionDefinition = \
                        db.productMgr.setProductVersionDefinition
            db.productMgr.setProductVersionDefinition = mock.MockObject()
            db.reposMgr = mock.MockObject()
        db.commit()
        self.setDjangoDB()
        self.writeMintConfig()
        return db

    def writeMintConfig(self):
        cfgPath = os.path.join(self.workDir, "rbuilder.conf")
        f = file(cfgPath, "w")
        self.mintCfg.display(f)
        f.close()
        self.mock(config, 'RBUILDER_CONFIG', cfgPath)

    def setDjangoDB(self):
        from django.db import connections, DEFAULT_DB_ALIAS
        conn = connections[DEFAULT_DB_ALIAS]
        sd = conn.settings_dict
        dbPath = self.mintCfg.dbPath
        if sd['NAME'] != dbPath or sd['TEST_NAME'] != dbPath:
            sd['NAME'] = sd['TEST_NAME'] = self.mintCfg.dbPath
            # Force re-open
            conn.close()

    def createUser(self, name, password=None, admin=False):
        db = self.openRestDatabase()
        if password is None:
            password = name
        return db.createUser(name, password, 'Full Name', '%s@foo.com' % name,
                            '%s@foo.com', '', admin=admin)

    def _startDatabase(self):
        mintDb = os.environ.get('CONARY_REPOS_DB', 'sqlite')
        if mintDb == "sqlite" or mintDb == 'postgresql':
            self.mintDb = SqliteMintDatabase(self.workDir + "/mintdb")
        elif mintDb == "mysql":
            raise NotImplementedError
        # loads schema, takes .2s
        # FIXME: eliminate for sqlite by copying in premade sqlite db.
        self.mintDb.start()

    def setDbUser(self, db, username, password=None):
        if password is None:
            password = username
        from mint import users
        if username:
            cu = db.cursor()
            cu.execute('select * from Users where username=?', username)
            row, = cu.fetchall()
            row = dict(row)
            admin = row.pop('is_admin')
            auth = users.Authorization(authorized=True, admin=admin, **row)
        else:
            auth = users.Authorization(authoried=False, admin=False,
                                       userId=-1, username=None)
        db.setAuth(auth, (username, password))

    def createProduct(self, shortname, description=None,
                      owners=None, developers=None, users=None, 
                      private=False, domainname=None, name=None,
                      db=None, prodtype='Appliance'):
        if db is None:
            db = self.openRestDatabase()
        if name is None:
            name = 'Project %s' % shortname

        oldUser = None
        if owners and db.auth.username not in owners:
            oldUser = db.auth.username
            self.setDbUser(db, owners[0])
        try:
            prd = models.Product(name=name, hostname=shortname,
                                 shortname=shortname, prodtype=prodtype,
                                 domainname=domainname, hidden=private,
                                 description=description)
            db.createProduct(prd)
            if owners:
                for username in owners:
                    db.setMemberLevel(shortname, username, 'owner')
            if developers:
                for username in developers:
                    db.setMemberLevel(shortname, username, 'developer')
            if users:
                for username in users:
                    db.setMemberLevel(shortname, username, 'user')
        finally:
            if oldUser:
                self.setDbUser(db, oldUser)
        return prd.productId

    def createRelease(self, db, hostname, buildIds):
        return db.createRelease(hostname, buildIds)

    def createProductVersion(self, db, hostname, versionName, 
                             namespace='rpl', description='',
                             platformLabel=None):
        pv = models.ProductVersion(hostname=hostname, name=versionName,
                                   namespace=namespace, description=description,
                                   platformLabel=platformLabel)
        return db.createProductVersion(hostname, pv)

    def createImage(self, db, hostname, imageType, imageFiles=None,
                 name='Build', description='Build Description',
                 troveName = 'foo',
                 troveVersion = '/localhost@test:1/1:0.1-1-1',
                 troveFlavor = '', outputTrove=None, buildData=None):
        troveVersion = versions.ThawVersion(troveVersion)
        troveFlavor = deps.parseFlavor(troveFlavor)

        img = models.Image(imageType=imageType, name=name, 
                           description=description,
                           troveName=troveName, troveVersion=troveVersion,
                           troveFlavor=troveFlavor,
                           outputTrove=outputTrove)
        imageId = db.imageMgr.createImage(hostname, img, buildData)
        return imageId

    def setImageFiles(self, db, hostname, imageId, imageFiles=None):
        if imageFiles is None:
            digest = sha1()
            digest.update(str(imageId))
            digest = digest.hexdigest()

            imageFiles = models.ImageFileList(files=[models.ImageFile(
                title='Image File %s' % imageId,
                size=1024 * imageId,
                sha1=digest,
                fileName='imagefile_%s.iso' % imageId,
                )])

        for item in imageFiles.files:
            path = '%s/%s/%s/%s' % (self.mintCfg.imagesPath, hostname, imageId,
                    item.fileName)
            util.mkdirChain(os.path.dirname(path))
            open(path, 'w').write('image data')
        db.imageMgr.setFilesForImage(hostname, imageId, imageFiles)


class MintDatabaseHelper(rephelp.RepositoryHelper, RestDBMixIn):
    def setUp(self):
        rephelp.RepositoryHelper.setUp(self)
        RestDBMixIn.setUp(self)

    def tearDown(self):
        self.tearDownLogging()
        RestDBMixIn.tearDown(self)
        rephelp.RepositoryHelper.tearDown(self)

    @classmethod
    def tearDownLogging(cls):
        raiseExceptions = logging.raiseExceptions
        logging.raiseExceptions = 0
        logging.shutdown()
        logging.raiseExceptions = raiseExceptions

    def loadRestFixture(self, name, fn=None):
        import fixtures
        if fn is None:
            from mint_test.resttest import restfixtures
            fixture = restfixtures.fixtures[name](self)
            fn = fixture.load
        name = 'rest_' + name
        cfg, data = fixtures.fixtureCache.load(name, fn)
        self.mintCfg = cfg
        self.mintDb = SqliteMintDatabase(self.mintCfg.dbPath, 
                                         initialized=True)
        self.mintDb.start()
        return data

    openMintDatabase = RestDBMixIn.openRestDatabase

def fixturize(name=None):
    def deco(fn):
        if name is None:
            module = fn.func_globals['__name__']
            fixtureName = '%s.%s' % (module, fn.func_name)
        else:
            fixtureName = name

        def wrapper(self, *args, **kw):
            def loader(mintCfg):
                self.mintCfg = mintCfg
                return mintCfg, fn(self, *args, **kw)
            if self.mintCfg and 'fixture' in self.mintCfg.dataPath:
                return fn(self)
            data = self.loadRestFixture(fixtureName, loader)
            return data

        return wrapper
    return deco
restFixturize = fixturize

def restfixture(name):
    def deco(func):
        def wrapper(self, *args, **kw):
            self.loadRestFixture(name)
            return func(self, *args, **kw)
        wrapper.__name__ = func.__name__
        wrapper.__dict__.update(func.__dict__)
        return wrapper
    return deco

class MintRepositoryHelper(rephelp.RepositoryHelper, RestDBMixIn):

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
        serv = serverCache.getCachedServer(serverIdx)
        SQLserver = sqlharness.start(self.topDir)
        reposDir = self._getReposDir() + '-mint'
        if not serv:
            conaryPath = resources.get_path()
            serv = serverCache.startServer(reposDir, 
                                             conaryPath,
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
            serv.setNeedsReset()
        if serverIdx == 0 and serverCache is self.mintServers:
            self.port = serv.port
            self.mintCfg = serv.mintCfg
            if self.mintCfg.SSL:
                self.securePort = serv.securePort
            else:
                self.securePort = 0
        util.mkdirChain(self.mintCfg.logPath)
        self.db = self.openMintDatabase()
        try:
            cli, userId = self.quickMintAdmin('intuser', 'intpass')
        except mint_error.UserAlreadyExists, e:
            pass
  
        if useProxy:
            self.cfg.configKey('conaryProxy',
                               'http http://localhost:%s' % serv.port)
        try:
            cli = mint.client.MintClient('http://%s:%s@localhost:%s/xmlrpc-private' % ('intuser', 'intpass', serv.port))
        except:
            print "Failure connecting to localhost:%s" % (serv.port, )
            serverCache.stopServer(serverIdx)
            raise
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
        return client, userId

    def quickMintAdmin(self, username, password, email = "test@example.com"):
        client, userId = self.quickMintUser(username, password, email = email)

        adminClient = self.openMintClient(('mintauth', 'mintpass'))
        try:
            adminClient.promoteUserToAdmin(userId)
        except mint_error.UserAlreadyAdmin:
            pass
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
        dataTable = builds.BuildDataTable(db)
        buildId = buildTable.new(projectId=projectId, buildType=imageType,
                name=name, description=description, createdBy=userId,
                troveName=troveName, troveVersion=troveVersion,
                troveFlavor=troveFlavor, status=jobstatus.FINISHED,
                statusMessage="Job Finished")
        if imageFiles is None:
            digest = sha1()
            digest.update(str(buildId))
            digest = digest.hexdigest()

            imageFiles = [('imageFile %s' % buildId, 'Image Title %s' % buildId,
                          1024 * buildId, digest)]
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
        RestDBMixIn.setUp(self)
        if not os.path.exists(self.reposDir):
            util.mkdirChain(self.reposDir)
        self.imagePath = os.path.join(self.tmpDir, "images")
        if not os.path.exists(self.imagePath):
            os.mkdir(self.imagePath)
        self.startMintServer()

        util.mkdirChain(os.path.join(self.reposDir + '-mint', "tmp"))

        self.mintServer = server.MintServer(self.mintCfg)

        self.db = self.mintServer.db

    def tearDown(self):
        mock.unmockAll()
        self.db.close()
        RestDBMixIn.tearDown(self)
        rephelp.RepositoryHelper.tearDown(self)

    def stockBuildFlavor(self, buildId, arch = "x86_64"):
        cu = self.db.cursor()
        flavor = deps.parseFlavor(stockFlavors['1#' + arch]).freeze()
        cu.execute("UPDATE Builds set troveFlavor=? WHERE buildId=?", flavor, buildId)
        self.db.commit()

    def setBuildFinished(self, buildId):
        cu = self.db.cursor()
        cu.execute("UPDATE Builds SET status = ?, statusMessage = ? "
                "WHERE buildId = ?", jobstatus.FINISHED, "Job Finished",
                buildId)
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

    def verifyContentsInFile(self, fileName, contents):
        f = file(fileName)
        assert(contents in f.read())

    def inboundMirror(self, debug = False):
        url = "http://mintauth:mintpass@localhost:%d/xmlrpc-private/" % \
              self.port

        scriptPath = os.path.join(os.path.dirname(os.path.dirname(__file__)),
            'scripts')
        mirrorScript = os.path.join(scriptPath , 'mirror-inbound')
        assert(os.access(mirrorScript, os.X_OK))
        cfg = self.mintServers.getServer(0).serverRoot + '/rbuilder.conf'
        cmd = "%s %s -c %s" % (mirrorScript, url, cfg)
        if debug:
            os.system(cmd + ' --show-mirror-cfg')
        else:
            #self.captureAllOutput( os.system, cmd)
            os.system(cmd)


    def __del__(self):
        try:
            self.stop()
        except:
            pass
        # HACK
        os.system("ipcs  -s  | awk '/^0x00000000/ {print $2}' | xargs -n1 -r ipcrm -s")


class BaseWebHelper(MintRepositoryHelper, webunittest.WebTestCase):
    def getServerData(self):
        # spawn a server if needed, then point our code at it...
        if self.mintServers.servers[0] is None:
            self.startMintServer()
        return FQDN, self.mintServers.servers[0].port

    def getServerHostname(self):
        return FQDN

    def getProjectServerHostname(self):
        return FQDN

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
        testName = getattr(self, '_testMethodName', None) 
        if not testName:
             testName = getattr(self, '_TestCase__testMethodName')
        

        webunittest.HTTPResponse._TestCase__testMethodName = testName
        webunittest.HTTPResponse._testMethodName = testName

    def setUpProductDefinition(self):
        from rpath_proddef import api1 as proddef
        schemaDir = proddef_resources.get_xsd()
        schemaFile = "rpd-%s.xsd" % proddef.ProductDefinition.version
        if not os.path.exists(os.path.join(schemaDir, schemaFile)):
            # Not running from a checkout
            schemaDir = os.path.join("/usr/share/rpath_proddef")
            assert(os.path.exists(os.path.join(schemaDir, schemaFile)))
        self.mock(proddef.ProductDefinition, 'schemaDir', schemaDir)
        self.mock(proddef.PlatformDefinition, 'schemaDir', schemaDir)
        self.mock(proddef.Platform, 'schemaDir', schemaDir)

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
            except self.failureException, err:
                if 'HTTP Response 500:' in str(err):
                    self.showHttpdError()
                raise

        return response

    def webLogin(self, username, password):
        page = self.fetch(self.mintCfg.basePath + 'web/')
        page = page.postForm(1, self.fetchWithRedirect,
                    {'username': username,
                     'password': password})
        self.failUnless('/logout' in page.body)
        return page

    def showHttpdError(self):
        server = self.mintServers.servers[0]
        if not server:
            return
        logPath = os.path.join(server.reposDir, 'httpd/error_log')
        if not os.path.isfile(logPath):
            return
        logFile = open(logPath)
        for line in logFile:
            if 'Traceback (most recent call last):' in line:
                print 'Error from httpd/error_log:'

                # unwind mod_python's awful traceback formatting
                tb = re.compile(r'^\[.*?\] \[error\] \[client .*?\] '
                        r'(.*?)(?:\\n(.*))?$')

                one, two = tb.match(line).groups()
                print one, two
                for line in logFile:
                    match = tb.match(line)
                    if match:
                        one, two = match.groups()
                        print one
                        if two:
                            print two
                    else:
                        print line


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

        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ''

        server = SimpleXMLRPCServer(("127.0.0.1", self.port),
                                    logRequests=False,
                                    requestHandler=RequestHandler)
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

