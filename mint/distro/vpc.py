#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#

import os
import tempfile
import zipfile

from mint import buildtypes
from mint import constants
from mint.distro import bootable_image
from mint.distro import vhd

from conary.lib import util, log

class VirtualPCImage(bootable_image.BootableImage):
    @bootable_image.timeMe
    def zipVirtualPCFiles(self, dir, outfile):
        cwd = os.getcwd()
        os.chdir(dir)
        try:
            files = os.listdir(dir)
            os.mkdir(os.path.join(dir, self.basefilename))
            for fr in files:
                os.rename(os.path.join(dir, fr),
                os.path.join(dir, self.basefilename, fr))
            pathOut, baseOut = os.path.split(outfile)
            util.execute('zip -rD %s %s' % (baseOut, self.basefilename))
            os.rename(baseOut, outfile)
        finally:
            try:
                os.chdir(cwd)
            except OSError, e:
                if e.errno == 2:
                    pass

    @bootable_image.timeMe
    def createVirtualPCImage(self, outfile, basedir):
        self.status('Compressing Microsoft Virtual Server Image')
        #Create a temporary directory
        vmbasedir = tempfile.mkdtemp('', 'mint-MDI-cvmpi-', basedir)
        try:
            filebase = os.path.join(vmbasedir, self.basefilename)

            self.createVHD(filebase)
            #Populate the vmc file
            self.createVMC(filebase)
            #zip the resultant files
            self.zipVirtualPCFiles(vmbasedir, outfile)
        finally:
            util.rmtree(vmbasedir)
        return (outfile, 'Virtual Server')

    @bootable_image.timeMe
    def createVHD(self, filebase):
        diskType = self.build.getDataValue('vhdDiskType')
        if diskType == 'dynamic':
            vhd.makeDynamic(self.outfile, filebase + '.vhd')
        elif diskType == 'fixed':
            vhd.makeFlat(self.outfile)
            os.rename(self.outfile, filebase + '.vhd')
        elif diskType == 'difference':
            vhd.makeDynamic(self.outfile, filebase + '-base.vhd')
            os.chmod(filebase + '-base.vhd', 0400)
            vhd.makeDifference(filebase + '-base.vhd', filebase + '.vhd',
                               self.basefilename + '-base.vhd')

    @bootable_image.timeMe
    def createVMC(self, fileBase):
        outfile = fileBase + '.vmc'
        diskFileName = fileBase + '.vhd'
        # Read in the stub file
        infile = open(os.path.join(self.imgcfg.dataDir, self.templateName),
                      'rb')
        # Replace the @DELIMITED@ text with the appropriate values
        filecontents = infile.read()
        infile.close()
        filecontents = filecontents.replace('@DISK_FILENAME@',
                                            os.path.basename(diskFileName))
        filecontents = filecontents.replace('@MINT_VERSION@',
                                            constants.mintVersion)

        # write the file to the proper location
        ofile = open(outfile, 'wb')
        # NOTE: Virtual PC only handles UTF-16.
        ofile.write(filecontents.encode('utf-16'))
        ofile.close()

    def write(self):
        try:
            # instantiate the contents that need to go into the image
            self.createFileTree()
            # and instantiate the image itself
            self.createImage()

            self.status('Creating Microsoft Virtual Server Image')
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

    def __init__(self, *args, **kwargs):
        bootable_image.BootableImage.__init__(self, *args, **kwargs)
        self.freespace = self.build.getDataValue("freespace") * 1048576
        self.swapSize = self.build.getDataValue("swapSize") * 1048576

        self.templateName = 'vpc.vmc'
        self.suffix = '.vpc.zip'
