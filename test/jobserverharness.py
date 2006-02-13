#
# Copyright (c) 2006 rPath, Inc.
# All Rights Reserved
#
import os
import time

from conary.lib import util

from mint_rephelp import MintRepositoryHelper
from mint import cooktypes
from mint import releasetypes
from mint.distro import jobserver


class JobServerHelper(MintRepositoryHelper):
    def writeIsoGenCfg(self):
        cfg = jobserver.IsoGenConfig()

        cfg.serverUrl       = "http://mintauth:mintpass@localhost:%d/xmlrpc-private/" % self.port
        cfg.supportedArch   = ['x86']
        cfg.cookTypes       = [cooktypes.GROUP_BUILDER]
        cfg.imageTypes      = [releasetypes.STUB_IMAGE]
        cfg.logPath         = os.path.join(self.reposDir, "jobserver", "logs")
        cfg.imagesPath      = os.path.join(self.reposDir, "jobserver", "images")
        cfg.finishedPath    = os.path.join(self.reposDir, "jobserver", "finished-images")
        cfg.lockFile        = os.path.join(self.reposDir, "jobserver", "jobserver.pid")

        for x in ["logs", "images", "finished-images"]:
            util.mkdirChain(os.path.join(self.reposDir, "jobserver", x))

        f = open(self.tmpDir + "/iso_gen.conf", "w")
        cfg.display(f)
        f.close()

        return cfg

    def startJobServer(self):
        self.jsCfg = self.writeIsoGenCfg()
        jspid = os.fork()
        if jspid == 0:
            args = ["/usr/bin/python",
                    "../scripts/job-server",
                    "--config=%s" % self.tmpDir + "/iso_gen.conf",]
            os.execv(args[0], args)
            return
        else:
            # wait for a pid file to show up
            lockFile = os.path.join(self.reposDir, "jobserver", "jobserver.pid")
            tries = 0
            pid = -1
            while tries < 10:
                if os.path.exists(lockFile):
                    pid = int(open(lockFile).read())
                    break
                tries += 1
                time.sleep(0.5)
        self.jsPid = jspid

    def stopJobServer(self):
        lockFile = os.path.join(self.reposDir, "jobserver", "jobserver.pid")
        os.system("../scripts/job-server --config=%s -k" % (self.tmpDir + "/iso_gen.conf"))

        os.waitpid(self.jsPid, 0)

    def setUp(self):
        MintRepositoryHelper.setUp(self)
        self.hideOutput()
        try:
            self.startJobServer()
        finally:
            self.showOutput()

    def tearDown(self):
        self.hideOutput()
        try:
            self.stopJobServer()
        finally:
            self.showOutput()
        MintRepositoryHelper.tearDown(self)
