#
# Copyright (c) 2006 rPath, Inc.
#

import time

from mint import client
from mint import jobstatus

from nagpy.plugin import NagiosPlugin
from nagpy.util.exceptionHooks import stdout_hook

class CheckJSRB(NagiosPlugin):
    def __init__(self):
        NagiosPlugin.__init__(self)
        self.mc = client.MintClient("http://mintauth:mintpass@%s:%s/xmlrpc-private/" % (self.server, self.port))
        # Time job is allowed to run, in seconds (6 hours)
        self.maxJobTime = 21600

    def getDbStoreConnectStr(self):
        return "%s:%s@%s/%s" % (self.user, self.passwd, self.host, self.db)

    def setupParser(self):
        p = NagiosPlugin.setupParser(self)
        p.add_option('-s', '--servername', dest='server',
                     help='Servername of rBuilder instance')
        p.add_option('-p', '--port', dest='port',
                     help='rBuilder port')
        return p

    def parseArgs(self):
        opts, args = NagiosPlugin.parseArgs(self)
        if not opts.server:
            print "servername not defined"
            self.usage()
        elif not opts.port:
            print "port not defined"
            self.usage()
        self.server = opts.server
        self.port = opts.port
        return opts, args

    @stdout_hook
    def check(self):
        jobs = self.mc.getJobs()
        badJobs = []
        for x in jobs:
            status = x.getStatus()
            if status == jobstatus.RUNNING:
                startTime = x.getTimeStarted()
                currentTime = time.time()
                if currentTime - startTime > self.maxJobTime:
                    badJobs.append(x)
            elif status == jobstatus.ERROR:
                badJobs.append(x)
        return badJobs
