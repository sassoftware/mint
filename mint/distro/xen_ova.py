#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#

import os
import tempfile
import stat
import zipfile

from mint import buildtypes
from mint import constants
from mint.distro import raw_fs_image, bootable_image

from conary.lib import util, log

class XenOVA(raw_fs_image.RawFsImage):
    fileType = buildtypes.typeNames[buildtypes.XEN_OVA]

    templateName = 'ova.xml.in'
    suffix = '.xva.zip'

    @bootable_image.timeMe
    def zipOVAFiles(self, dir, outfile):
        cwd = os.getcwd()
        os.chdir(dir)
        try:
            util.execute('zip -0rD %s %s' % (outfile, self.basefilename))
        finally:
            try:
                os.chdir(cwd)
            except OSError, e:
                if e.errno == 2:
                    pass

    @bootable_image.timeMe
    def createXVA(self, tmpDir):
        outfile = os.path.join(tmpDir, self.basefilename, 'ova.xml')

        # Read in the stub file
        infile = file(os.path.join(self.imgcfg.dataDir, self.templateName), 'rb')

        # Replace the @DELIMITED@ text with the appropriate values
        template = infile.read()
        infile.close()

        template = template.replace('@TITLE@', self.build.getName())
        template = template.replace('@DESCRIPTION@',
            'Created by rPath rBuilder version %s' % constants.mintVersion)
        template = template.replace('@MEMORY@', str(self.build.getDataValue('vmMemory') * 1024 * 1024))
        template = template.replace('@DISKSIZE@', str(os.stat(self.outfile)[stat.ST_SIZE]))

        # write the file to the proper location
        ofile = file(outfile, 'wb')
        ofile.write(template)
        ofile.close()

    def write(self):
        try:
            # instantiate the contents that need to go into the image
            self.createFileTree()
            # and instantiate the image itself
            self.createImage()

            self.status('Creating Xen Enterprise XVA')

            # create a temporary directory for creation
            tmpDir = tempfile.mkdtemp('', 'mint-MDI-cvmpi-', self.cfg.imagesPath)
            fd, outFile = tempfile.mkstemp(self.suffix, dir = self.cfg.imagesPath)
            os.unlink(outFile)
            util.mkdirChain(os.path.join(tmpDir, self.basefilename, 'sda'))

            self.createXVA(tmpDir)

            # FIXME: do the dir-chunked split here
            self.outfile = self.compressImage(self.outfile)

            os.rename(self.outfile, os.path.join(tmpDir, self.basefilename, 'sda', 'chunk-000000000.gz') )

            self.zipOVAFiles(tmpDir, outFile)

            imagesList = [(outFile, self.fileType)]
        finally:
            if self.fakeroot:
                util.rmtree(self.fakeroot)
            if os.path.exists(self.outfile):
                os.unlink(self.outfile)

        return self.moveToFinal(imagesList,
                    os.path.join(self.cfg.finishedPath,
                                 self.project.getHostname(),
                                 str(self.build.getId())))
