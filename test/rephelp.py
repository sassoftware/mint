#
# Copyright (c) 2004-2005 rpath, Inc.
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
from webunit import webunittest

#conary
import sqlite3
import branch
from build import cook
from build import recipe, use
import checkin
import clone
import conaryclient
import conarycfg
import cscmd
import cvc
import deps
import files
import flavorcfg
from lib import log
from lib import sha1helper
from lib import util
from lib import openpgpkey
from lib import openpgpfile
from local import database
from repository import netclient, changeset, filecontents
import repository
import trove
import updatecmd
import versions

#test
import recipes
import testsuite

#mint
from mint import dbversion
from mint import mint
from mint import users
from mint import config

# this is an override for deps.arch.x86flags -- we never want to use
# any system flags (normally gathered from places like /proc/cpuinfo)
# because they could change the results from run to run
def x86flags(archTag, *args):
    # always pretend we're on i686 for x86 machines
    if archTag == 'x86':
        flags = []
        for f in ('i486', 'i586', 'i686'):
            flags.append((f, deps.deps.FLAG_SENSE_PREFERRED))
        return deps.deps.Dependency(archTag, flags)
    # otherwise, just use the archTag with no flags
    return deps.deps.Dependency(archTag)
# override the existing x86flags() function
deps.arch.x86flags = x86flags
# reinitialize deps.arch
deps.arch.initializeArch()

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
        self.needsPGPKey = True

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
        f = open("%s/mint.conf" % self.serverRoot, "w")
        print >> f, 'domainName localhost:%i' % self.port
        print >> f, 'dbPath %s' % self.reposDir + '/mintdb'
        print >> f, 'authDbPath %s' % self.reposDir + '/sqldb'
        print >> f, 'reposPath %s' % self.reposDir + '/repos/'
        print >> f, 'imagesPath %s' % self.reposDir + '/images/'
        print >> f, 'authRepoMap %s http://mintauth:mintpass@127.0.0.1:%d/conary/' % (self.name, self.port)
        print >> f, 'debugMode False'
        print >> f, 'sendNotificationEmails False'
        f.close()

    def __del__(self):
	self.stop()
	shutil.rmtree(self.serverRoot)

    def getMap(self, user = 'mintauth', password = 'mintpass'):
        return {self.name: 'http://%s:%s@127.0.0.1:%d/conary/' %
                                        (user, password, self.port) }

    def reset(self):
        self.stop()
        self.start()
        self.needsPGPKey = True

    def start(self):
        shutil.rmtree(self.reposDir)
        os.mkdir(self.reposDir)
        os.mkdir(self.reposDir + "/images/")
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

