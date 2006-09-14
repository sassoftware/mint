#
# Copyright (c) 2006 rPath, Inc.
#

import time
import re

from mint import jobstatus
from mint.config import MintConfig

from nagpy.plugin import NagiosPlugin
from nagpy.util.exceptionHooks import stdout_hook

from mint_nagpy.config import CheckJobsConfig
from conary.lib import cfgtypes
from conary import dbstore

class CheckJobs(NagiosPlugin):
    def __init__(self):
        NagiosPlugin.__init__(self)
        self.cfg = CheckJobsConfig()
        try:
            self.cfg.read('/srv/rbuilder/nagios/check.cfg')
        except cfgtypes.CfgEnvironmentError:
            pass
        self.mintConfigPath = '/srv/rbuilder/rbuilder.conf'

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

    @stdout_hook
    def check(self):
        newTimeStamp = time.time()
        timeStamp = self.getTimeStamp()
        cfg = MintConfig()
        cfg.read(self.mintConfigPath)
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        cu = db.cursor()
        cu.execute("""SELECT jobId, status, statusMessage, timeStarted
                      FROM jobs""")
        jobs = cu.fetchall_dict()
        badJobs = []
        for x in jobs:
            if x['status'] == jobstatus.RUNNING:
                currentTime = time.time()
                if currentTime - x['timeStarted'] > self.cfg.maxJobTime:
                    badJobs.append(x['jobId'])
            elif x['status'] == jobstatus.ERROR:
                if x['timeStarted'] > timeStamp:
                    if not self.filterJobErrors(x['statusMessage']):
                        badJobs.append(x['jobId'])
        if badJobs:
            if self.itterate():
                self.setTimeStamp(newTimeStamp)
        else:
            self.itterate(reset=True)
        return badJobs, timeStamp
