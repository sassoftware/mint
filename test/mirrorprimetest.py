#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#
import os
import sys
import httplib
import testsuite
import tempfile
import unittest
import signal
import simplejson
import socket
import stat
import urllib
import time
import BaseHTTPServer
testsuite.setup()

from conary.lib import util, coveragehook

from mint_rephelp import MintRepositoryHelper
from mint import server
from mint import users
from mint import shimclient
from mint import mirrorprime

class MirrorPrimeTest(unittest.TestCase):
    def setUp(self):
        self.primePort = testsuite.findPorts()[0]
        self.topLevel = tempfile.mkdtemp()
        self.tmpPath = self.topLevel + "/tmp"
        self.sourcePath = self.topLevel + "/src"
        util.mkdirChain(self.tmpPath)
        util.mkdirChain(self.sourcePath)

        # find archiveDir
        for dir in sys.path:
            thisdir = os.path.normpath(os.sep.join((dir, 'archive')))
            if os.path.isdir(thisdir):
                self.archiveDir = thisdir
                break

        self.primePid = os.fork()
        if not self.primePid:
            coveragehook.install()
            fd = os.open(os.devnull, os.W_OK)
            os.dup2(fd, sys.stdout.fileno())
            os.dup2(fd, sys.stderr.fileno())
            os.close(fd)

            mirrorprime.needsMount = False
            mirrorprime.sourcePath = self.sourcePath
            mirrorprime.tmpPath = self.tmpPath
            mirrorprime.targetPath = self.tmpPath

            httpd = BaseHTTPServer.HTTPServer(('', self.primePort), mirrorprime.TarHandler)

            while 1:
                httpd.handle_request()
                coveragehook.save()

        ready = False
        tries = 0
        while tries < 100:
            try:
                self.fetch("copyStatus")
            except socket.error:
                tries += 1
                time.sleep(0.1)
            else:
                break

        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        os.kill(self.primePid, signal.SIGTERM)
        os.waitpid(self.primePid, 0)
        util.rmtree(self.topLevel)

    def fetch(self, method, *args):
        params = simplejson.dumps([method, args])
        headers = {"Content-type": "application/x-json",
                   "Accept": "application/x-json"}
        conn = httplib.HTTPConnection("localhost", self.primePort)
        conn.request("POST", "/", params, headers)
        response = conn.getresponse()

        return (response.status, response.reason), simplejson.loads(response.read())

    def writeMirrorInfo(self, count = 2, curDisc = 1, serverName = "test.rpath.local"):
        f = file(self.sourcePath + "/MIRROR-INFO", "w")
        print >> f, serverName
        print >> f, "%d/%d" % (curDisc, count)
        print >> f, "123"
        f.close()

    def writeMirrorFiles(self, dest, count = 2, sums = True):
        for x in range(count):
            f = file(dest + "/mirror-test.rpath.local.tar%03d" % x, "w")
            f.write("Hello World\n")
            f.close()

            if sums:
                f = file(dest + "//mirror-test.rpath.local.tar%03d.sha1" % x, "w")
                f.write("648a6a6ffffdaa0badb23b8baf90b6168dd16b3a  helloworld")
                f.close()

    def testGetDiscInfo(self):
        self.writeMirrorInfo()
        r = self.fetch('getDiscInfo')
        assert(r[0] == (200, 'OK'))
        assert(r[1]['serverName'] == 'test.rpath.local')
        assert(r[1]['count'] == 2)
        assert(r[1]['curDisc'] == 1)
        assert(r[1]['numFiles'] == 123)

    def testCopy(self):
        self.writeMirrorInfo()
        self.writeMirrorFiles(dest = self.sourcePath)
        r = self.fetch('copyfiles')
        assert(r[0] == (200, 'OK'))

        done = False
        tries = 0
        while not done and tries < 10:
            r = self.fetch('copyStatus')
            done = r[1]['done']
            time.sleep(0.5)
            tries += 1
        self.failIf(not done, "copy never completed")

        assert(os.path.isfile(os.path.join(self.tmpPath, "mirror-test.rpath.local.tar000")))
        assert(os.path.isfile(os.path.join(self.tmpPath, "mirror-test.rpath.local.tar001")))
        assert(not r[1]['checksumError'])

    def testCopyBadChecksum(self):
        self.writeMirrorInfo()
        self.writeMirrorFiles(dest = self.sourcePath, count = 1, sums = False)
        r = self.fetch('copyfiles')
        assert(r[0] == (200, 'OK'))

        done = False
        tries = 0
        while not done and tries < 10:
            r = self.fetch('copyStatus')
            done = r[1]['done']
            time.sleep(0.5)
            tries += 1
        self.failIf(not done, "copy never completed")

        assert(r[1]['checksumError'])

    def testConcat(self):
        self.writeMirrorFiles(dest = self.tmpPath)

        r = self.fetch('concatfiles')
        assert(r[0] == (200, 'OK'))

        done = False
        tries = 0
        while not done and tries < 10:
            r = self.fetch('copyStatus')
            done = r[1]['done']
            time.sleep(0.5)
            tries += 1

        assert(os.stat(os.path.join(self.tmpPath, "mirror-test.rpath.local.tar"))[stat.ST_SIZE] == 24)

    def testUntar(self):
        util.copyfile(self.archiveDir + "/mirror-test.tar", self.tmpPath)
        r = self.fetch('untar')

        done = False
        tries = 0
        while not done and tries < 10:
            r = self.fetch('copyStatus')
            done = r[1]['done']
            time.sleep(0.5)
            tries += 1
 
        assert(os.path.exists(self.tmpPath + "/repos/test/Makefile"))
        assert(not os.path.exists(self.tmpPath + "/mirror-test.tar"))

if __name__ == "__main__":
    testsuite.main()
