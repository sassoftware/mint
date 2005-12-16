#
# Copyright (c) 2004-2005 rPath, Inc.
#

#python
import copy
import errno
import os
import signal
import pwd
import random
import re
import shutil
import socket
import stat
import sys
import tempfile
import time
import unittest
from urlparse import urlparse

#conary
from conary import sqlite3
from conary import branch
from conary.build import cook
from conary.build import loadrecipe, use
from conary import checkin
from conary import clone
from conary import conaryclient
from conary import conarycfg
from conary import cscmd
from conary import cvc
from conary.deps import deps, arch
from conary import files
from conary import flavorcfg
from conary.lib import log
from conary.lib import sha1helper
from conary.lib import util
from conary.local import database
from conary.repository import netclient, changeset, filecontents
from conary import repository
from conary import trove
from conary import updatecmd
from conary import versions

#test
import recipes
import testsuite

#mint
from mint import dbversion
from mint import mint
from mint import users
from mint import config

MINT_DOMAIN = 'rpath.local'
MINT_HOST = 'test'

# this is an override for deps.arch.x86flags -- we never want to use
# any system flags (normally gathered from places like /proc/cpuinfo)
# because they could change the results from run to run
def x86flags(archTag, *args):
    # always pretend we're on i686 for x86 machines
    if archTag == 'x86':
        flags = []
        for f in ('i486', 'i586', 'i686'):
            flags.append((f, deps.FLAG_SENSE_PREFERRED))
        return deps.Dependency(archTag, flags)
    # otherwise, just use the archTag with no flags
    return deps.Dependency(archTag)
# override the existing x86flags() function
arch.x86flags = x86flags
# reinitialize deps.arch
arch.initializeArch()

class IdGen0(cook._IdGen):

    formatStr = "%s"

    def __call__(self, path, version, flavor):
	if self.map.has_key(path):
	    return self.map[path]

	fileid = sha1helper.md5String(self.formatStr % path)
	self.map[(path, flavor)] = (fileid, None, None)
	return (fileid, None, None)

class IdGen1(IdGen0):

    formatStr = "1%s"

class IdGen3(IdGen0):

    formatStr = "111%s"

class RepositoryServer:
    def __init__(self, name):
        self.name = name

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

class ChildRepository(RepositoryServer):
    """
    sets up a repository that will be run as a child process
    """
    def __init__(self, name, server, serverDir, reposDir, conaryPath):
        RepositoryServer.__init__(self, name)
        self.reposDir = reposDir
        self.conaryPath = conaryPath
        self.serverDir = serverDir
        self.server = server
                
        foundport = False
        portstart = 53981
        for port in xrange(portstart, portstart + 100):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(('localhost', port))
                s.close()
            except:
                pass
            else:
                foundport = True
                break

        if not foundport:
            raise socket.error, "Cannot find open port to run server on"

        self.port = port

    def createUser(self):
        # using echo to send the password isn't secure, but the password
        # is foo, so who cares?
        os.system("cd %s; echo mintpass | ./server.py --add-user mintauth %s"
                  % (self.serverDir, self.reposDir))
        os.system("cd %s; echo anonymous | ./server.py --add-user anonymous %s"
                  % (self.serverDir, self.reposDir))

