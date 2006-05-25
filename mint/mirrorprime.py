#!/usr/bin/python
#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#
import BaseHTTPServer
import simplejson
import threading
import os
import stat
import subprocess

from conary.lib import util
from conary.lib import sha1helper
from conary.repository.netrepos import netserver

tarThread = None
copyThread = None

sourcePath = "/mnt/"
needsMount = False

# derive tmp path via config file
from mint import config
mc = config.MintConfig()
mc.read(config.RBUILDER_CONFIG)
tmpPath = os.path.join(mc.dataPath, 'tmp', '')

class JsonRPCHandler(BaseHTTPServer.BaseHTTPRequestHandler, object):
    def do_GET(self):
        method = self.send_head()
        resp = simplejson.dumps(method())
        self.wfile.write(resp)

    def do_HEAD(self):
        self.send_head()

    def send_head(self):
        self.path = self.path.strip()
        if self.path == "/":
            method = self.root
        else:
            try:
                method = self.__getattribute__(self.path[1:])
            except AttributeError:
                self.send_response(404)
                return

        self.send_response(200)
        self.send_header("Content-type", "application/x-json")
        self.end_headers()

        return method

    def do_POST(self):
        contentLength = int(self.headers['Content-Length'])
        args = simplejson.loads(self.rfile.read(contentLength))

        method = args[0]

        try:
            method = self.__getattribute__(method)
        except AttributeError:
            self.send_response(404)
            return

        self.send_response(200)
        self.send_header("Content-type", "application/x-json")
        self.end_headers()

        resp = simplejson.dumps(method(*args[1]))
        self.wfile.write(resp)


class CopyThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        self.tmpPath = kwargs['tmpPath']
        self.sourcePath = kwargs['sourcePath']
        self.needsMount = kwargs['needsMount']
        del kwargs['tmpPath']
        del kwargs['sourcePath']
        del kwargs['needsMount']

        threading.Thread.__init__(self, *args, **kwargs)
        self.status = {"bytesTotal": 0, "bytesRead": 0, "done": False, "checksumError": False,
            "error": False, "errorMessage": ""}
        self.lastTotal = 0

    def copyCallback(self, total, rate):
        if total - self.lastTotal > 0:
            bytes = total - self.lastTotal
        else:
            bytes = 0
        self.status['bytesRead'] += bytes
        self.lastTotal = total

    def mount(self):
        if self.needsMount:
            os.system("sudo mount /dev/cdrom /mnt")
    
    def umount(self):
        if self.needsMount:
            os.system("sudo umount /mnt")



class ConcatThread(CopyThread):
    def run(self):
        files = [x for x in os.listdir(self.tmpPath)
            if x.startswith("mirror-")
                and "tar" in x
                and not x.endswith('tar')
                and not x.endswith('.sha1')
        ]
        bytesTotal = sum(os.stat(os.path.join(self.tmpPath, x))[stat.ST_SIZE] for x in files)
        self.status['bytesTotal'] = bytesTotal
        print "concatting: ", files, bytesTotal

        baseName = files[0].split(".tar")[0]
        output = file(os.path.join(self.tmpPath, baseName + ".tar"), "w")
        for f in sorted(files):
            input = file(os.path.join(self.tmpPath, f))
            util.copyfileobj(input, output, self.copyCallback)
            input.close()
            self.lastTotal = 0
            os.unlink(os.path.join(self.tmpPath, f))
        output.close()
        self.status['done'] = True


def setupUsers(cfg, serverName, dbPath):
    nscfg = netserver.ServerConfig()
    nscfg.serverName = serverName
    nscfg.repositoryDB = dbPath
    nscfg.contentsDir = " ".join(x % serverName for x in cfg.reposContentsDir)

    repos = netserver.NetworkRepositoryServer(nscfg, '')

    repos.auth.addUser(cfg.authUser, cfg.authPass)
    repos.auth.addAcl(cfg.authUser, None, None, True, False, True)
    repos.auth.setMirror(cfg.authUser, True)

    repos.auth.addUser('anonymous', 'anonymous')
    repos.auth.addAcl('anonymous', None, None, False, False, False)


