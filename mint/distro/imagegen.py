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


class ImageGenerator(Generator):
    def __init__(self, client, cfg, job, build, project):
        Generator.__init__(self, client, cfg, job)
        self.build = build
        self.project = project

    def _getLabelPath(self, cclient, trove):
        repos = cclient.getRepos()
        trv = repos.getTroves([trove])
        return " ".join(trv[0].getTroveInfo().labelPath)

    def writeConaryRc(self, tmpPath, cclient):
        # write the conaryrc file
        conaryrcFile = open(os.path.join(tmpPath, "conaryrc"), "w")
        ilp = self.build.getDataValue("installLabelPath")
        if not ilp: # allow a BuildData ILP to override the group label path
            ilp = self._getLabelPath(cclient, (self.build.getTroveName(),
                                               self.build.getTroveVersion(),
                                               self.build.getTroveFlavor()))
        if not ilp: # fall back to a reasonable default if group trove was
                    # cooked before conary0.90 and builddata is blank
            ilp = self.project.getLabel() + " conary.rpath.com@rpl:1 contrib.rpath.com@rpl:devel"

        print >> conaryrcFile, "installLabelPath " + ilp
        print >> conaryrcFile, "pinTroves kernel.*"
        print >> conaryrcFile, "includeConfigFile /etc/conary/config.d/*"
        if self.build.getDataValue("autoResolve"):
            print >> conaryrcFile, "autoResolve True"
        conaryrcFile.close()
