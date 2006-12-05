#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

import os
import sys
import stat
import tempfile

import rephelp
from mint_rephelp import EmptyCallback
from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_PROJECT_DOMAIN

from mint.distro import bootable_image
from mint.distro import raw_fs_image, raw_hd_image
from mint.distro import live_iso, vmware_image
from mint import data

from conary import conarycfg, conaryclient
from conary import versions
from conary.deps import deps
from conary.lib import util

VFS = versions.VersionFromString
Flavor = deps.parseFlavor

class BootableImageTest(MintRepositoryHelper):
    def setupBootableImage(self, trove = None, subclass = bootable_image.BootableImage):
        if not trove:
            self.addComponent("test:runtime", "1.0", "is: x86")
            trove = self.addCollection("group-dist", "1.0",
                 [("test:runtime", True)], defaultFlavor = "is: x86")

        client, userId = self.quickMintUser("testuser", "testpass")

        projectId = client.newProject("Test", "testproject",
                MINT_PROJECT_DOMAIN)
        project = client.getProject(projectId)

        build = client.newBuild(projectId, "Test Build")
        build.setTrove(trove.getName(), trove.getVersion().freeze(), trove.getFlavor().freeze())
        build.setDataValue("installLabelPath", "conary.rpath.com@rpl:1",
            dataType = data.RDT_STRING, validate = False)
        build.setDataValue("autoResolve", False,
            dataType = data.RDT_BOOL, validate = False)
        build.setDataValue("freespace", 512, dataType = data.RDT_INT,
            validate = False)
        build.setDataValue("swapSize", 0, dataType = data.RDT_INT,
            validate = False)
        build.setDataValue('baseFileName', '', dataType = data.RDT_STRING,
                           validate = False)
        build.setDataValue('mirrorUrl', 'http://test.rpath.mirror/conaryrc/',
                            dataType = data.RDT_STRING, validate = False)
        build.setDataValue('diskAdapter', 'lsilogic',
                           dataType = data.RDT_STRING, validate = False)

        build.setDataValue('vmSnapshots', False, dataType = data.RDT_BOOL,
                           validate = False)

        job = client.startImageJob(build.id)
        isocfg = self.writeIsoGenCfg()

        bi = subclass(client, isocfg, job, build, project)
        bi.conarycfg = self.cfg

        bi.imgcfg.dataDir = os.path.normpath("../scripts/DiskImageData/")
        bi.setupConaryClient()
        util.mkdirChain(bi.fakeroot + "/tmp", bi.fakeroot + "/root")

        empty = EmptyCallback()
        uJob = bi.updateGroupChangeSet(empty)
        bi.applyUpdate(uJob, empty, 'tag-scripts')

        return bi

    def testStrongKernel(self):
        """Test that the bootable image code pulls in the correct strongly-included kernel"""
        self.addComponent("kernel:runtime", "1.0", flavor = "is: x86")
        self.addComponent("test:runtime", "1.0", "is: x86", filePrimer = 1)

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

        self.addComponent("test:runtime", "1.0", "is: x86", filePrimer = 1)
        trove = self.addCollection("group-dist", "1.0",
            [("group-core", "1.0", trove.getFlavor(), True),
             ("test:runtime", True)], defaultFlavor = "is:x86")

        bi = self.setupBootableImage(trove)
        kuJob = bi.updateKernelChangeSet(EmptyCallback())

        # make sure we get !smp flavors of kernel:runtime
        correctSet = set([('kernel:runtime', (None, None), (VFS('/localhost@rpl:linux/1.0-1-1'), Flavor('!kernel.smp is: x86')), True)])
        assert(kuJob.getPrimaryJobs() == correctSet)

    def testNoKernel(self):
        bi = self.setupBootableImage()

        self.assertRaises(bootable_image.KernelTroveRequired,
            bi.updateKernelChangeSet, EmptyCallback())

    def testGrubSetup(self):
        bi = self.setupBootableImage()
        for d in 'sbin', 'boot/grub', 'etc':
            util.mkdirChain(os.path.join(bi.fakeroot, d))
        file(os.path.join(bi.fakeroot, 'sbin', 'grub'), "w").close()

        bi._setupGrub()
        self.verifyContentsInFile(
            os.path.join(bi.fakeroot, 'etc', 'grub.conf'),
            "Test Build (1.0) (template)"
        )

    def testPrepareDiskImage(self):
        bi = self.setupBootableImage()
        _, bi.outfile = tempfile.mkstemp()
        bi.imagesize = 1024 * 1024 * 2

        try:
            bi.prepareDiskImage()
            assert(os.stat(bi.outfile)[stat.ST_SIZE] == bi.imagesize)
        finally:
            os.unlink(bi.outfile)

    def testFindFile(self):
        self.hideOutput()
        try:
            bi = self.setupBootableImage()
            x = bi.findFile(".", "httpd.conf.in")
        finally:
            self.showOutput()
        assert(x == "./server/httpd.conf.in")

    def testFileSystemOddsNEnds(self):
        bi = self.setupBootableImage()
        bi.swapSize = 1024 * 1024
        bi.createTemporaryRoot()

        self.captureAllOutput(bi.fileSystemOddsNEnds)

        assert(os.stat(os.path.join(bi.fakeroot, "var", "swap"))[stat.ST_SIZE] == 1024 * 1024)

        for x in ['/etc/conaryrc', '/etc/fstab',
                  '/var/lib/conarydb/conarydb',
                  '/etc/sysconfig/appliance-name']:
            self.failUnless(os.path.exists(bi.fakeroot + x))

    def testSparse(self):
        bi = self.setupBootableImage()

        f = self.captureAllOutput(bi.createSparseFile, 5)
        try:
            s = self.captureAllOutput(bi.copySparse, f, f + "out")

            assert(s == 0)
        finally:
            os.unlink(f)
            os.unlink(f + "out")

        fd, fn = tempfile.mkstemp()
        try:
            f = os.fdopen(fd, "w")
            f.write('1' * 1024 * 1024 * 5)
            f.close()

            os.system("gzip %s" % fn)
            s = bi.copySparse(fn + ".gz", fn + ".gz.out")

            assert(s == 5133) # happens to be the compressed size of 5M of '1's
        finally:
            os.unlink(fn + ".gz")
            os.unlink(fn + ".gz.out")

    def testRawHdImageClass(self):
        bi = self.setupBootableImage(subclass = raw_hd_image.RawHdImage)
        assert(bi.makeBootable)

    def testRawFsImageClass(self):
        bi = self.setupBootableImage(subclass = raw_fs_image.RawFsImage)
        assert(not bi.makeBootable)

    def testVMwareImageClass(self):
        bi = self.setupBootableImage(subclass = vmware_image.VMwareImage)
        assert(bi.makeBootable)

    def testVMwareESXImageClass(self):
        bi = self.setupBootableImage(subclass = vmware_image.VMwareESXImage)
        assert(bi.makeBootable)

    def testLiveIsoClass(self):
        bi = self.setupBootableImage(subclass = live_iso.LiveIso)
        assert(not bi.makeBootable)

    def testUmlKernelCheck(self):
        bi = self.setupBootableImage()
        bi.outfile = '/dev/null'
        bi.imgcfg.umlKernel = {'x86': '/does_not_exist'}
        self.assertRaises(RuntimeError, bi.runTagScripts)


if __name__ == "__main__":
    testsuite.main()
