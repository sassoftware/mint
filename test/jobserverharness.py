#
# Copyright (c) 2006 rPath, Inc.
# All Rights Reserved
#
import os
import time

from conary.lib import util

from mint import cooktypes
from mint import producttypes
from mint.distro import jobserver

from mint_rephelp import MintRepositoryHelper

class JobServerHelper(MintRepositoryHelper):
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
                    try:
                        pid = int(open(lockFile).read())
                    except ValueError:
                        self.fail("pid file belongs to another job server?")
                    break
                tries += 1
                time.sleep(0.5)
        self.jsPid = jspid

    def stopJobServer(self):
        lockFile = os.path.join(self.reposDir, "jobserver", "jobserver.pid")
        os.system("../scripts/job-server --config=%s -k" % (self.tmpDir + "/iso_gen.conf"))

        os.waitpid(self.jsPid, 0)
        # wait for a pid file to disappear
        lockFile = os.path.join(self.reposDir, "jobserver", "jobserver.pid")
        tries = 0
        success = False
        # it can take up to 15 seconds, so this needs to be generous.
        while tries < 30:
            if not os.path.exists(lockFile):
                success = True
                break
            tries += 1
            time.sleep(1)
        if not success:
            self.fail("Job server didn't shut down.")

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