class ApacheServer(ChildRepository):
    def __init__(self, name, server, serverDir, reposDir, conaryPath, mintPath, repMap,
                 useCache = False):
        ChildRepository.__init__(self, name, server, serverDir, reposDir,
                                 conaryPath)
        self.mintPath = mintPath
        self.serverpid = -1

        self.serverRoot = tempfile.mkdtemp()
	os.mkdir(self.serverRoot + "/tmp")
        for path in ('/usr/lib64/httpd/modules', '/usr/lib/httpd/modules'):
            if os.path.isdir(path):
                os.symlink(path, self.serverRoot + "/modules")
                break
	testDir = os.path.realpath(os.path.dirname(
            sys.modules['rephelp'].__file__))
	os.system("sed 's|@NETRPATH@|%s|;s|@CONARYPATH@|%s|;s|@PORT@|%s|;"
		       "s|@DOCROOT@|%s|;s|@MINTPATH@|%s|'"
		    " < %s/server/httpd.conf.in > %s/httpd.conf"
		    % (self.serverDir, conaryPath, str(self.port),
		       self.serverRoot, mintPath, testDir, self.serverRoot))
	f = open("%s/test.cnr" % self.serverRoot, "w")
	print >> f, 'repositoryDir %s' % self.reposDir
	print >> f, 'tmpDir %s/tmp' % self.serverRoot
	print >> f, 'serverName %s' %self.name
        for repname, reppath in repMap.iteritems():
            print >> f, 'repositoryMap %s %s' %(repname, reppath)
        if useCache:
            print >> f, 'cacheChangeSets True'
        else:
            print >> f, 'cacheChangeSets False'

        # write Mint configuration
        cfg = config.MintConfig()

        cfg.siteDomainName = "%s:%i" % (MINT_DOMAIN, self.port)
        cfg.projectDomainName = "%s:%i" % (MINT_DOMAIN, self.port)
        cfg.externalDomainName = "%s:%i" % (MINT_DOMAIN, self.port)
        cfg.hostName = MINT_HOST
        cfg.secureHost = "%s.%s" % (MINT_HOST, MINT_DOMAIN)
        
        sqldriver = os.environ.get('MINT_SQL', 'sqlite')
        if sqldriver == 'sqlite':
            cfg.dbPath = self.serverRoot + '/mintdb'
        elif sqldriver == 'mysql':
            cfg.dbPath = 'testuser:testpass@localhost.localdomain/minttest'
        else:
            assert("Invalid database type")
        cfg.dbDriver = sqldriver
      
        cfg.dataPath = self.reposDir
        cfg.authDbPath = self.reposDir + '/sqldb'
        cfg.imagesPath = self.reposDir + '/images/'
        cfg.authRepoMap = {self.name: 'http://127.0.0.1:%d/conary/' % self.port}
        cfg.authUser = 'mintauth'
        cfg.authPass = 'mintpass'

        cfg.configured = True
        cfg.debugMode = True
        cfg.sendNotificationEmails = False
        cfg.commitAction = """%s/scripts/commitaction --username mintauth --password mintadmin --repmap '%%(repMap)s' --build-label %%(buildLabel)s --module \'%s/mint/rbuilderaction.py --user %%%%(user)s --url http://%s:%d/xmlrpc-private/'""" % (conaryPath, mintPath, 'test.rpath.local', self.port)
        cfg.postCfg()
        self.mintCfg = cfg

    def __del__(self):
	self.stop()
	shutil.rmtree(self.serverRoot)

    def getMap(self):
        return {self.name: 'http://127.0.0.1:%d/conary/' % self.port }

    def reset(self):
        self.stop()
        self.start()

    def start(self):
        shutil.rmtree(self.reposDir)
        os.mkdir(self.reposDir)
        self.createUser()
        if self.serverpid != -1:
            return

        # write mint.conf to disk
        f = open("%s/mint.conf" % self.serverRoot, "w")
        self.mintCfg.display(out = f)
        f.close()

	# HACK
	os.system("ipcs  -s  | awk '/^0x/ {print $2}' | xargs -n1 -r ipcrm -s")

        self.serverpid = os.fork()
        if self.serverpid == 0:
            #print "starting server in %s" % self.serverRoot
	    args = ("/usr/sbin/httpd", 
		    "-X",
		    "-d", self.serverRoot,
		    "-f", "httpd.conf",
		    "-C", 'DocumentRoot "%s"' % self.serverRoot)
	    os.execv(args[0], args)
        else:
            pass

    def stop(self):
        if self.serverpid != -1:
            # HACK
            os.system("ipcs  -s  | awk '/^0x/ {print $2}' | xargs -n1 -r ipcrm -s")

            os.kill(self.serverpid, signal.SIGTERM)
            os.waitpid(self.serverpid, 0)
            self.serverpid = -1

