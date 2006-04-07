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
from mint_rephelp import MINT_PROJECT_DOMAIN
from mint_rephelp import EmptyCallback
from conary import conarycfg, conaryclient
from conary.deps import deps
from conary.lib import util
from conary import versions

from mint.distro import bootable_image

VFS = versions.VersionFromString
Flavor = deps.parseFlavor

class BootableImageTest(MintRepositoryHelper):
    def setupBootableImage(self, trove):
        client, userId = self.quickMintUser("testuser", "testpass")

        projectId = client.newProject("Test", "testproject",
                MINT_PROJECT_DOMAIN)
        project = client.getProject(projectId)

        release = client.newRelease(projectId, "Test Release")
        release.setTrove(trove.getName(), trove.getVersion().freeze(), trove.getFlavor().freeze())
        job = client.startImageJob(release.id)
        isocfg = self.writeIsoGenCfg()

        bi = bootable_image.BootableImage(client, isocfg, job, release, project)
        bi.conarycfg = self.cfg
        bi.setupConaryClient()
        util.mkdirChain(bi.fakeroot + "/tmp", bi.fakeroot + "/root")

        empty = EmptyCallback()
        uJob = bi.updateGroupChangeSet(empty)
        bi.applyUpdate(uJob, empty, 'tag-scripts')

        return bi

    def testStrongKernel(self):
        """Test that the bootable image code pulls in the correct strongly-included kernel"""
        self.addComponent("kernel:runtime", "1.0", flavor = "is: x86")
        self.addComponent("test:runtime", "1.0")

        trove = self.addCollection("group-dist", "1.0",
            [("kernel:runtime", True),
             ("test:runtime", True)], defaultFlavor = "is: x86")

        bi = self.setupBootableImage(trove)
        self.assertRaises(conaryclient.NoNewTrovesError,
            bi.updateKernelChangeSet, EmptyCallback())

    def testWeakKernel(self):
        """Test that the bootable image code pulls in the correct weakly-included kernel"""

        # emulate the usual group-core configuration with two notByDefault kernels:
        # one smp, one not. we want to prefer the !smp flavored kernel.
        SMP = "use:kernel.smp is:x86"
        noSMP = "use:!kernel.smp is:x86"
        self.addComponent("kernel:runtime", "1.0", flavor = noSMP)
        self.addComponent("kernel:runtime", "1.0", flavor = SMP)
        self.addComponent("kernel:configs", "1.0", flavor = noSMP)
        self.addComponent("kernel:configs", "1.0", flavor = SMP)
        self.addComponent("kernel:build-tree", "1.0", flavor = noSMP)
        self.addComponent("kernel:build-tree", "1.0", flavor = SMP)

        trove = self.addCollection("group-core", "1.0",
            [
                ("kernel:runtime", "1.0", noSMP, False),
                ("kernel:configs", "1.0", noSMP, False),
                ("kernel:build-tree", "1.0", noSMP, False),
                ("kernel:runtime", "1.0", SMP, False),
                ("kernel:configs", "1.0", SMP, False),
                ("kernel:build-tree", "1.0", SMP, False),
            ], defaultFlavor = "is:x86",
        )

        self.addComponent("test:runtime", "1.0")
        trove = self.addCollection("group-dist", "1.0",
            [("group-core", "1.0", trove.getFlavor(), True),
             ("test:runtime", True)], defaultFlavor = "is:x86")

        bi = self.setupBootableImage(trove)
        kuJob = bi.updateKernelChangeSet(EmptyCallback())

        # make sure we get !smp flavors of kernel:runtime
        correctSet = set([('kernel:runtime', (None, None), (VFS('/localhost@rpl:linux/1.0-1-1'), Flavor('!kernel.smp is: x86')), True)])
        assert(kuJob.getPrimaryJobs() == correctSet)

    def testNoKernel(self):
        self.addComponent("test:runtime", "1.0")

        trove = self.addCollection("group-dist", "1.0",
             [("test:runtime", True)], defaultFlavor = "is: x86")

        bi = self.setupBootableImage(trove)

        self.assertRaises(bootable_image.KernelTroveRequired,
            bi.updateKernelChangeSet, EmptyCallback())


if __name__ == "__main__":
    testsuite.main()
