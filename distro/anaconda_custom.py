#
# Copyright (c) 2007-2009 rPath, Inc.
# All rights reserved
#

import sys
sys.path.insert(0, '/usr/lib/anaconda/installclasses')

from pykickstart.constants import CLEARPART_TYPE_ALL
from rhpl.translate import N_

import parted
import partRequests
from fsset import FileSystemType
from fsset import fileSystemTypeGet
from fsset import fileSystemTypeGetDefault
from fsset import fileSystemTypeRegister

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

    in_advanced_mode = False

    def setInstallData(self, anaconda):
        BaseInstallClass.setInstallData(self, anaconda)
        anaconda.id.partitions.autoClearPartType = CLEARPART_TYPE_ALL
        anaconda.id.bootloader.setBootLoader(BL_EXTLINUX)

        anaconda.id.rootPassword['password'] = ''
        anaconda.id.rootPassword['isCrypted'] = True

        anaconda.backend.addManifest('jspreload', optional=True)

    def setSteps(self, anaconda):
        BaseInstallClass.setSteps(self, anaconda);
        anaconda.dispatch.skipStep("authentication")
        anaconda.dispatch.skipStep("bootloader", permanent = 1)
        anaconda.dispatch.skipStep("package-selection")
        anaconda.dispatch.skipStep("firewall")
        anaconda.dispatch.skipStep("confirminstall")
        self.set_advanced(False, anaconda)

    def set_advanced(self, enabled, anaconda):
        self.in_advanced_mode = enabled
        anaconda.dispatch.skipStep('parttype', skip=not enabled)
        anaconda.dispatch.skipStep('partition', skip=not enabled)
        anaconda.dispatch.skipStep('network', skip=not enabled)
        anaconda.dispatch.skipStep('timezone', skip=not enabled)
        anaconda.dispatch.skipStep('accounts', skip=not enabled)
        anaconda.dispatch.skipStep('complete', skip=not enabled)

    def setDefaultPartitioning(self, partitions, clear = CLEARPART_TYPE_ALL,
                               doClear = 1):

        partitions.autoClearPartDrives = None

        requests = []

        # Create /boot
        requests.append(partRequests.PartitionSpec(
            fstype=fileSystemTypeGet('ext3'), size=100, mountpoint='/boot',
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

        # Create swap -- always 4GiB
        # (minswap, maxswap) = iutil.swapSuggestion()
        requests.append(partRequests.LogicalVolumeRequestSpec(lvname='swap',
            fstype=fileSystemTypeGet('swap'), size=4096, 
            grow=0, format=1, volgroup='vg00'))

        partitions.autoPartitionRequests = requests

    def postAction(self, anaconda, serial):
        # If in advanced mode the user had the opportunity to configure
        # networking already.
        if not self.in_advanced_mode:
            self.enable_network(anaconda)

        BaseInstallClass.postAction(self, anaconda, serial)

    def enable_network(self, anaconda):
        network = anaconda.id.network
        devices = network.netdevices

        # Iterate over available devs to find if any have already been
        # configured, possibly through kickstart.
        for dev in devices.itervalues():
            if dev.get('onboot').lower() == 'yes' and dev.get('bootproto'):
                # Someone has configured a device, don't mess with the
                # network config.
                return

        # Configure the first device for dhcp and onboot.
        firstDev = network.getFirstDeviceName()
        dev = devices[firstDev]
        dev.set(('onboot', 'yes'))
        dev.set(('bootproto', 'dhcp'))

        # Write out final config.
        network.write(anaconda.rootPath)
