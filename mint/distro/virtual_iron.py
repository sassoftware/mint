#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

import os
import tempfile
import zipfile

from mint import buildtypes
from mint import constants
from mint.distro import bootable_image
from mint.distro import vpc
from mint.distro import vhd

from conary.lib import util, log

class VirtualIronVHD(vpc.VirtualPCImage):
    suffix = '.vhd.zip'
    fileType = buildtypes.typeNames[buildtypes.VIRTUAL_IRON]

    @bootable_image.timeMe
    def createVirtualPCImage(self, outfile, basedir):
        self.status('Compressing Virtual Iron Image')
        #Create a temporary directory
        vmbasedir = tempfile.mkdtemp('', 'mint-MDI-cvmpi-', basedir)
        try:
            filebase = os.path.join(vmbasedir, self.basefilename)

            self.createVHD(filebase)
            self.zipVirtualPCFiles(vmbasedir, outfile)
        finally:
            util.rmtree(vmbasedir)
        return (outfile, self.fileType)

    def write(self):
        try:
            # instantiate the contents that need to go into the image
            self.createFileTree()
            # and instantiate the image itself
            self.createImage()

            self.status('Creating Virtual Iron Image')
            fd, outfile = tempfile.mkstemp(self.suffix, 'mint-MDI-cvmpi-',
                self.cfg.imagesPath)
            os.close(fd)
            del fd
            imagesList = [self.createVirtualPCImage( \
                    outfile, self.cfg.imagesPath)]
        finally:
            if self.fakeroot:
                util.rmtree(self.fakeroot)
            if os.path.exists(self.outfile):
                os.unlink(self.outfile)

        return self.moveToFinal(imagesList,
                                os.path.join(self.cfg.finishedPath,
                                             self.project.getHostname(),
                                             str(self.build.getId())))