class ServerCache:

    def __init__(self):
        self.servers = [ None ] * 5

    def startServer(self, reposDir, conaryPath, mintPath, serverIdx = 0):
        if self.servers[serverIdx] is not None:
            return self.servers[serverIdx]

        name = '127.0.0.1'
        envname = 'CONARY_SERVER'
        if serverIdx > 0:
            name += str(serverIdx)
            reposDir += '-%d' %serverIdx
            envname += str(serverIdx)

        if not os.path.isdir(reposDir):
            os.mkdir(reposDir)

        useDefault = False
        server = os.environ.get(envname, None)
        kw = {}
        serverDir = os.environ.get('CONARY_PATH') + '/conary/server'
        serverClass = ApacheServer
        self.servers[serverIdx] = serverClass(name, server, serverDir, 
                                              reposDir,
                                              conaryPath,
                                              mintPath,
                                              self.getMap())
        self.servers[serverIdx].start()
        return self.servers[serverIdx]

    def resetAllServers(self):
        for server in self.servers:
            if server is not None:
                server.reset()

    def getServer(self, serverIdx=0):
        return self.servers[serverIdx]

    def getMap(self):
        servers = {}
        for server in self.servers:
            if server:
                servers.update(server.getMap())
        return servers

    def getServerNames(self):
        for server in self.servers:
            if server:
                yield (server.name)

_servers = ServerCache()

