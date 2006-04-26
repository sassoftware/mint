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
import urllib
import BaseHTTPServer
testsuite.setup()

from conary.lib import util

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

        self.primePid = os.fork()
        if not self.primePid:
            fd = os.open(os.devnull, os.W_OK)
            os.dup2(fd, sys.stdout.fileno())
            os.dup2(fd, sys.stderr.fileno())
            os.close(fd)

            mirrorprime.needsMount = False
            mirrorprime.sourcePath = self.sourcePath
            mirrorprime.tmpPath = self.tmpPath

            httpd = BaseHTTPServer.HTTPServer(('', self.primePort), mirrorprime.TarHandler)
            httpd.serve_forever()
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
        f.close()

    def testGetDiscInfo(self):
        self.writeMirrorInfo()
        r = self.fetch('getDiscInfo')
        assert(r[0] == (200, 'OK'))
        assert(r[1]['serverName'] == 'test.rpath.local')
        assert(r[1]['count'] == 2)
        assert(r[1]['curDisc'] == 1)


if __name__ == "__main__":
    testsuite.main()
