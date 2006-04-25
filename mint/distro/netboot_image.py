#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

# python standard library imports
import os, sys
import re
import subprocess
import tempfile

# mint imports
from mint.distro import bootable_image
from mint.distro import gencslist

from conary.lib import util
from mint import releasetypes


class NetbootImage(bootable_image.BootableImage):
    fileType = releasetypes.typeNames[releasetypes.NETBOOT_IMAGE]

    def write(self):
        try:
            # instantiate the contents that need to go into the image
            self.createFileTree()
            kernel = self.findFile(os.path.join(self.fakeroot, 'boot'),
                                   'vmlinuz.*')
            fd, kernelPath = tempfile.mkstemp('.vmlinuz')
            os.close(fd)
            gencslist._linkOrCopyFile(kernel, kernelPath)
            # and instantiate the image itself
            self.createImage('cpio')
            imagesList = [(self.outfile, 'Initrd'), (kernelPath, 'Kernel')]
        finally:
            if self.fakeroot:
                util.rmtree(self.fakeroot)

        return self.moveToFinal(imagesList,
                                os.path.join(self.cfg.finishedPath,
                                             self.project.getHostname(),
                                             str(self.release.getId())))

    def __init__(self, *args, **kwargs):
        res = bootable_image.BootableImage.__init__(self, *args, **kwargs)
        self.freespace = 0
        self.addJournal = False
        self.makeBootable = False
        self.swapSize = 134217728 # 128MB swap will be removed by toolkit.
        return res
