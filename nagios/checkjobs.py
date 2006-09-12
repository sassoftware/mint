#
# Copyright (c) 2006 rPath, Inc.
#

import time
import re

from mint import client
from mint import jobstatus

from nagpy.plugin import NagiosPlugin
from nagpy.util.exceptionHooks import stdout_hook

from mint_nagpy.config import CheckJobsConfig
from conary.lib import cfgtypes

class CheckJobs(NagiosPlugin):
    def __init__(self):
        NagiosPlugin.__init__(self)
        self.mc = client.MintClient("http://mintauth:mintpass@%s:%s/xmlrpc-private/" % (self.host, self.port))
        self.cfg = CheckJobsConfig()
        try:
            self.cfg.read('/srv/rbuilder/nagios/check.cfg')
        except cfgtypes.CfgEnvironmentError:
            pass

    def getTimeStamp(self):
        try:
            f = open(self.cfg.timeStampFile)
        except IOError:
            stamp = 0
        else:
            stamp = float(f.read())
            f.close()
        return stamp

    def itterate(self, reset=False):
        try:
            f = open(self.cfg.iterationFile)
        except IOError:
            dat = 1
        else:
            dat = int(f.read())
            f.close()
        f = open(self.cfg.iterationFile, 'w')
        if dat < self.cfg.retries and not reset:
            f.write(str(dat+1))
        else:
            f.write('1')
        f.close()
        return dat == self.cfg.retries and True or False

    def setTimeStamp(self, newTimeStamp):
        f = open(self.cfg.timeStampFile, 'w')
        f.write(str(newTimeStamp))
        f.close()
            
    def filterJobErrors(self, message):
        for e in self.cfg.filterExp:
            if re.search(e, message):
                return True
        return False

    def setupParser(self):
        p = NagiosPlugin.setupParser(self)
        p.add_option('-p', '--port', dest='port',
                     help='rBuilder port')
        return p

    def parseArgs(self):
        opts, args = NagiosPlugin.parseArgs(self)
        if not opts.host:
            print "hostname not defined"
            self.usage()
        elif not opts.port:
            print "port not defined"
            self.usage()
        self.host = opts.host
        self.port = opts.port
        return opts, args

    @stdout_hook
    def check(self):
        newTimeStamp = time.time()
        timeStamp = self.getTimeStamp()
        jobs = self.mc.getJobs()
        badJobs = []
        for x in jobs:
            status = x.getStatus()
            if status == jobstatus.RUNNING:
                startTime = x.getTimeStarted()
                currentTime = time.time()
                if currentTime - startTime > self.cfg.maxJobTime:
                    badJobs.append(x.getId())
            elif status == jobstatus.ERROR:
                if x.getTimeStarted() > timeStamp:
                    if not self.filterJobErrors(x.getStatusMessage()):
                        badJobs.append(x.getId())
        if badJobs:
            if self.itterate():
                self.setTimeStamp(newTimeStamp)
        else:
            self.itterate(reset=True)
        return badJobs, timeStamp
