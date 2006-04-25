#!/usr/bin/python
import BaseHTTPServer
import simplejson
import threading
import os
import stat

from conary.lib import util


# this global hack is to bypass the the inherent stateless nature of http.
tarThread = None
copyThread = None


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

        print args[1]
        resp = simplejson.dumps(method(*args[1]))
        print "returning",  resp
        self.wfile.write(resp)

class CopyThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.status = {"bytesTotal": 0, "bytesRead": 0, "done": False}
        self.lastTotal = 0

    def copyCallback(self, total, rate):
        bytes = total - self.lastTotal
        self.status['bytesRead'] += bytes
        self.lastTotal = total


class ConcatThread(CopyThread):
    def run(self):
        files = [x for x in os.listdir("/tmp/") if x.startswith("mirror-") and "tgz" in x and not x.endswith('tgz')]
        bytesTotal = sum(os.stat(os.path.join("/tmp", x))[stat.ST_SIZE] for x in files)
        self.status['bytesTotal'] = bytesTotal
        print "concatting: ", files, bytesTotal

        baseName = files[0].split(".tgz")[0]
        output = file("/tmp/" + baseName + ".tgz", "w")
        for f in files:
            input = file("/tmp/" + f)
            util.copyfileobj(input, output, self.copyCallback)
            input.close()
            self.lastTotal = 0
        output.close()
        self.status['done'] = True


class CopyFromDiscThread(CopyThread):
    def run(self):
        files = os.listdir("/mnt/")
        files = [x for x in files if x != 'MIRROR-INFO' and os.path.isfile("/mnt/" + x)]
        print "files", files

        bytesTotal = sum(os.stat(os.path.join("/mnt", x))[stat.ST_SIZE] for x in files)
        self.status['bytesTotal'] = bytesTotal

        for f in files:
            fromF = file("/mnt/" + f)
            toF = file("/tmp/" + f, "w")
            util.copyfileobj(fromF, toF, self.copyCallback)
            toF.close()
            fromF.close()

        self.status['done'] = True


class TarHandler(JsonRPCHandler):
    def copyfiles(self):
        global copyThread
        if copyThread and not copyThread.isAlive():
            copyThread = None

        if not copyThread:
            copyThread = CopyFromDiscThread()
            copyThread.start()

    def concatfiles(self):
        global copyThread
        if copyThread and not copyThread.isAlive():
            copyThread = None

        if not copyThread:
            copyThread = ConcatThread()
            copyThread.start()

    def getDiscInfo(self):
#        os.system("sudo mount /cdrom")
        try:
            keyFile = open("/mnt/MIRROR-INFO")
            serverName = keyFile.readline().strip()
            curDisc, count = keyFile.readline().strip().split("/")

            return {
                "error": False,
                "message": "Success",
                "curDisc": int(curDisc),
                "count": int(count),
                "serverName": serverName
            }
        except IOError, e:
            return {
                "error": True,
                "message": "Error: " + str(e),
                "curDisc": 0,
                "count": 0,
                "serverName": ""
            }
#        os.system("sudo umount /cdrom")

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
            return {'bytesTotal': 0, 'bytesRead': 0, 'done': False}