class NetworkReposServer(ChildRepository):
    def __init__(self, name, server, serverDir, reposDir, conaryPath, repMap):
        ChildRepository.__init__(self, name, server, serverDir, reposDir,
                                 conaryPath)
        self.repMap = repMap
        self.serverpid = -1
        if 'SERVER_FILE_PATH' in os.environ:
            self.serverFilePath = os.environ['SERVER_FILE_PATH']
            self.delServerPath = False
        else:
            self.serverFilePath =  None
            self.delServerPath = True
        self.serverLog = '/tmp/conary-server-%s.log' % self.name
        try:
            os.unlink(self.serverLog)
        except OSError, err:
            if err.errno == errno.ENOENT:
                pass
            elif err.errno == errno.EPERM:
                try:
                    self.serverLog = '/tmp/conary-server-%s-%s.log' \
                                % (self.name, pwd.getpwuid(os.getuid())[0])
                    os.unlink(self.serverLog)
                except OSError, err:
                    if err.errno == errno.ENOENT:
                        pass
        except OSError:
            pass

    def start(self):
        if self.serverpid != -1:
            return
        shutil.rmtree(self.reposDir)
        os.mkdir(self.reposDir)
        self.createUser()
        
	sb = os.stat(self.server)
	if not stat.S_ISREG(sb.st_mode) or not os.access(self.server, os.X_OK):
	    print "bad server path: %s" % self.server
	    sys.exit(1)

        self.serverpid = os.fork()
        if self.serverpid == 0:
	    os.environ['CONARY_PATH'] = self.conaryPath
            log = os.open(self.serverLog, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
            os.dup2(log, sys.stdout.fileno())
            os.dup2(log, sys.stderr.fileno())
            print "starting server"
            sys.stdout.flush()
            f = open(self.reposDir + '/serverrc', 'w')
            print >> f, 'port %d' %self.port
            for repname, reppath in self.repMap.iteritems():
                print >> f, 'repositoryMap %s %s' %(repname, reppath)
            f.close()

            if self.serverFilePath is None:
                self.serverFilePath = tempfile.mkdtemp()
            args = (self.server, self.reposDir, 
                    self.name, 
                    '--config-file', self.reposDir + '/serverrc', 
                    '--tmp-file-path', self.serverFilePath)
	    os.execv(args[0], args)
        else:
            pass

    def stop(self):
        if self.serverpid != -1:
            os.kill(self.serverpid, signal.SIGKILL)
            os.waitpid(self.serverpid, 0)
            self.serverpid = -1
        if self.serverFilePath and self.delServerPath:
            util.rmtree(self.serverFilePath)
            self.serverFilePath = None

    def getMap(self, user = 'mintauth', password = 'mintpass'):
        return {self.name: 'http://%s:%s@127.0.0.1:%d/' %
                                        (user, password, self.port) }

    def reset(self):
	repos = netclient.NetworkRepositoryClient(self.getMap())
        repos.c[self.name].reset()
        self.createUser()
        self.needsPGPKey = True

    def __del__(self):
        self.stop()


class ExistingServer(RepositoryServer):
    def __init__(self, name, port=8000):
        RepositoryServer.__init__(self, name)
	self.port = port
        self.reposDir = None
        #self.reset()
        
    def getMap(self):
        return {self.name: 'http://mintauth:mintpass@127.0.0.1:%d/' %self.port}

    def reset(self):
	repos = netclient.NetworkRepositoryClient(self.getMap())
        repos.c[self.name].reset()
        self.needsPGPKey = True

    def start(self):
        pass

    def stop(self):
        pass

    def getMap(self, user = 'mintauth', password = 'mintpass'):
        return {self.name: 'http://%s:%s@127.0.0.1:%d/' %
                                        (user, password, self.port) }

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

    def getMap(self, user = 'mintauth', password = 'mintpass'):
        servers = {}
        for server in self.servers:
            if server:
                servers.update(server.getMap(user = user, password = password))
        return servers
    
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

        # set up the keyCache so that it won't prompt for passwords in
        # any of the test suites.
        keyCache = openpgpkey.OpenPGPKeyFileCache()
        openpgpkey.setKeyCache(keyCache)

        # pre-populate private key cache
        keyCache.setPrivatePath(testsuite.archivePath + '/secring.gpg')
        fingerprint = '95B457D16843B21EA3FC73BBC7C32FC1F94E405E'
        keyCache.getPrivateKey(fingerprint, '111111')
        keyCache.getPrivateKey('', '111111')

        # pre-populate public key cache
        keyCache.setPublicPath(testsuite.archivePath + '/pubring.gpg')
        keyCache.getPublicKey('')

    def tearDown(self):
        self.resetFlavors()
        self.reset()
        os.chdir(self._origDir)
        testsuite.TestCase.tearDown(self)
        self.cfg.excludeTroves = conarycfg.RegularExpressionList()
        self.cfg.pinTroves = conarycfg.RegularExpressionList()
        self.logFilter.clear()
        
    def getRepositoryClient(self, user = 'mintauth', password = 'mintpass'):
        rmap = self.servers.getMap(user = user, password = password)
	return netclient.NetworkRepositoryClient(rmap)

    def getPort(self, serverIdx = 0):
        return self.servers.getServer(serverIdx).port

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

        if server.needsPGPKey:
            ascKey = open(testsuite.archivePath + '/key.asc', 'r').read()
            repos.addNewAsciiPGPKey(label, 'mintauth', ascKey)
            server.needsPGPKey = False
        return repos
   
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
        # 1.0-2 Test (http://buzilla.rpath.com/) Mon Nov 22 12:11:24 2004
	# -> 1.0-2 Test
	str = re.sub(r'\(http://bugzilla.rpath.com/\) .*', '', str)
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
        str = re.sub(r'\(http://bugzilla.rpath.com/\).*', '(http://bugzilla.rpath.com/)', str, 1)
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
        callback = checkin.CheckinCallback()
	cvc.sourceCommand(self.cfg, [ "update" ] + list(args), {},
                          callback=callback)

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

    def _cvtVersion(self, verStr):
        if verStr[0] != '/':
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

        flavor = deps.deps.DependencySet()
        fullList = []
        for info in troveList:
            if len(info) == 4:
                (trvName, trvVersion, trvFlavor, byDefault) = info
            elif len(info) == 2:
                (trvName, trvVersion) = info
                trvFlavor = ''
                byDefault = True
            else:
                (trvName, trvVersion, trvFlavor) = info
                byDefault = True

            if type(trvFlavor) == str:
                trvFlavor = deps.deps.parseFlavor(trvFlavor)
            trvVersion = self._cvtVersion(trvVersion)
            flavor.union(trvFlavor, deps.deps.DEP_MERGE_TYPE_DROP_CONFLICTS)
            fullList.append(((trvName, trvVersion, trvFlavor), byDefault))

        coll = trove.Trove(name, version, flavor, None)
        for (info, byDefault) in fullList:
            coll.addTrove(*info, **{ 'byDefault' : byDefault })

        # create an absolute changeset
        cs = changeset.ChangeSet()
        diff = coll.diff(None, absolute = 1)[0]
        cs.newTrove(diff)

        repos = self.openRepository()
        repos.commitChangeSet(cs)
        return coll

    def addQuickTestComponent(self, name, version, flavor='', fileContents=None,
                              provides=deps.deps.DependencySet(),
                              requires=deps.deps.DependencySet(),
                              installBucket = None,
                              filePrimer=0):
        troveVersion = self._cvtVersion(version)

        assert(':' in name)

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
                if fileName.startswith('/etc'):
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

        flavor = deps.deps.parseFlavor(flavor)
        t = trove.Trove(name, troveVersion, flavor, None)
        req = requires.copy()
        for f, name, pathId, fileVersion in fileList:
            t.addFile(pathId, '/' + name, fileVersion, f.fileId())
            req.union(f.requires())
        t.setRequires(req)

        if installBucket is not None:
            t.setInstallBucket(installBucket)

        prov = provides.copy()
        prov.union(deps.deps.ThawDependencySet('4#%s' % 
                                t.getName().replace(':', '::')))
        t.setProvides(prov)
        diff = t.diff(None, absolute = 1)[0]
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

    def addQuickDbTestPkg(self, db, name, version, flavor, 
                          provides=deps.deps.DependencySet(), 
                          requires=deps.deps.DependencySet()):
        fileList = []

        # create a file
        cont = self.workDir + '/contents'
        f = open(cont, 'w')
        f.write('hello, world!\n')
        f.close()
        pathId = sha1helper.md5FromString('0' * 32)
        f = files.FileFromFilesystem(cont, pathId)
        fileList.append((f, cont, pathId))

        v = versions.VersionFromString(version)
        v.setTimeStamps([ time.time() for x in v.versions ])
        flavor = deps.deps.parseFlavor(flavor)
        t = trove.Trove(name, v, flavor, None)
        for f, name, pathId in fileList:
            t.addFile(pathId, '/' + name, v, f.fileId())
        t.setRequires(requires)
        t.setProvides(provides)
	db.addTrove(t)
        db.commit()
        return t

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

    def cookFromRepository(self, troveName, buildLabel = None, ignoreDeps = False):
        if buildLabel:
            oldLabel = self.cfg.buildLabel
            self.cfg.buildLabel = buildLabel

        repos = self.openRepository()
        built = cook.cookItem(repos, self.cfg, troveName, ignoreDeps = ignoreDeps)

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
        if sorted(actual) != sorted(ideal):
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
                   serverIdx = 0, ignoreDeps = False, logBuild = False):
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
                                        ignoreDeps=ignoreDeps,
                                        logBuild=logBuild)
        finally:
            os.dup2(stdout, sys.stdout.fileno())
            os.dup2(stderr, sys.stderr.fileno())
            os.close(null)
            os.close(stdout)
            os.close(stderr)
	    repos.close()
    
	return builtList

    def cookPackageObject(self, theClass, prep=False, macros={}, 
                          sourceVersion = None, serverIdx = 0, 
                          ignoreDeps = False):
        """ cook a package object, return the buildpackage components 
            and package obj 
        """
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
	    res = cook._cookPackageObject(repos, self.cfg, theClass,
                                        sourceVersion,
					prep=prep, macros=macros,
                                        ignoreDeps=ignoreDeps)
        finally:
            os.dup2(stdout, sys.stdout.fileno())
            os.dup2(stderr, sys.stderr.fileno())
            os.close(null)
            os.close(stdout)
            os.close(stderr)
	    repos.close()
        if not res:
            return None
        #return bldList, recipeObj
        return res[0:2]

    def updatePkg(self, root, pkg, version = None, tagScript = None,
		  keepExisting = False, replaceFiles = False,
                  resolve = False, depCheck = True, justDatabase = False,
                  flavor = None, recurse = True, split=True, sync = False,
                  info = False, fromFiles = []):
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
                               recurse = recurse, split = split, 
                               sync = sync, info = info, fromFiles = fromFiles)
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
                               recurse = recurse, split = split,
                               sync = sync, info = info, fromFiles = fromFiles)
	else:
            assert(not info)
            assert(not fromFiles)
            cl = conaryclient.ConaryClient(self.cfg)
            updJob, suggMap = cl.updateChangeSet([pkg], 
                                keepExisting = keepExisting,
                                recurse = recurse, split = split, sync = sync)
            if depCheck:
                assert(not suggMap)
            cl.applyUpdate(updJob, replaceFiles = replaceFiles, 
                           tagScript = tagScript, justDatabase = justDatabase)

    def localChangeset(self, root, pkg, fileName):
        db = database.Database(root, self.cfg.dbPath)
	newcfg = copy.deepcopy(self.cfg)
	newcfg.root = root
        db = database.Database(root, self.cfg.dbPath)
	newcfg = copy.deepcopy(self.cfg)
	newcfg.root = root

	cscmd.LocalChangeSetCommand(db, newcfg, pkg, fileName)

        db.close()

    def erasePkg(self, root, pkg, version = None, tagScript = None,
                 depCheck = True, justDatabase = False, flavor = None):
        db = database.Database(root, self.cfg.dbPath)

        if type(pkg) == list:
            updatecmd.doUpdate(self.cfg, pkg, 
                               tagScript = tagScript, depCheck = depCheck,
                               justDatabase = justDatabase,
                               updateByDefault = False)
        elif version and flavor:
            updatecmd.doUpdate(self.cfg, [ "%s=%s[%s]" % (pkg, version, 
                                                         flavor) ], 
                               tagScript = tagScript, depCheck = depCheck,
                               justDatabase = justDatabase,
                               updateByDefault = False)
        elif version:
            updatecmd.doUpdate(self.cfg, [ "%s=%s" % (pkg, version) ], 
                               tagScript = tagScript, depCheck = depCheck,
                               justDatabase = justDatabase,
                               updateByDefault = False)
        elif flavor:
            updatecmd.doUpdate(self.cfg, [ "%s[%s]" % (pkg, flavor) ], 
                               tagScript = tagScript, depCheck = depCheck,
                               justDatabase = justDatabase,
                               updateByDefault = False)
        else:
            updatecmd.doUpdate(self.cfg, [ "%s" % (pkg) ], 
                               tagScript = tagScript, depCheck = depCheck,
                               justDatabase = justDatabase,
                               updateByDefault = False)
        db.close()

    def removeFile(self, root, path, version = None):
        db = database.Database(root, self.cfg.dbPath)
	os.unlink(root + path)
	db.removeFile(path)
	db.close()

    def build(self, str, name, dict = {}, sourceVersion = None, serverIdx = 0):
	(built, d) = self.buildRecipe(str, name, dict, 
				      sourceVersion = sourceVersion)
	(name, version, flavor) = built[0]
	version = versions.VersionFromString(version)
	repos = self.openRepository(serverIdx)
	pkg = repos.getTrove(name, version, flavor)
	return pkg

    def buildRecipe(self, theClass, theName, vars = {}, prep=False, macros={},
		    sourceVersion = None, d = {}, serverIdx = 0,
                    logLevel = log.WARNING, ignoreDeps=False,
                    logBuild=False):

        use.setBuildFlagsFromFlavor(theName, self.cfg.buildFlavor)

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
                                ignoreDeps = ignoreDeps,
                                logBuild = logBuild)
        log.setVerbosity(level)
	return (built, d)

    def buildPackageObject(self, theClass, theName, vars = {}, prep=False, 
                        macros={}, sourceVersion = None, d = {}, serverIdx = 0,
                        logLevel = log.WARNING, ignoreDeps=False):
        use.setBuildFlagsFromFlavor(theName, self.cfg.buildFlavor)

	built = []
	recipe.setupRecipeDict(d, "test1")

	code = compile(theClass, theName, "exec")
	exec code in d
	d[theName].filename = "test"
	
	for name in vars.iterkeys():
	    d[theName].__dict__[name] = vars[name]

        
        level = log.getVerbosity()
        log.setVerbosity(logLevel)
	built = self.cookPackageObject(d[theName], prep=prep, macros=macros,
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

    def pin(self, troveName):
        updatecmd.changePins(self.cfg, [ troveName ], True)

    def unpin(self, troveName):
        updatecmd.changePins(self.cfg, [ troveName ], False)

    def clone(self, targetLabel, troveSpec):
        clone.CloneTrove(self.cfg, targetLabel, troveSpec)

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
