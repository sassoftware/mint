#
# Copyright (c) 2004-2005 rpath, Inc.
#

#python
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
from webunit import webunittest

#conary
import sqlite3
import branch
from build import cook
from build import recipe, use
import checkin
import conaryclient
import conarycfg
import cvc
import deps
import files
import flavorcfg
from lib import log
from lib import sha1helper
from lib import util
from local import database
from repository import netclient, changeset, filecontents
import repository
import trove
import updatecmd
import versions

#mint
from mint import dbversion
from mint import mint
from mint import users
from mint import config
from mint import shimclient

#test
import recipes
import testsuite

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
        os.system("cd %s; echo foo | ./server.py --add-user test %s" 
                  % (self.serverDir, self.reposDir))
        os.system("cd %s; echo anonymous | ./server.py --add-user anonymous %s" 
                  % (self.serverDir, self.reposDir))

class ApacheServer(ChildRepository):
    def __init__(self, name, server, serverDir, reposDir, conaryPath,
                 mintPath, repMap, useCache = False):
        ChildRepository.__init__(self, name, server, serverDir, reposDir,
                                 conaryPath)
        self.serverpid = -1

        self.mintPath = mintPath
        self.serverRoot = tempfile.mkdtemp()
	os.mkdir(self.serverRoot + "/tmp")
        os.mkdir(self.reposDir + "/repos/")
	os.symlink("/usr/lib/httpd/modules", self.serverRoot + "/modules")
	testDir = os.path.realpath(os.path.dirname(
            sys.modules['rephelp'].__file__))
	os.system("sed 's|@NETRPATH@|%s|;s|@CONARYPATH@|%s|;s|@PORT@|%s|;"
		       "s|@DOCROOT@|%s|;s|@MINTPATH@|%s|'"
		    " < %s/server/httpd.conf.in > %s/httpd.conf"
		    % (self.serverDir, conaryPath, str(self.port),
		       self.serverRoot, mintPath, testDir,
                       self.serverRoot))
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
        f = open("%s/mint.conf" % self.serverRoot, "w")
        print >> f, 'dbPath %s' % self.reposDir + '/mintdb'
        print >> f, 'authDbPath %s' % self.reposDir + '/sqldb'
        print >> f, 'reposPath %s' % self.reposDir + '/repos/'
        print >> f, 'authRepoMap %s http://test:foo@localhost:%d/conary/' % (self.name, self.port)
        f.close()

    def __del__(self):
	self.stop()
	shutil.rmtree(self.serverRoot)

    def getMap(self, user = 'test', password = 'foo'):
        return {self.name: 'http://%s:%s@localhost:%d/conary/' %
                                        (user, password, self.port) }

    def reset(self):
        self.stop()
        self.start()

    def start(self):
        shutil.rmtree(self.reposDir)
        os.mkdir(self.reposDir)
        self.createUser()
        self.createMintUser()
        if self.serverpid != -1:
            return

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

    def createMintUser(self):
        cfg = config.MintConfig()
        cfg.read("%s/mint.conf" % self.serverRoot)
        db = sqlite3.connect(self.reposDir + "/mintdb", timeout = 30000)
        versionTable = dbversion.VersionTable(db)
        usersTable = users.UsersTable(db, cfg)
        usersTable.new(username="test",
                       fullName="Test User",
                       email="test@example.com",
                       active = True)
       
    def stop(self):
        if self.serverpid != -1:
            # HACK
            os.system("ipcs  -s  | awk '/^0x/ {print $2}' | xargs -n1 -r ipcrm -s")

            os.kill(self.serverpid, signal.SIGTERM)
            os.waitpid(self.serverpid, 0)
            self.serverpid = -1

class ApacheServerWithCache(ApacheServer):
    def __init__(self, name, server, serverDir, reposDir, conaryPath, repMap):
        ApacheServer.__init__(self, name, server, serverDir, reposDir,
                              conaryPath, repMap, useCache = True)

class ServerCache:

    def __init__(self):
        self.servers = [ None ] * 5

    def startServer(self, reposDir, conaryPath, mintPath, serverIdx = 0):
        if self.servers[serverIdx] is not None:
            return self.servers[serverIdx]

        name = 'localhost'
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
        serverDir = os.environ.get('CONARY_PATH') + '/server'
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

    def getMap(self, user = 'test', password = 'foo'):
        servers = {}
        for server in self.servers:
            if server:
                servers.update(server.getMap(user = user, password = password))
        return servers

    def getMintUrl(self):
        for server in self.servers:
            return "http://%%s:%%s@localhost:%d/mint/" % server.port
                        
    
