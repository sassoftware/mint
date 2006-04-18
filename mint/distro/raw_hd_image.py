#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

import os, sys

from mint import releasetypes
from mint.distro import bootable_image

from conary.lib import util

class RawHdImage(bootable_image.BootableImage):
    fileType = releasetypes.typeNames[releasetypes.RAW_HD_IMAGE]

    def write(self):
        try:
            # instantiate the contents that need to go into the image
            self.createFileTree()
            # and instantiate the image itself
            self.createImage()
            self.status('Compressing hard disk image')
            zipfn = self.compressImage(self.outfile)
            imagesList = [(zipfn, self.fileType)]
        finally:
            if self.fakeroot:
                util.rmtree(self.fakeroot)
            os.unlink(self.outfile)

        return self.moveToFinal(imagesList,
                                os.path.join(self.cfg.finishedPath,
                                             self.project.getHostname(),
                                             str(self.release.getId())))

    def __init__(self, *args, **kwargs):
        res = bootable_image.BootableImage.__init__(self, *args, **kwargs)
        self.freespace = self.release.getDataValue("freespace") * 1048576
        self.swapSize = self.release.getDataValue("swapSize") * 1048576
        return res
