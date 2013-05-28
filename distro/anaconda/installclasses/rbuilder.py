#
# Copyright (c) SAS Institute Inc.
#

import os
import sys
sys.path.insert(0, '/usr/lib/anaconda/installclasses')

from pykickstart.constants import CLEARPART_TYPE_ALL

import parted
from storage import formats
from storage.formats import fs
from storage.partspec import PartSpec

from rpathapp import InstallClass as BaseInstallClass


class BlankFS(fs.FS):
    _type = 'blank'
    partedSystem = parted.fileSystemType['ext2']
formats.register_device_format(BlankFS)


class InstallClass(BaseInstallClass):
    hidden = 0

    id = "rbuilder"
    name = "r_Builder"
    pixmap = "rpath-color-graphic-only.png"
    description = "rBuilder Appliance install type."

    sortPriority = 100
    showLoginChoice = 1

    def setInstallData(self, anaconda):
        BaseInstallClass.setInstallData(self, anaconda)
        anaconda.id.storage.clearPartType = CLEARPART_TYPE_ALL
        anaconda.id.storage.doAutoPart = True

        anaconda.id.rootPassword['password'] = ''
        anaconda.id.rootPassword['isCrypted'] = True

        anaconda.backend.addManifest('jspreload', optional=True)

    def setSteps(self, anaconda):
        BaseInstallClass.setSteps(self, anaconda);
        anaconda.dispatch.skipStep("bootloader", permanent = 1)
        anaconda.dispatch.skipStep("timezone")
        anaconda.dispatch.skipStep("confirminstall")

    def setDefaultPartitioning(self, storage, platform):
        requests = []

        # Create /boot
        requests.append(PartSpec(mountpoint="/boot", fstype="ext4",
            size=200, weight=2000))

        # Create / (grow to half of disk)
        requests.append(PartSpec(mountpoint="/", fstype="ext4",
            size=4096, grow=True, asVol=True))

        # Create a dummy slave (to be deleted on boot, grow to half of disk)
        requests.append(PartSpec(fstype="blank",
            size=4096, grow=True, asVol=True))

        # Create swap -- always 4GiB
        # (minswap, maxswap) = iutil.swapSuggestion()
        requests.append(PartSpec(fstype="swap",
            size=4096, asVol=True))

        storage.autoPartitionRequests = requests

        # Monkeypatch the storage class so the dummy volume will have the
        # correct name.
        origNewLV = storage.__class__.newLV
        def newLV(self, *args, **kwargs):
            if kwargs.get('fmt_type') == 'blank':
                kwargs['name'] = 'slave_dummy'
            return origNewLV(self, *args, **kwargs)
        storage.__class__.newLV = newLV


    def postAction(self, anaconda):
        vgs = anaconda.id.storage.vgs
        if vgs:
            vgName = vgs[0].name
            cfgPath = os.path.join(anaconda.rootPath,
                    'srv/rbuilder/jobmaster/config.d/50_lvm.conf')
            with open(cfgPath, 'w') as f:
                print >> f, "lvmVolumeName", vgName
