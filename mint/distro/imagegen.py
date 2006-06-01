#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

import os
import sys
from threading import currentThread

from mint import jobstatus


MSG_INTERVAL = 5

class NoConfigFile(Exception):
    def __init__(self, path = ""):
        self._path = path

    def __str__(self):
        import epdb
        epdb.st()
        return "Unable to access configuration file: %s" % self._path

class Generator:
    configObject = None

    def __init__(self, client, cfg, job):
        self.client = client
        self.cfg = cfg
        self.job = job

    def getConfig(self):
        assert(self.configObject)
        imageCfg = self.configObject()

        cfgFile = os.path.join(self.cfg.configPath, imageCfg.filename)
        if os.access(cfgFile, os.R_OK):
            imageCfg.read(cfgFile)
        else:
            raise NoConfigFile(cfgFile)
        return imageCfg

    def readConaryRc(self, cfg):
        conarycfgFile = os.path.join(self.cfg.configPath, 'config', 'conaryrc')
        if os.path.exists(conarycfgFile):
            cfg.read(conarycfgFile)
        return conarycfgFile

    def write(self):
        raise NotImplementedError

    def status(self, msg):
        self.job.setStatus(jobstatus.RUNNING, msg)

    def grabOutput(self, logFile):
        """Redirect stdout and stderr to a file"""
        self.logfd = os.open(logFile, os.O_TRUNC | os.O_WRONLY | os.O_CREAT)
        sys.stdout.flush()
        sys.stderr.flush()

        self.stdout = os.dup(sys.stdout.fileno())
        self.stderr = os.dup(sys.stderr.fileno())
        os.dup2(self.logfd, sys.stdout.fileno())
        os.dup2(self.logfd, sys.stderr.fileno())

    def releaseOutput(self):
        """Restore stdout and stderr to the original state before grabOutput"""
        sys.stdout.flush()
        sys.stderr.flush()

        os.dup2(self.stdout, sys.stdout.fileno())
        os.dup2(self.stderr, sys.stderr.fileno())
        os.close(self.stdout)
        os.close(self.stderr)

        os.close(self.logfd)


class ImageGenerator(Generator):
    def __init__(self, client, cfg, job, release, project):
        Generator.__init__(self, client, cfg, job)
        self.release = release
        self.project = project

    def _getLabelPath(self, cclient, trove):
        repos = cclient.getRepos()
        trv = repos.getTroves([trove])
        return " ".join(trv[0].getTroveInfo().labelPath)

    def writeConaryRc(self, tmpPath, cclient):
        # write the conaryrc file
        conaryrcFile = open(os.path.join(tmpPath, "conaryrc"), "w")
        ilp = self.release.getDataValue("installLabelPath")
        if not ilp: # allow a ReleaseData ILP to override the group label path
            ilp = self._getLabelPath(cclient, (self.release.getTroveName(),
                                               self.release.getTroveVersion(),
                                               self.release.getTroveFlavor()))
        if not ilp: # fall back to a reasonable default if group trove was
                    # cooked before conary0.90 and releasedata is blank
            ilp = self.project.getLabel() + " conary.rpath.com@rpl:1 contrib.rpath.com@rpl:devel"

        print >> conaryrcFile, "installLabelPath " + ilp
        print >> conaryrcFile, "pinTroves kernel.*"
        print >> conaryrcFile, "includeConfigFile /etc/conary/config.d/*"
        if self.release.getDataValue("autoResolve"):
            print >> conaryrcFile, "autoResolve True"
        conaryrcFile.close()