class RepositoryHelper(testsuite.TestCase):
    topDir = None
    cleanupDir = True
    defLabel = versions.Label("127.0.0.1@rpl:linux")

    def setUp(self):
        # set up the flavor based on the defaults in use
        self.initializeFlavor()
        self._origFlavor = use.allFlagsToFlavor('')
        self._origDir = os.getcwd()
        testsuite.TestCase.setUp(self)
        self.cfg.buildLabel = self.defLabel
        self.logFilter.clear()

    def tearDown(self):
        self.resetFlavors()
        self.reset()
        os.chdir(self._origDir)
        testsuite.TestCase.tearDown(self)
        self.cfg.excludeTroves = conarycfg.RegularExpressionList()
        self.cfg.pinTroves = conarycfg.RegularExpressionList()
        self.logFilter.clear()

    def getRepositoryClient(self, user = 'mintauth', password = 'mintpass'):
        cfg = copy.copy(self.cfg)
        for name in self.servers.getServerNames():
            cfg.user.addServerGlob(name + "*", user, password)
        cfg.repositoryMap.update(self.servers.getMap())
        client = conaryclient.ConaryClient(cfg)
        return client.getRepos()

    def getPort(self, serverIdx = 0):
        return self.servers.getServer(serverIdx).port

    def openRepository(self, serverIdx=0):
        server = self.servers.startServer(self.reposDir, self.conaryDir,
                                          self.mintDir, serverIdx)
        # make sure map is up to date
        self.cfg.repositoryMap.update(self.servers.getMap())

	count = 0
        repos = self.getRepositoryClient()

        name = "127.0.0.1"
        if serverIdx:
            name += "%d" % serverIdx
        label = versions.Label("%s@rpl:linux" % name)

        ready = False
	while count < 500:
	    try:
                repos.troveNames(label)
                ready = True
                break
	    except:
		pass

	    time.sleep(0.01)
	    count += 1
        if not ready:
            raise RuntimeError, "unable to open networked repository"

        return repos

    def addfile(self, file):
        cvc.sourceCommand(self.cfg, [ "add", file ], {} )

    def checkout(self, name, versionStr = None, dir = None):
	self.openRepository()
	dict = {}
	if dir:
	    dict = { "dir" : dir }

        callback = checkin.CheckinCallback()

	if versionStr:
	    cvc.sourceCommand(self.cfg, [ "checkout", name +'='+ versionStr ], 
                              dict, callback=callback)
	else:
	    cvc.sourceCommand(self.cfg, [ "checkout", name ], dict,
                              callback=callback)

    def commit(self):
	self.openRepository()
        callback = checkin.CheckinCallback()
	cvc.sourceCommand(self.cfg, [ "commit" ], { 'message' : 'foo' },
                          callback=callback)

    def newpkg(self, name):
	self.openRepository()
	cvc.sourceCommand(self.cfg, [ "newpkg", name], {})

    def makeSourceTrove(self, name, recipeFile, branch = 'rpl:devel'):
        buildLabel = self.cfg.buildLabel
        self.cfg.buildLabel = versions.Label(buildLabel.asString().split("@")[0] + "@" + branch)
        try:
            origDir = os.getcwd()
            os.chdir(self.workDir)
            self.newpkg(name)
            os.chdir(name)
            self.writeFile(name + '.recipe', recipeFile)
            self.addfile(name + '.recipe')
            self.commit()
            os.chdir(origDir)
        finally:
            self.cfg.buildLabel = buildLabel

    def resetFlavors(self):
        use.clearFlags()
        use.track(False)

    def resetAllRepositories(self):
        self.servers.resetAllServers()
	self.openRepository()

    def resetRepository(self, serverIdx=0):
        server = self.servers.getServer(serverIdx)
        if server is not None:
            server.reset()
            self.openRepository()

    def resetWork(self):
	util.rmtree(self.workDir)
	os.mkdir(self.workDir)

    def resetRoot(self):
	util.rmtree(self.rootDir)
	os.mkdir(self.rootDir)

    def resetCache(self):
	util.rmtree(self.cacheDir)
	os.mkdir(self.cacheDir)

    def reset(self):
	self.resetRepository()
	self.resetWork()
	self.resetRoot()
	self.resetCache()
        sys.excepthook = util.genExcepthook(True)

    def writeFile(self, file, contents):
	if os.path.exists(file):
	    mtime = os.stat(file).st_mtime
	else:
	    mtime = None

	f = open(file, "w")
	f.write(contents)
	f.close()

	if mtime:
	    os.utime(file, (mtime, mtime))

    def cookFromRepository(self, troveName, buildLabel = None, ignoreDeps = False):
        if buildLabel:
            oldLabel = self.cfg.buildLabel
            self.cfg.buildLabel = buildLabel

        repos = self.openRepository()
        built = cook.cookItem(repos, self.cfg, troveName, ignoreDeps = ignoreDeps)

        if buildLabel:
            self.cfg.buildLabel = oldLabel

        return built[0]

    def verifyFile(self, file, contents):
	f = open(file, "r")
	other = f.read()
	if other != contents:
	    self.fail("contents incorrect for %s" % file)
	assert(other == contents)

    def removeFile(self, root, path, version = None):
        db = database.Database(root, self.cfg.dbPath)
	os.unlink(root + path)
	db.removeFile(path)
	db.close()

    def initializeFlavor(self):
        use.clearFlags()
        for dir in reversed(sys.path):
	    thisdir = os.path.normpath(os.sep.join((dir, 'archive')))
	    if os.path.isdir(thisdir):
                archiveDir = thisdir
		break
        self.cfg.useDirs = archiveDir + '/use'
        self.cfg.archDirs = archiveDir + '/arch'
        self.cfg.initializeFlavors()
        use.setBuildFlagsFromFlavor('', self.cfg.buildFlavor)

    def _cvtVersion(self, verStr):
        if isinstance(verStr, versions.Version):
            return verStr
        if verStr[0] == ':':
            buildLabel = self.cfg.buildLabel
            verStr = '/%s@%s%s' % (buildLabel.getHost(),
                                   buildLabel.getNamespace(),
                                   verStr)
        elif verStr[0] != '/':
            verStr = '/%s/%s' % (self.cfg.buildLabel.asString(), verStr)
        try:
            v = versions.VersionFromString(verStr)
            v.setTimeStamps([ time.time() for x in v.versions ])
        except versions.ParseError:
            v = versions.ThawVersion(verStr)
        return v

    def addQuickTestCollection(self, name, version, troveList):
        version = self._cvtVersion(version)
        assert(':' not in name and not name.startswith('fileset'))

        flavor = deps.DependencySet()
        fullList = []
        for info in troveList:
            trvFlavor = None
            trvVersion = None
            byDefault = True
            if isinstance(info, str):
                trvName = info
            elif len(info) == 1:
                (trvName,) = info
            elif len(info) == 2:
                (trvName, trvVersion) = info
            elif len(info) == 3:
                (trvName, trvVersion, trvFlavor) = info
            elif len(info) == 4:
                (trvName, trvVersion, trvFlavor, byDefault) = info
            else:
                assert(False)


            if not trvVersion:
                trvVersion = version
            else:
                trvVersion = self._cvtVersion(trvVersion)

            if not trvFlavor:
                trvFlavor = deps.DependencySet()
            elif type(trvFlavor) == str:
                trvFlavor = deps.parseFlavor(trvFlavor)

            flavor.union(trvFlavor, deps.DEP_MERGE_TYPE_DROP_CONFLICTS)
            fullList.append(((trvName, trvVersion, trvFlavor), byDefault))

        coll = trove.Trove(name, version, flavor, None)
        coll.setIsCollection(True)
        for (info, byDefault) in fullList:
            coll.addTrove(*info, **{ 'byDefault' : byDefault })
        coll.setSourceName(name + ":source")

        # create an absolute changeset
        cs = changeset.ChangeSet()
        diff = coll.diff(None, absolute = True)[0]
        cs.newTrove(diff)

        repos = self.openRepository()
        repos.commitChangeSet(cs)
        return coll

    def addQuickTestComponent(self, troveName, version, flavor='',
                              fileContents=None,
                              provides=deps.DependencySet(),
                              requires=deps.DependencySet(),
                              filePrimer=0, setConfigFlags = True):
        troveVersion = self._cvtVersion(version)

        assert(':' in troveName)

        # set up a file with some contents
        fileList = []
        if fileContents is None:
            cont = self.workDir + '/contents%s' % filePrimer
            f = open(cont, 'w')
            f.write('hello, world!\n')
            f.close()
            if not filePrimer:
                filePrimer = '0'
            filePrimer = str(filePrimer)
            repeats = (32 / len(filePrimer) + 1)
            pathId = (filePrimer * repeats)[:32]
            pathId = sha1helper.md5FromString(pathId)
            f = files.FileFromFilesystem(cont, pathId)
            fileList.append((f, '/contents%s' % filePrimer, pathId, troveVersion))
        else:
            index = 0
            for fileInfo in fileContents:
                fileName, contents = fileInfo[0:2]
                if len(fileInfo) > 3:
                    fileDeps = fileInfo[3]
                else:
                    fileDeps = None

                cont = self.workDir + '/' + fileName
                dir = os.path.dirname(cont)
                if not os.path.exists(dir):
                    os.mkdir(dir)
                f = open(cont, 'w')
                f.write(contents)
                f.close()
                pathId = sha1helper.md5String(fileName)
                f = files.FileFromFilesystem(cont, pathId)
                if fileDeps is not None:
                    f.requires.set(fileDeps)
                if setConfigFlags and fileName.startswith('/etc'):
                    f.flags.isConfig(True)
                index += 1

                if len(fileInfo) > 2 and fileInfo[2] is not None:
                    fileVersion = self._cvtVersion(fileInfo[2])
                else:
                    fileVersion = troveVersion
                fileList.append((f, fileName, pathId, fileVersion))
        # create an absolute changeset
        cs = changeset.ChangeSet()
        # add a pkg diff

        flavor = deps.parseFlavor(flavor)
        t = trove.Trove(troveName, troveVersion, flavor, None)
        if isinstance(requires, str):
            req = deps.parseDep(requires)
        else:
            req = requires.copy()

        for f, name, pathId, fileVersion in fileList:
            if not troveName.endswith(':source'):
                name = '/' + name

            t.addFile(pathId, name, fileVersion, f.fileId())
            req.union(f.requires())
        t.setRequires(req)
        if not troveName.endswith(':source'):
            t.setSourceName(troveName.split(":")[0] + ":source")

        if isinstance(provides, str):
            prov = deps.parseDep(provides)
        else:
            prov = provides.copy()

        prov.union(deps.parseDep('trove: %s' % t.getName()))
        t.setProvides(prov)
        t.computePathHashes()
        diff = t.diff(None, absolute = True)[0]
        cs.newTrove(diff)

        # add the file and file contents
        for f,name, pathId, fileVersion in fileList:
            cs.addFile(None, f.fileId(), f.freeze())
            cs.addFileContents(pathId, changeset.ChangedFileTypes.file,
                               filecontents.FromFilesystem(
                                 os.path.normpath(self.workDir + '/' + name)),
                               f.flags.isConfig())
        repos = self.openRepository()
        repos.commitChangeSet(cs)
        return t
    
    
    def __init__(self, methodName):
	testsuite.TestCase.__init__(self, methodName)

        if 'CONARY_IDGEN' in os.environ:
            className = "IdGen%s" % os.environ['CONARY_IDGEN']
            cook._IdGen = sys.modules[__name__].__dict__[className]

        if testsuite.isIndividual():
            # if we're running a test case by itself, don't clean up
            # and use a constant path
            self.topDir = '/tmp/conarytest'
            if not os.access(self.topDir, os.W_OK):
                self.topDir = '/tmp/conarytest-%s' \
                                            % pwd.getpwuid(os.getuid())[0]
            self.cleanupDir = False
            
	if self.topDir:
	    self.tmpDir = self.topDir
	    if os.path.isdir(self.tmpDir):
		util.rmtree(self.tmpDir)
	    os.mkdir(self.tmpDir)
	else:
	    self.tmpDir = tempfile.mkdtemp()

	self.reposDir = self.tmpDir + "/repos"
	self.workDir = self.tmpDir + "/work"
	self.buildDir = self.tmpDir + "/build"
	self.rootDir = self.tmpDir + "/root"
	self.cacheDir = self.tmpDir + "/cache"
        self.imagePath = self.tmpDir + "/images"
	os.mkdir(self.reposDir)
	os.mkdir(self.workDir)
	os.mkdir(self.rootDir)
	os.mkdir(self.cacheDir)
        os.mkdir(self.imagePath)
	self.cfg = conarycfg.ConaryConfiguration(False)
	self.cfg.name = 'Test'
	self.cfg.contact = 'http://bugzilla.rpath.com/'
	self.cfg.installLabelPath = [ self.defLabel ]
	self.cfg.installLabel = self.defLabel
	self.cfg.buildLabel = self.defLabel
        self.cfg.sourceSearchDir = self.workDir
        self.cfg.buildPath = self.buildDir
	self.cfg.dbPath = '/var/lib/conarydb'
	self.cfg.debugRecipeExceptions = True
	self.cfg.repositoryMap = {}
        self.cfg.useDir = None
        self.cfg.quiet = True

        global _servers
        self.servers = _servers

	self.cfg.root = self.rootDir
	self.cfg.lookaside = self.cacheDir
	revsyspath = sys.path[:]
	revsyspath.reverse()
	for dir in revsyspath:
	    thisdir = os.path.normpath(os.sep.join((dir, 'archive')))
	    if os.path.isdir(thisdir):
		self.cfg.sourceSearchDir = os.path.abspath(thisdir)
		break
	del revsyspath
	os.umask(0022)

    def __del__(self):
	if self.cleanupDir:
            server = self.servers.getServer()
            if server is not None:
                server.stop()
	    util.rmtree(self.tmpDir)
        else:
            global notCleanedUpWarning
            if notCleanedUpWarning:
                sys.stderr.write("Note: not cleaning up %s\n" %self.tmpDir)
                notCleanedUpWarning = False

notCleanedUpWarning = True