class TarThread(CopyThread):
    def run(self):
        file = [x for x in os.listdir(self.tmpPath)
            if x.startswith("mirror-") and x.endswith(".tar")][0]

        serverName = file[7:-4]
        cmd = ["tar", "xvf", os.path.join(self.tmpPath, file), "-C", "/srv/rbuilder/repos/%s" % serverName]
        tar = subprocess.Popen(cmd, stdout = subprocess.PIPE)

        lines = 100
        d = tar.stdout.readlines(100)
        while d:
            d = tar.stdout.readlines(100)
            lines += 100
            self.status['bytesRead'] = lines

        # do a few post-mirror config items
        #
        # o Chown the files to apache.apache
        # o Add mintauth and anonymous users
        #
        os.system("chown -R apache.apache /srv/rbuilder/repos/%s/" % serverName)
        from mint import config
        cfg = config.MintConfig()
        cfg.read(config.RBUILDER_CONFIG)
        dbPath = ('sqlite', cfg.reposDBPath % serverName)

        setupUsers(cfg, serverName, dbPath)
        self.status['done'] = True


class CopyFromDiscThread(CopyThread):
    def run(self):
        self.umount()
        self.mount()
        files = os.listdir(self.sourcePath)
        files = [x for x in files if x != 'MIRROR-INFO' and not x.endswith('.sha1') and os.path.isfile(os.path.join(self.sourcePath, x))]

        bytesTotal = sum(os.stat(os.path.join(self.sourcePath, x))[stat.ST_SIZE] for x in files)
        self.status['bytesTotal'] = bytesTotal

        for f in files:
            fromF = file(os.path.join(self.sourcePath, f))
            toF = file(os.path.join(self.tmpPath, f), "w")
            util.copyfileobj(fromF, toF, self.copyCallback)
            toF.close()
            fromF.close()

            try:
                origSha1 = file(os.path.join(self.sourcePath, f) + ".sha1")
                data = origSha1.read()
                origSha1.close()
                origSum = data.split()[0]

                newSum = sha1helper.sha1ToString(sha1helper.sha1FileBin(os.path.join(self.tmpPath, f)))
                if origSum != newSum:
                    self.status['checksumError'] = True
            except IOError, e:
                self.status['checksumError'] = True
                print e
            print "checksumError:", self.status['checksumError']

        self.status['done'] = True
        self.umount()


class TarHandler(JsonRPCHandler):
    def handle_one_request(self):
        global sourcePath, tmpPath, needsMount
        self.sourcePath = sourcePath
        self.tmpPath = tmpPath
        self.needsMount = needsMount
        JsonRPCHandler.handle_one_request(self)

    def copyfiles(self):
        global copyThread
        if copyThread and not copyThread.isAlive():
            copyThread = None

        if not copyThread:
            copyThread = CopyFromDiscThread(
                tmpPath = self.tmpPath,
                sourcePath = self.sourcePath,
                needsMount = self.needsMount)
            copyThread.start()

    def concatfiles(self):
        global copyThread
        if copyThread and not copyThread.isAlive():
            copyThread = None

        if not copyThread:
            copyThread = ConcatThread(
                tmpPath = self.tmpPath,
                sourcePath = self.sourcePath,
                needsMount = self.needsMount)
            copyThread.start()

    def untar(self):
        global copyThread
        if copyThread and not copyThread.isAlive():
            copyThread = None

        if not copyThread:
            copyThread = TarThread(
                tmpPath = self.tmpPath,
                sourcePath = self.sourcePath,
                needsMount = self.needsMount)
            copyThread.start()

    def getDiscInfo(self):
        if self.needsMount:
            os.system("sudo mount /dev/cdrom /mnt")
        try:
            keyFile = open(os.path.join(self.sourcePath, "MIRROR-INFO"))
            serverName = keyFile.readline().strip()
            curDisc, count = keyFile.readline().strip().split("/")
            numFiles = keyFile.readline()

            return {
                "error": False,
                "message": "Success",
                "curDisc": int(curDisc),
                "count": int(count),
                "numFiles": int(numFiles),
                "serverName": serverName
            }
        except IOError, e:
            return {
                "error": True,
                "message": "Error: " + str(e),
                "curDisc": 0,
                "count": 0,
                "numFiles": 0,
                "serverName": ""
            }
        if self.needsMount:
            os.system("sudo umount /mnt")

    def startTar(self):
        global tarThread
        if not tarThread.isAlive():
            tarThread = None

        if not tarThread:
            tarThread = TarThread()
            tarThread.start()

    def tarStatus(self, *args):
        global tarThread
        if tarThread:
            return {'message': tarThread.status}
        else:
            return {'message': "None"}

    def copyStatus(self, *args):
        global copyThread
        if copyThread:
            status = copyThread.status
            if status['done']:
               copyThread = None
            return status
        else:
            return {'bytesTotal': 0, 'bytesRead': 0, 'done': False, 'checksumError': False}
