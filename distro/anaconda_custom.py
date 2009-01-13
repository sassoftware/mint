#
# Copyright (c) 2007-2009 rPath, Inc.
# All rights reserved
#

import os
import sys
sys.path.insert(0, '/usr/lib/anaconda/installclasses')

from pykickstart.constants import CLEARPART_TYPE_ALL
from rhpl.translate import N_

import bootloader
import iutil
import partRequests
import parted
from fsset import FileSystemType, fileSystemTypeGet, fileSystemTypeGetDefault, fileSystemTypeRegister
from constants import BL_EXTLINUX
from rpathapp import InstallClass as BaseInstallClass


class blankFileSystem(FileSystemType):
    def __init__(self):
        FileSystemType.__init__(self)
        self.partedFileSystemType = parted.file_system_type_get("ext2")
        self.formattable = 1
        self.checked = 0
        self.linuxnativefs = 0
        self.name = "blank"
        self.supported = 0
        self.maxSizeMB = 8 * 1024 * 1024
        self.packages = []

    def formatDevice(self, entry, progress, chroot='/'):
        pass

fileSystemTypeRegister(blankFileSystem())

class InstallClass(BaseInstallClass):
    hidden = 0

    id = "rbuilder"
    name = N_("r_Builder")
    pixmap = "rpath-color-graphic-only.png"
    description = N_("rBuilder Appliance install type.")

    sortPriority = 100
    showLoginChoice = 1

    def setSteps(self, anaconda):
        BaseInstallClass.setSteps(self, anaconda);
        anaconda.dispatch.skipStep("authentication")
        anaconda.dispatch.skipStep("bootloader", permanent = 1)
        anaconda.dispatch.skipStep("package-selection")
        anaconda.dispatch.skipStep("firewall")
        anaconda.dispatch.skipStep("confirminstall")


    def setDefaultPartitioning(self, partitions, clear = CLEARPART_TYPE_ALL,
                               doClear = 1):

        partitions.autoClearPartDrives = None

        requests = []

        # Create /boot
        requests.append(partRequests.PartitionSpec(
            fstype=fileSystemTypeGet('ext2'), size=100, mountpoint='/boot',
            primary=1, format=1))

        # Create PVs
        requests.append(partRequests.PartitionSpec(
            fstype=fileSystemTypeGet('physical volume (LVM)'),
            size=4096, grow=1, format=1, multidrive=1))

        # Create the VG
        requests.append(partRequests.VolumeGroupRequestSpec(vgname='vg00',
            fstype=fileSystemTypeGet('volume group (LVM)'), physvols=[], format=1))

        # Create / (grow to half of disk)
        requests.append(partRequests.LogicalVolumeRequestSpec(lvname='root',
            fstype=fileSystemTypeGetDefault(), mountpoint='/', size=4096,
            grow=1, format=1, volgroup='vg00'))

        # Create a dummy slave (to be deleted on boot, grow to half of disk)
        requests.append(partRequests.LogicalVolumeRequestSpec(
            fstype=fileSystemTypeGet('blank'), size=4096, lvname='slave_dummy',
            grow=1, volgroup='vg00'))

        # Create /var/log - 4GiB
        requests.append(partRequests.LogicalVolumeRequestSpec(lvname='logs',
            fstype=fileSystemTypeGetDefault(), mountpoint='/var/log', 
            size=4096, format=1, volgroup='vg00'))

        # Create swap
        (minswap, maxswap) = iutil.swapSuggestion()
        requests.append(partRequests.LogicalVolumeRequestSpec(lvname='swap',
            fstype=fileSystemTypeGet('swap'), size=minswap, maxSizeMB=maxswap,
            grow=1, format=1, volgroup='vg00'))

        partitions.autoPartitionRequests = requests

    def setInstallData(self, anaconda):
        BaseInstallClass.setInstallData(self, anaconda)
        anaconda.id.partitions.autoClearPartType = CLEARPART_TYPE_ALL
        anaconda.id.bootloader.setBootLoader(BL_EXTLINUX)

    def postAction(self, anaconda, serial):
        # assume that half of total mem is at least 2G
        totalMem = iutil.memInstalled() / 1024 # in MB
        dom0mem = max(int(totalMem / 2), 2048) # in MB

        fObj = open(os.path.join(anaconda.rootPath, 'etc/bootloader.d/dom0-mem.conf'), 'w')
        print >> fObj, 'add_xen_options dom0_mem=%dM' % dom0mem
        fObj.close()

        iutil.execWithRedirect('/sbin/bootman', [], root=anaconda.rootPath)

        BaseInstallClass.postAction(self, anaconda, serial)
