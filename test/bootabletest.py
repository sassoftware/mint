#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()
import rephelp

import os
import sys

from mint_rephelp import MintRepositoryHelper
from conary import conarycfg, conaryclient
from conary.deps import deps
from conary.callbacks import UpdateCallback, ChangesetCallback

from mint.distro import bootable_image

class EmptyCallback(UpdateCallback, ChangesetCallback):
    pass

class BootableImageTest(MintRepositoryHelper):
    def setupBootableImage(self, trove):
        client, userId = self.quickMintUser("testuser", "testpass")

        projectId = client.newProject("Test", "testproject", "rpath.local")
        project = client.getProject(projectId)

        release = client.newRelease(projectId, "Test Release")
        release.setTrove(trove.getName(), trove.getVersion().freeze(), trove.getFlavor().freeze())
        job = client.startImageJob(release.id)
        isocfg = self.writeIsoGenCfg()

        bi = bootable_image.BootableImage(client, isocfg, job, release, project)
        bi.conarycfg = self.cfg
        bi.setupConaryClient()

        return bi

    def testStrongKernel(self):
        """Test that the bootable image code pulls in the correct strongly-included kernel"""
        self.addComponent("kernel:runtime", "1.0", flavor = "is: x86")
        self.addComponent("test:runtime", "1.0")

        trove = self.addCollection("group-dist", "1.0",
            [("kernel:runtime", True),
             ("test:runtime", True)], defaultFlavor = "is: x86")

        bi = self.setupBootableImage(trove)
        uJob, kuJob = bi.updateGroupChangeSet(EmptyCallback())

        assert(uJob)
        assert(not kuJob) # kernel update job should be null since we have a strongly-included kernel

    def testWeakKernel(self):
        """Test that the bootable image code pulls in the correct weakly-included kernel"""
        self.addComponent("kernel:runtime", "1.0", flavor = "is: x86")
        self.addCollection("group-core", "1.0",
            [("kernel:runtime", False)], defaultFlavor = "is: x86")

        self.addComponent("test:runtime", "1.0")
        trove = self.addCollection("group-dist", "1.0",
            [("group-core", True),
             ("test:runtime", True)], defaultFlavor = "is: x86")

        bi = self.setupBootableImage(trove)
        uJob, kuJob = bi.updateGroupChangeSet(EmptyCallback())

        assert(uJob)
        assert(kuJob) # kernel update job should be explicitly provided

    def testNoKernel(self):
        self.addComponent("test:runtime", "1.0")

        trove = self.addCollection("group-dist", "1.0",
             [("test:runtime", True)], defaultFlavor = "is: x86")

        bi = self.setupBootableImage(trove)

        self.assertRaises(bootable_image.KernelTroveRequired,
            bi.updateGroupChangeSet, EmptyCallback())


if __name__ == "__main__":
    testsuite.main()
