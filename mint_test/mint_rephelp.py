#
# Copyright (c) SAS Institute Inc.
#
import logging
import os
import pwd
import socket
import re
from testutils import mock
# make webunit not so picky about input tags closed
from webunit import SimpleDOM
try:
    SimpleDOM.EMPTY_HTML_TAGS.remove('input')
    SimpleDOM.EMPTY_HTML_TAGS.remove('img')
except ValueError:
    pass

import mint.db.database
import mint.client
from mint.rest.db import reposmgr
from mint import config
from mint import buildtypes
from mint import urltypes
from mint.rest.api import models

from conary import dbstore
from conary import versions
from conary.callbacks import UpdateCallback, ChangesetCallback
from conary.deps import deps
from conary.lib import util
from conary.lib.digestlib import sha1
from conary_test import rephelp
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
