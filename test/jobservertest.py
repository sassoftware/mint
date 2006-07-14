#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import os
import testsuite
import time
testsuite.setup()

import jobserverharness

from mint import buildtypes
from mint import constants
from mint.distro import jsversion

from conary.lib import util

class JobServerTest(jobserverharness.JobServerHelper):
    def testJobServer(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")
        project = client.getProject(projectId)

        build = client.newBuild(projectId, "Test Build")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setDataValue('stringArg', 'Hello World!')

        build.setTrove("group-trove",
            "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")

        job = client.startImageJob(build.getId())

        tries = 0
        while True:
            if os.path.exists(self.jsCfg.finishedPath + "/stub.iso"):
                break
            if tries > 30:
                self.fail("stub.iso never appeared")
            tries += 1
            time.sleep(1)

        contents = open(self.jsCfg.finishedPath + "/stub.iso").read()
        assert(contents == "Hello World!\n")
        assert(job.getDataValue("hostname") == "127.0.0.1")


if __name__ == "__main__":
    testsuite.main()
