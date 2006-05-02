#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import os
import shutil
import mysqlharness
import rephelp
import sys
import testsuite
import urlparse

from webunit import webunittest

from mint import config
from mint import cooktypes, releasetypes
from mint import dbversion
from mint import server
from mint import shimclient
from mint import releasetypes

from mint.distro import jobserver
from mint.distro.flavors import stockFlavors
from mint.projects import mysqlTransTable

from conary import dbstore
from conary import sqlite3
from conary import versions
from conary.callbacks import UpdateCallback, ChangesetCallback
from conary.deps import deps
from conary.lib import util

# NOTE: make sure that test.rpath.local and test.rpath.local2 is in your
# system's /etc/hosts file (pointing to 127.0.0.1) before running this
# test suite.
MINT_HOST = 'test'
MINT_DOMAIN = 'rpath.local'
if bool(os.environ.get("MINT_TEST_SAMEDOMAINS", "")):
    MINT_PROJECT_DOMAIN = MINT_DOMAIN
else:
    MINT_PROJECT_DOMAIN = 'rpath.local2'

# Stop any redirection loops, if encountered, after 20 redirects.
MAX_REDIRECTS = 20


class EmptyCallback(UpdateCallback, ChangesetCallback):
    def setChangeSet(self, name):
        pass


class MintDatabase:
    def __init__(self, path):
        self.path = path

    def start(self):
        pass

    def reset(self):
        pass