_servers = ServerCache()

class RepositoryHelper(testsuite.TestCase):
    topDir = None
    cleanupDir = True
    defLabel = versions.Label("localhost@spx:linux")

    def setUp(self):
        # set up the flavor based on the defaults in use
        self.initializeFlavor()
        self._origFlavor = use.allFlagsToFlavor('')
        self._origDir = os.getcwd()
        testsuite.TestCase.setUp(self)
        self.cfg.buildLabel = self.defLabel

    def tearDown(self):
        self.resetFlavors()
        self.reset()
        os.chdir(self._origDir)
        testsuite.TestCase.tearDown(self)
        self.cfg.excludeTroves = []
        
    def getRepositoryClient(self, user = 'test', password = 'foo'):
        rmap = self.servers.getMap(user = user, password = password)
	return netclient.NetworkRepositoryClient(rmap)

    def printRepMap(self):
        rmap = self.servers.getMap()
        for name, url in rmap.items():
            print 'repositoryMap %s %s' %(name, url)

    def openRepository(self, serverIdx=0):
        server = self.servers.startServer(self.reposDir, self.conaryDir,
                                          self.mintDir, serverIdx)
        # make sure map is up to date
        self.cfg.repositoryMap.update(self.servers.getMap())

	count = 0
	repos = netclient.NetworkRepositoryClient(self.cfg.repositoryMap)

        name = "localhost"
        if serverIdx:
            name += "%d" % serverIdx
        label = versions.Label("%s@spx:linux" % name)
						   
	while count < 50:
	    try:
                repos.troveNames(label)
		return repos
	    except:
		pass

	    time.sleep(0.1)
	    count += 1

	raise RuntimeError, "unable to open networked repository"

    def openMint(self, authToken=('test', 'foo')):
        self.openRepository()
        #self.openRepository(serverIdx = 1)
        cfg = config.MintConfig()
        cfg.read("%s/mint.conf" % self.servers.getServer().serverRoot)
        return shimclient.ShimMintClient(cfg, authToken)
                    
    def addfile(self, file):
        cvc.sourceCommand(self.cfg, [ "add", file ], {} )

    def describe(self, file):
        cvc.sourceCommand(self.cfg, [ 'describe', file ], {} )

    def mkbranch(self, src, new, what, shadow = False):
	if type(src) == str and src[0] != "/" and src.find("@") == -1:
	    src = "/" + self.cfg.buildLabel.asString() + "/" + src
        elif not isinstance(src, str):
            src = src.asString()

	if type(new) == str and new[0] == "@":
	    new = versions.Label("localhost" + new)
        elif isinstance(new, str):
            new = versions.Label(new)

        repos = self.openRepository()

        branch.branch(repos, self.cfg, new.asString(), 
                      troveSpec = what + '=' + src, makeShadow = shadow)

    def checkout(self, name, versionStr = None, dir = None):
	self.openRepository()
	dict = {}
	if dir:
	    dict = { "dir" : dir }

	if versionStr:
	    cvc.sourceCommand(self.cfg, [ "checkout", name +'='+ versionStr ], 
				 dict )
	else:
	    cvc.sourceCommand(self.cfg, [ "checkout", name ], dict )

    def commit(self):
	self.openRepository()
	cvc.sourceCommand(self.cfg, [ "commit" ], { 'message' : 'foo' })

    def diff(self, *args):
	self.openRepository()
	(rc, str) = self.captureOutput(cvc.sourceCommand, 
				       self.cfg, [ "diff" ] + list(args), {})
	# (working version) Thu Jul  1 09:51:03 2004 (no log message)
	# -> (working version) (no log message)
	str = re.sub(r'\) .* \(', ') (', str, 1)
	return str

    def showLog(self, *args):
        self.openRepository()
        (rc, str) = self.captureOutput(cvc.sourceCommand,
                                        self.cfg, [ "log" ] + list(args), {})
        # 1.0-2 Test (http://buzilla.specifixinc.com/) Mon Nov 22 12:11:24 2004
	# -> 1.0-2 Test
	str = re.sub(r'\(http://bugzilla.specifix.com/\) .*', '', str)
        return str

    def annotate(self, *args):
	self.openRepository()
	(rc, str) = self.captureOutput(cvc.sourceCommand, 
				       self.cfg, [ "annotate" ] + list(args), 
                                        {})
	# remove date information from string
        # also remove variable space padding 
        str = re.sub(r'(\n[^ ]*) *\((.*) .*\):', r'\1 (\2):', str)
        # first line doesn't have an \n
        str = re.sub(r'^([^ ]*) *\((.*) .*\):', r'\1 (\2):', str)
	return str

    def rdiff(self, *args):
	self.openRepository()
	(rc, str) = self.captureOutput(cvc.sourceCommand,
				       self.cfg, [ "rdiff" ] + list(args), 
                                        {})
        str = re.sub(r'\(http://bugzilla.specifix.com/\).*', '(http://bugzilla.specifix.com/)', str, 1)
	return str

    def newpkg(self, name):
	self.openRepository()
	cvc.sourceCommand(self.cfg, [ "newpkg", name], {})

    def makeSourceTrove(self, name, recipeFile, branch=None):
        origDir = os.getcwd()
        os.chdir(self.workDir)
        self.newpkg(name)
        os.chdir(name)
        self.writeFile(name + '.recipe', recipeFile)
        self.addfile(name + '.recipe')
        self.commit()
        os.chdir(origDir)

    def updateSourceTrove(self, name, recipeFile, versionStr=None):
        origDir = os.getcwd()
        os.chdir(self.workDir)
        self.checkout(name, versionStr=versionStr)
        os.chdir(name)
        self.writeFile(name + '.recipe', recipeFile)
        self.commit()
        os.chdir(origDir)

    def remove(self, name):
	self.openRepository()
	cvc.sourceCommand(self.cfg, [ "remove", name], {})

    def rename(self, oldname, newname):
	self.openRepository()
	cvc.sourceCommand(self.cfg, [ "rename", oldname, newname], {})

    def update(self, *args):
	self.openRepository()
	cvc.sourceCommand(self.cfg, [ "update" ] + list(args), {})

    def resetFlavors(self):
        use.clearFlags()
        use.track(False)

    def resetAllRepositories(self):
        self.servers.resetAllServers()
	self.openRepository()

    def merge(self, *args):
	self.openRepository()
	cvc.sourceCommand(self.cfg, [ "merge" ] + list(args), {})

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
        sys.excepthook = util.genExcepthook(False)

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

    def addQuickTestPkg(self, name, version, flavor='', label=None,
                        fileContents=''):
        if label is None:
            label = self.cfg.buildLabel

        # set up a file with some contents
        fileList = []
        if not fileContents:
            cont = self.workDir + '/contents'
            f = open(cont, 'w')
            f.write('hello, world!\n')
            f.close()
            pathId = sha1helper.md5FromString('0' * 32)
            f = files.FileFromFilesystem(cont, pathId)
            fileList.append((f, cont, pathId))
        else:
            index = 0
            for name, contents in fileContents:
                cont = self.workDir + '/' + name
                f = open(cont, 'w')
                f.write(contents)
                f.close()
                pathId = sha1helper.md5FromString('0' * 31 + str(index))
                f = files.FileFromFilesystem(cont, pathId)
                index += 1
                fileList.append((f, name, pathId))
        # create an absolute changeset
        cs = changeset.ChangeSet()

        # add a pkg diff
        v = versions.VersionFromString(version)
        v.setTimeStamps([ time.time() for x in v.versions ])

        flavor = deps.deps.parseFlavor(flavor)
        t = trove.Trove(name, v, flavor, None)
        for f, name, pathId in fileList:
            t.addFile(pathId, '/' + name, v, f.fileId())
        diff = t.diff(None, absolute = 1)[0]
        cs.newPackage(diff)

        # add the file and file contents
        for f,name, pathId in fileList:
            cs.addFile(None, f.fileId(), f.freeze())
            cs.addFileContents(pathId, changeset.ChangedFileTypes.file,
                               filecontents.FromFilesystem(
                                            os.path.join(self.workDir, name)),
                               f.flags.isConfig())
        repos = self.openRepository()
        repos.commitChangeSet(cs)

    def addTestPkg(self, num, requires=[], fail=False, content='', 
                   flags=[], localflags=[], packageSpecs=[], subPackages=[], 
                   version='1.0', branch=None, 
                   header='', fileContents='',
                   tag=None, binary=False):
        """ This method is a wrapper around the recipes.py createRecipe 
            method.  It creates the recipe with the given characteristics,
            and then commits it to the repository.

            num = recipe name is 'test%(num)s
            requires = other packages added to the buildRequires of 
                        this package
            fail - if true, an exit(1) is added
            fileContents - contents of the text file in the package
            content - place to add content to the recipe setup() function
            header - place to add content to the recipe before setup()
            branch - place this source component on a branch
            localFlags - check Flags.foo for this recipe for every foo passed in
            flags - check use.[Arch,Use].foo, for every [Arch,Use].foo passed in
        """
        origDir = os.getcwd()
        os.chdir(self.workDir)
        pkgname = 'test%d' % num
        if not 'packages' in self.__dict__:
            self.packages = {}
        if num in self.packages:
            self.checkout(pkgname, branch)
        else:
            self.newpkg(pkgname)
        os.chdir(pkgname)
        if not isinstance(subPackages, (tuple, list)):
            subPackages = [subPackages]
        if not isinstance(packageSpecs, (tuple, list)):
            packageSpecs = [packageSpecs]
        fileContents = recipes.createRecipe(num, requires, fail, content, 
            packageSpecs, subPackages, version=version, flags=flags, 
            localflags=localflags, header=header, fileContents=fileContents, 
            tag=tag, binary=binary)
        self.writeFile(pkgname + '.recipe', fileContents)
        if num not in self.packages:
            self.addfile(pkgname + '.recipe')
        self.commit()
        os.chdir('..')
        shutil.rmtree(pkgname)
        os.chdir(origDir)
        self.packages[num] = pkgname
        return fileContents

    def cookTestPkg(self, num, logLevel=log.WARNING, macros={}):
        return cook.cookItem(self.repos, self.cfg, 'test%s' % num, macros=macros)

    def cookFromRepository(self, troveName, buildLabel = None):
        if buildLabel:
            oldLabel = self.cfg.buildLabel
            self.cfg.buildLabel = buildLabel

        repos = self.openRepository()
        built = cook.cookItem(repos, self.cfg, troveName)

        if buildLabel:
            self.cfg.buildLabel = oldLabel

        return built[0]

    def verifyFifo(self, file):
	return stat.S_ISFIFO(os.lstat(file).st_mode)

    def verifyFile(self, file, contents):
	f = open(file, "r")
	other = f.read()
	if other != contents:
	    self.fail("contents incorrect for %s" % file)
	assert(other == contents)

    def verifyNoFile(self, file):
        try:
            f = open(file, "r")
        except IOError, err:
            if err.errno == 2:
                return
            else:
                self.fail("verifyNoFile returned unexpected error code: %d" % err.errno)
        else:
            self.fail("file exists: %s" % file)

    def verifySrcDirectory(self, contents, dir = "."):
	self.verifyDirectory(contents + [ "CONARY" ], dir)

    def verifyDirectory(self, contents, dir = "."):
	self.verifyFileList(contents, os.listdir(dir))

    def verifyPackageFileList(self, pkg, ideal):
	list = [ x[1] for x in pkg.iterFileList() ]
	self.verifyFileList(ideal, list)

    def verifyTroves(self, pkg, ideal):
	actual = [ (x[0], x[1].asString(), x[2]) for x in pkg.iterTroveList() ]
        if actual != ideal:
            self.fail("troves don't match expected: got %s expected %s"
                      %(actual, ideal))

    def verifyFileList(self, ideal, actual):
	dict = {}
	for n in ideal: dict[n] = 1

	for n in actual:
	    if dict.has_key(n):
		del dict[n]
	    else:
		self.fail("unexpected file %s" % n)
	if dict:
	    self.fail("files missing %s" % " ".join(dict.keys()))

	assert(not dict)

    def verifyInstalledFileList(self, dir, list):
	paths = {}
	for path in list:
	    paths[path] = True
	dirLen = len(dir)
	    
	# this skips all of /var/lib/conarydb/
	for (dirName, dirNameList, pathNameList) in os.walk(dir):
	    for path in pathNameList:
		if path[0] == ".": continue
		fullPath = dirName[dirLen:] + "/" + path
		if fullPath.startswith("/var/lib/conarydb/"): continue
		if paths.has_key(fullPath):
		    del paths[fullPath]
		else:
		    self.fail("unexpected file %s" % fullPath)

	if paths:
	    self.fail("files missing %s" % " ".join(paths.keys()))

    def cookObject(self, theClass, prep=False, macros={}, sourceVersion = None,
                   serverIdx = 0, ignoreDeps = False):
	repos = self.openRepository(serverIdx)
        if sourceVersion is None:
            sourceVersion = cook.guessSourceVersion(repos, theClass.name, 
                                                    theClass.version,
                                                    self.cfg.buildLabel,
                                                    searchBuiltTroves=True)
        if not sourceVersion:
            # just make up a sourceCount -- there's no version in 
            # the repository to compare against
            sourceVersion = versions.VersionFromString('/%s/%s-1' % (
                                               self.cfg.buildLabel.asString(),
                                               theClass.version))
        use.resetUsed()
        stdout = os.dup(sys.stdout.fileno())
        stderr = os.dup(sys.stderr.fileno())
        null = os.open('/dev/null', os.O_WRONLY)
        os.dup2(null, sys.stdout.fileno())
        os.dup2(null, sys.stderr.fileno())

        try:
	    builtList = cook.cookObject(repos, self.cfg, theClass,
                                        sourceVersion,
					prep=prep, macros=macros,
                                        allowMissingSource=True,
                                        ignoreDeps=ignoreDeps)
        finally:
            os.dup2(stdout, sys.stdout.fileno())
            os.dup2(stderr, sys.stderr.fileno())
            os.close(null)
            os.close(stdout)
            os.close(stderr)
	    repos.close()
    
	return builtList

    def updatePkg(self, root, pkg, version = None, tagScript = None,
		  keepExisting = False, replaceFiles = False,
                  resolve = False, depCheck = True, justDatabase = False,
                  flavor = None, recurse = True):
	newcfg = self.cfg
	newcfg.root = root

	repos = self.openRepository()
	if type(pkg) == str:
            if version is not None:
                if type(version) is not str:
                    version = version.asString()
                item = "%s=%s" % (pkg, version)
            else:
                item = pkg

            if flavor is not None:
                item += '[%s]' % flavor

            newcfg.autoResolve = resolve

	    updatecmd.doUpdate(newcfg, [ item ],
			       tagScript = tagScript,
			       keepExisting = keepExisting,
                               replaceFiles = replaceFiles,
                               depCheck = depCheck,
                               justDatabase = justDatabase,
                               recurse = recurse)
        elif type(pkg) == list:
            assert(version is None)
            assert(flavor is None)

            newcfg.autoResolve = resolve

	    updatecmd.doUpdate(newcfg, pkg,
			       tagScript = tagScript,
			       keepExisting = keepExisting,
                               replaceFiles = replaceFiles,
                               depCheck = depCheck,
                               justDatabase = justDatabase,
                               recurse = recurse)
	else:
	    # pkg should be a change set
	    if pkg.isAbsolute():
		cl = conaryclient.ConaryClient(self.cfg)
		cl._rootChangeSet(pkg, keepExisting = keepExisting)
		del cl

	    db = database.Database(root, self.cfg.dbPath)
	    db.commitChangeSet(pkg, keepExisting = keepExisting,
			       tagScript = tagScript, 
                               replaceFiles = replaceFiles,
                               justDatabase = justDatabase)
	    db.close()

    def erasePkg(self, root, pkg, version = None, tagScript = None,
                 depCheck = True, justDatabase = False, flavor = None):
        db = database.Database(root, self.cfg.dbPath)

        if type(pkg) == list:
            updatecmd.doErase(self.cfg, pkg, 
                              tagScript = tagScript, depCheck = depCheck,
                              justDatabase = justDatabase)
        elif version and flavor:
            updatecmd.doErase(self.cfg, [ "%s=%s[%s]" % (pkg, version, 
                                                         flavor) ], 
                              tagScript = tagScript, depCheck = depCheck,
                              justDatabase = justDatabase)
        elif version:
            updatecmd.doErase(self.cfg, [ "%s=%s" % (pkg, version) ], 
                              tagScript = tagScript, depCheck = depCheck,
                              justDatabase = justDatabase)
        elif flavor:
            updatecmd.doErase(self.cfg, [ "%s[%s]" % (pkg, flavor) ], 
                              tagScript = tagScript, depCheck = depCheck,
                              justDatabase = justDatabase)
        else:
            updatecmd.doErase(self.cfg, [ "%s" % (pkg) ], 
                              tagScript = tagScript, depCheck = depCheck,
                              justDatabase = justDatabase)
        db.close()

    def removeFile(self, root, path, version = None):
        db = database.Database(root, self.cfg.dbPath)
	os.unlink(root + path)
	db.removeFile(path)
	db.close()

    def build(self, str, name, dict = {}, sourceVersion = None, serverIdx = 0):
        use.setBuildFlagsFromFlavor(name, self.cfg.buildFlavor)
        
	(built, d) = self.buildRecipe(str, name, dict, 
				      sourceVersion = sourceVersion)
	(name, version, flavor) = built[0]
	version = versions.VersionFromString(version)
	repos = self.openRepository(serverIdx)
	pkg = repos.getTrove(name, version, flavor)
	return pkg

    def buildRecipe(self, theClass, theName, vars = {}, prep=False, macros={},
		    sourceVersion = None, d = {}, serverIdx = 0,
                    logLevel = log.WARNING, ignoreDeps=False):
	built = []
	recipe.setupRecipeDict(d, "test1")

	code = compile(theClass, theName, "exec")
	exec code in d
	d[theName].filename = "test"
	
	for name in vars.iterkeys():
	    d[theName].__dict__[name] = vars[name]

        
        level = log.getVerbosity()
        log.setVerbosity(logLevel)
	built = self.cookObject(d[theName], prep=prep, macros=macros,
                                sourceVersion=sourceVersion,
                                serverIdx = serverIdx, 
                                ignoreDeps = ignoreDeps)
        log.setVerbosity(level)
	return (built, d)

    def overrideBuildFlavor(self, flavorStr):
        flavor = deps.deps.parseFlavor(flavorStr)
        if flavor is None:
            raise RuntimeError, 'Invalid flavor %s' % flavorStr 
        buildFlavor = self.cfg.buildFlavor.copy()
        if deps.deps.DEP_CLASS_IS in buildFlavor.getDepClasses():
            # instruction set deps are overridden completely -- remove 
            # any buildFlavor instruction set info
            del buildFlavor.members[deps.deps.DEP_CLASS_IS]
        buildFlavor.union(flavor,
                          mergeType = deps.deps.DEP_MERGE_TYPE_OVERRIDE)
        self.cfg.buildFlavor = buildFlavor

    def initializeFlavor(self):
        use.clearFlags()
        for dir in reversed(sys.path):
	    thisdir = os.path.normpath(os.sep.join((dir, 'archive')))
	    if os.path.isdir(thisdir):
                archiveDir = thisdir
		break
        flavorConfig = flavorcfg.FlavorConfig(archiveDir + '/use', 
                                              archiveDir + '/arch')
        self.cfg.configLine('flavor is: x86(i686)')
        self.cfg.flavor = flavorConfig.toDependency(override=self.cfg.flavor)
        #insSet = deps.deps.DependencySet()
        #for dep in deps.arch.currentArch:
        #    insSet.addDep(deps.deps.InstructionSetDependency, dep)
        #self.cfg.flavor.union(insSet)
        self.cfg.buildFlavor = self.cfg.flavor[0].copy()
        flavorConfig.populateBuildFlags()
        use.setBuildFlagsFromFlavor('', self.cfg.buildFlavor)

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
	os.mkdir(self.reposDir)
	os.mkdir(self.workDir)
	os.mkdir(self.rootDir)
	os.mkdir(self.cacheDir)
	self.cfg = conarycfg.ConaryConfiguration(False)
	self.cfg.name = 'Test'
	self.cfg.contact = 'http://bugzilla.specifix.com/'
	self.cfg.installLabelPath = [ self.defLabel ]
	self.cfg.installLabel = self.defLabel
	self.cfg.buildLabel = self.defLabel
        self.cfg.sourceSearchDir = self.workDir
        self.cfg.buildPath = self.buildDir
	self.cfg.dbPath = '/var/lib/conarydb'
	self.cfg.debugRecipeExceptions = True
	self.cfg.repositoryMap = {}
        self.cfg.useDir = None

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

    def getWebTestUrl(self):
        parts = urlparse(self.mintUrl)
        return parts[1].split(":")

    def getMintClient(self, username, password):
        client = self.openMint(('test', 'foo'))
        userId = client.registerNewUser(username, password, "Test User",
                "test@example.com", "test at example.com", "", active=True)

        return self.openMint((username, password))

class WebRepositoryHelper(RepositoryHelper, webunittest.WebTestCase):
    def __init__(self, methodName):
        RepositoryHelper.__init__(self, methodName)
        webunittest.WebTestCase.__init__(self, methodName)

    def setUp(self):
        RepositoryHelper.setUp(self)
        webunittest.WebTestCase.setUp(self)
        self.server, self.port = self.getWebTestUrl()

    def activateUsers(self):
        os.system("echo 'UPDATE Users SET active=1;' | sqlite3 /data/mint/data/db")

notCleanedUpWarning = True
