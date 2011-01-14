#
# Copyright (c) 2011 rPath, Inc.
#

"""
Convert VHD bootable images created by the Windows Build Service to other
virtualization formats.
"""

import os
import subprocess
import tempfile
from conary.lib import util as cny_util

from mint import buildtypes


class ImageConverter(object):
    """
    Converts a bootable VHD image to another format.
    """

    def __init__(self, vhdObj, vhdSize, tempDir):
        self.vhdObj = vhdObj
        self.vhdSize = vhdSize
        self.workDir = tempfile.mkdtemp(dir=tempDir, prefix='imagegen-')

    def convert(self):
        raise NotImplementedError

    def fetch(self):
        """Copy input VHD to a file in the workdir and return its path."""
        vhdPath = os.path.join(self.workDir, 'input.vhd')
        tempFobj = open(vhdPath, 'wb')
        copied = cny_util.copyfileobj(self.vhdObj, tempFobj)
        tempFobj.close()
        self.vhdObj.close()
        self.vhdObj = None
        if copied != self.vhdSize:
            raise RuntimeError("Downloaded VHD is wrong size -- "
                    "expected %s but got %s" % (self.vhdSize, copied))
        return vhdPath

    def qemuConvert(self, format, name='output.img'):
        vhdPath = self.fetch()

        outPath = os.path.join(self.workDir, name)
        proc = subprocess.Popen(['/usr/bin/qemu-img', 'convert', '-O', format,
            vhdPath, outPath], shell=False)
        proc.wait()

        cny_util.removeIfExists(vhdPath)
        return outPath

    def destroy(self):
        """Clean up the workdir."""
        if self.workDir:
            cny_util.rmtree(self.workDir)
            self.workDir = None


class VMDKConverter(ImageConverter):

    outputName = "VMware (R) Image"

    def convert(self):
        outPath = self.qemuConvert('vmdk')
        return outPath, self.outputName


def getConverter(imageType, vhdObj, vhdSize, tempDir):
    if imageType == buildtypes.VMWARE_IMAGE:
        cls = VMDKConverter
    else:
        raise RuntimeError("Unsupported image type %r" % (imageType,))

    return cls(vhdObj, vhdSize, tempDir)