class SqliteMintDatabase(MintDatabase):
    def reset(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def start(self):
        if os.path.exists(self.path):
            os.unlink(self.path)


class MySqlMintDatabase(MintDatabase):
    keepDbs = ['mysql', 'test', 'information_schema', 'testdb']

    def connect(self):
        return dbstore.connect(self.path, "mysql")

    def dropAndCreate(self, dbName, create = True):
        db = self.connect()
        cu = db.cursor()
        cu.execute("SHOW DATABASES")
        if dbName in [x[0] for x in cu.fetchall()]:
            cu.execute("DROP DATABASE %s" % dbName)
        if create:
            cu.execute("CREATE DATABASE %s" % dbName)
        db.close()

    def start(self):
        self.dropAndCreate("minttest")

    def reset(self):
        db = self.connect()
        cu = db.cursor()
        cu.execute("SHOW DATABASES")
        for dbName in [x[0] for x in cu.fetchall() if x[0] not in self.keepDbs]:
            cu.execute("DROP DATABASE %s" % dbName)
        self.dropAndCreate("minttest")
        db.close()

mintCfg = None

class MintApacheServer(rephelp.ApacheServer):
    def __init__(self, name, reposDB, contents, server, serverDir, reposDir,
            conaryPath, repMap, useCache = False, requireSigs = False):
        self.mintPath = os.environ.get("MINT_PATH", "")

        rephelp.ApacheServer.__init__(self, name, reposDB, contents, server, serverDir, reposDir, conaryPath, repMap, useCache, requireSigs)
        self.needsPGPKey = False

        self.sslDisabled = bool(os.environ.get("MINT_TEST_NOSSL", ""))

        # Add dynamic images path to apache settings if necessary
        f = open("%s/httpd.conf" % self.serverRoot)
        if 'finished-images' not in f.read():
            os.rename("%s/httpd.conf" % self.serverRoot,
                      "%s/httpd.conf.in" % self.serverRoot)
            os.system("sed 's|@IMAGESPATH|%s|g'"
                    " < %s/httpd.conf.in > %s/httpd.conf" % \
                      (os.path.join(self.reposDir, "jobserver",
                                    "finished-images"),
                       self.serverRoot, self.serverRoot))
        f.close()

        if not self.sslDisabled:

            # Reserve SSL port
            self.securePort = testsuite.findPorts(num = 1)[0]

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

        f = file(self.serverRoot + "/mint.conf", "w")
        self.mintCfg.display(f)
        f.close()

        mintDb = os.environ.get('CONARY_REPOS_DB', 'sqlite')
        if mintDb == "sqlite":
            self.mintDb = SqliteMintDatabase(self.reposDir + "/mintdb")
        elif mintDb == "mysql":
            self.mintDb = MySqlMintDatabase(reposDB.path)

        
    def start(self):
        rephelp.ApacheServer.start(self)
        self.mintDb.start()

    def reset(self):
        if os.path.exists(self.reposDir + "/repos/"):
            util.rmtree(self.reposDir + "/repos/")
        rephelp.ApacheServer.reset(self)
        self.needsPGPKey = False
        self.mintDb.reset()

    def getTestDir(self):
        return os.environ.get("MINT_PATH", "")  + "/test/"

    def getMap(self):
        return { self.name: 'http://localhost:%d/conary/' %self.port }

    def getMintCfg(self):
        # write Mint configuration
        conaryPath = os.environ.get("CONARY_PATH", "")
        mintPath = os.environ.get("MINT_PATH", "")

        cfg = config.MintConfig()

        cfg.siteDomainName = "%s:%i" % (MINT_DOMAIN, self.port)
        cfg.projectDomainName = "%s:%i" % (MINT_PROJECT_DOMAIN,
                self.sslDisabled and self.port or self.securePort)
        cfg.externalDomainName = "%s:%i" % (MINT_DOMAIN, self.port)
        cfg.hostName = MINT_HOST
        cfg.basePath = '/'

        sqldriver = os.environ.get('CONARY_REPOS_DB', 'sqlite')
        if sqldriver == 'sqlite':
            cfg.dbPath = self.reposDir + '/mintdb'
        elif sqldriver == 'mysql':
            cfg.dbPath = 'root@localhost.localdomain:%d/minttest' % self.reposDB.port
        elif sqldriver == 'postgresql':
            cfg.dbPath = 'root@localhost.localdomain:%d/minttest' % self.reposDB.port
        else:
            raise AssertionError("Invalid database type")
        cfg.dbDriver = sqldriver

        reposdriver = os.environ.get('CONARY_REPOS_DB', 'sqlite')
        if reposdriver == 'sqlite':
            cfg.reposDBPath = self.reposDir + "/repos/%s/sqldb"
        elif reposdriver == 'mysql':
            cfg.reposDBPath = 'root@localhost.localdomain:%d/%%s' % self.reposDB.port
        cfg.reposDBDriver = reposdriver
        cfg.reposPath = self.reposDir + "/repos/"
        cfg.reposContentsDir = [self.reposDir + "/contents1/%s/", self.reposDir + "/contents2/%s/"]

        cfg.dataPath = self.reposDir
        cfg.authDbPath = None
        cfg.imagesPath = self.reposDir + '/images/'
        cfg.authUser = 'mintauth'
        cfg.authPass = 'mintpass'

#        cfg.newsRssFeed = 'file://' +mintPath + '/test/archive/news.xml'
        cfg.configured = True
        cfg.debugMode = True
        cfg.sendNotificationEmails = False
        cfg.commitAction = """%s/scripts/commitaction --username mintauth --password mintpass --repmap '%%(repMap)s' --build-label %%(buildLabel)s --module \'%s/mint/rbuilderaction.py --user %%%%(user)s --url http://mintauth:mintpass@%s:%d/xmlrpc-private/'""" % (conaryPath, mintPath, MINT_HOST + '.' + \
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

        cfg.visibleImageTypes = [releasetypes.INSTALLABLE_ISO,
                                 releasetypes.RAW_HD_IMAGE,
                                 releasetypes.RAW_FS_IMAGE,
                                 releasetypes.LIVE_ISO,
                                 releasetypes.VMWARE_IMAGE,
                                 releasetypes.STUB_IMAGE]
        cfg.maintenanceLockPath  = os.path.join(cfg.dataPath,
                                                'maintenance.lock')

        self.mintCfg = cfg


class MintServerCache(rephelp.ServerCache):
    def getServerClass(self, envname):
        name = "mint." + MINT_DOMAIN
        server = None
        serverDir = os.environ.get('CONARY_PATH') + '/conary/server'
        serverClass = MintApacheServer

        return server, serverClass, serverDir


rephelp._servers = MintServerCache()
rephelp.SERVER_HOSTNAME = "mint." + MINT_DOMAIN + "@rpl:devel"


class MintRepositoryHelper(rephelp.RepositoryHelper):
    def openRepository(self, serverIdx = 0, requireSigs = False, serverName = None):
        ret = rephelp.RepositoryHelper.openRepository(self, serverIdx, requireSigs, serverName)

        if serverIdx == 0:
            self.port = self.servers.getServer(serverIdx).port
            self.mintCfg = self.servers.getServer(serverIdx).mintCfg
            if self.mintCfg.SSL:
                self.securePort = self.servers.getServer(serverIdx).securePort
            else:
                self.securePort = 0

        return ret

    def __init__(self, methodName):
        rephelp.RepositoryHelper.__init__(self, methodName)
        self.imagePath = os.path.join(self.tmpDir, "images")
        os.mkdir(self.imagePath)

        self.sslDisabled = bool(os.environ.get("MINT_TEST_NOSSL", ""))

        if 'context' in self.__class__.__dict__:
            # take string or list of strings--ensure we copy the original
            # otherwise recursive behavior ensues to ill effect.
            context = isinstance(self.context, str) and \
                      [self.context] or self.context[:]

            method = self.__class__.__dict__[self._TestCase__testMethodName]
            if '_contexts' in method.__dict__:
                method._contexts.extend(context)
            else:
                method._contexts = context

    def openMintClient(self, authToken=('mintauth', 'mintpass')):
        """Return a mint client authenticated via authToken, defaults to 'mintauth', 'mintpass'"""
        return shimclient.ShimMintClient(self.mintCfg, authToken)

    def quickMintUser(self, username, password, email = "test@example.com"):
        """Retrieves a client, creates a user as specified by username and
        password, and returns a connection to mint as that new user, and the
        user ID.:"""
        client = self.openMintClient(('mintauth', 'mintpass'))
        userId = client.registerNewUser(username, password, "Test User",
            email, "test at example.com", "", active=True)

        cu = self.db.cursor()
        cu.execute("DELETE FROM Confirmations WHERE userId=?", userId)
        self.db.commit()

        return self.openMintClient((username, password)), userId

    def quickMintAdmin(self, username, password, email = "test@example.com"):
        # manipulate the UserGroups and UserGroup
        cu = self.db.cursor()

        cu.execute("""SELECT COUNT(*) FROM UserGroups
                          WHERE UserGroup = 'MintAdmin'""")
        if cu.fetchone()[0] == 0:
            cu.execute("""SELECT IFNULL(MAX(userGroupId) + 1, 1)
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

        cu.execute("SELECT userId from Users where username=?", username)
        authUserId = cu.fetchone()[0]

        cu.execute("INSERT INTO UserGroupMembers VALUES(?, ?)",
                   groupId, authUserId)
        self.db.commit()

        return client, userId

    def newProject(self, client, name = "Test Project",
                   hostname = "testproject",
                   domainname = MINT_PROJECT_DOMAIN):
        """Create a new mint project and return that project ID."""
        projectId = client.newProject(name, hostname, domainname)
        self.cfg.buildLabel = versions.Label("%s.%s@rpl:devel" % \
                                             (hostname, domainname))
        if self.mintCfg.SSL:
            port = self.securePort
            protocol = 'https'
        else:
            port = self.port
            protocol = 'http'
        self.cfg.repositoryMap = {"%s.%s" % (hostname, domainname):
            "%s://%s.%s:%d%srepos/%s/" % (protocol, MINT_HOST, 
                    MINT_PROJECT_DOMAIN, port, self.mintCfg.basePath, hostname)}

        self.cfg.user.insert(0, ("%s.%s" % (hostname, domainname),
                              client.server._server.authToken[0],
                              client.server._server.authToken[1]))

        # re-open the repos to make changes to repositoryMap have any effect
        self.openRepository()

        return projectId

    def createTestGroupTrove(self, client, projectId,
                             name = 'group-test', upstreamVer = '1.0.0',
                             description = 'No Description'):
        return client.createGroupTrove(projectId, name, upstreamVer,
                                       description, False)

    def setUp(self):
        rephelp.RepositoryHelper.setUp(self)
        self.openRepository()

        self.mintServer = server.MintServer(self.mintCfg, alwaysReload = True)
        self.db = self.mintServer.db

    def tearDown(self):
        self.db.close()
        #self.servers.getServer().stop()
        rephelp.RepositoryHelper.tearDown(self)

    def stockReleaseFlavor(self, releaseId, arch = "x86_64"):
        cu = self.db.cursor()
        flavor = deps.parseFlavor(stockFlavors['1#' + arch]).freeze()
        cu.execute("UPDATE Releases set troveFlavor=? WHERE releaseId=?", flavor, releaseId)
        self.db.commit()

    def hideOutput(self):
        self.oldFd = os.dup(sys.stderr.fileno())
        fd = os.open(os.devnull, os.W_OK)
        os.dup2(fd, sys.stderr.fileno())
        os.close(fd)

    def showOutput(self):
        os.dup2(self.oldFd, sys.stderr.fileno())
        os.close(self.oldFd)

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

    def moveToServer(self, project, serverIdx = 1):
        """Call this to set up a project's Labels table to access a different
           serverIdx instead of 0. Useful for multi-repos tests."""
        self.openRepository(serverIdx)

        defaultLabel = project.getLabelIdMap().keys()[0]
        labelId = project.getLabelIdMap()[defaultLabel]
        label = project.server.getLabel(labelId)

        port = self.mintCfg.SSL and \
                self.servers.getServer(serverIdx).securePort or \
                self.servers.getServer(serverIdx).port

        project.editLabel(labelId, defaultLabel,
            'http://localhost:%d/repos/%s/' % (port, project.hostname),
            label[2], label[3])

    def writeIsoGenCfg(self):
        cfg = jobserver.IsoGenConfig()

        cfg.serverUrl       = "http://mintauth:mintpass@localhost:%d/xmlrpc-private/" % self.port
        cfg.supportedArch   = ['x86']
        cfg.cookTypes       = [cooktypes.GROUP_BUILDER]
        cfg.imageTypes      = [releasetypes.STUB_IMAGE]
        cfg.logPath         = os.path.join(self.reposDir, "jobserver", "logs")
        cfg.imagesPath      = os.path.join(self.reposDir, "jobserver", "images")
        cfg.finishedPath    = os.path.join(self.reposDir, "jobserver", "finished-images")
        cfg.lockFile        = os.path.join(self.reposDir, "jobserver", "jobserver.pid")

        cfg.jobTypes        = {'cookTypes' : cfg.cookTypes,
                               'imageTypes' : cfg.imageTypes}

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


class WebRepositoryHelper(MintRepositoryHelper, webunittest.WebTestCase):
    def __init__(self, methodName):
        webunittest.WebTestCase.__init__(self, methodName)
        MintRepositoryHelper.__init__(self, methodName)

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

    def getServerData(self):
        server = self.getServerHostname()
        # spawn a server if needed, then point our code at it...
        if self.servers.servers[0] is None:
            self.openRepository()
        return server, self.servers.servers[0].port

    def getServerHostname(self):
        return '%s.%s' % (MINT_HOST, MINT_DOMAIN)

    def getProjectServerHostname(self):
        return '%s.%s' % (MINT_HOST, MINT_PROJECT_DOMAIN)

    def getMintUrl(self):
        return 'http://%s:%d/' % (self.getServerData())

    def setUp(self):
        # add our redirect method into HTTPResponse
        webunittest.HTTPResponse.fetchWithRedirect = self.fetchWithRedirect
        webunittest.WebTestCase.setUp(self)
        MintRepositoryHelper.setUp(self)
        self.setAcceptCookies(True)
        self.server, self.port = self.getServerData()
        self.URL = self.getMintUrl()
        # this is tortured, but webunit won't run without it.
        webunittest.HTTPResponse._TestCase__testMethodName = \
                                          self._TestCase__testMethodName

    def tearDown(self):
        self.clearCookies()
        MintRepositoryHelper.tearDown(self)
        webunittest.WebTestCase.tearDown(self)
        # tear down the running server...

    def webLogin(self, username, password):
        page = self.fetch(self.mintCfg.basePath)
        page = page.postForm(1, self.fetchWithRedirect,
                    {'username': username,
                     'password': password})
        self.failUnless('/logout' in page.body)
        return page
