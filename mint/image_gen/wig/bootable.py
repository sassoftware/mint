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

from jobslave import geometry as js_geometry
from jobslave.generators import raw_hd_image as js_hdd
from jobslave.generators import vmware_image as js_vmware
from mint import buildtypes


class ImageConverter(object):
    """
    Converts a bootable VHD image to another format.
    """

    def __init__(self, jobData, vhdObj, vhdSize, tempDir):
        self.jobData = jobData
        self.vhdObj = vhdObj
        self.vhdSize = vhdSize
        self.scratchDir = tempfile.mkdtemp(dir=tempDir, prefix='imagegen-')

        # Make it easy to mix in jobslave image generators, which expect these
        # to be here.
        self.basefilename = self.jobData['baseFileName']
        self.baseFlavor = self.jobData['troveTup'].flavor
        self.buildOVF10 = self.jobData.getBuildData('buildOVF10')
        self.outputDir = self.scratchDir
        self.outputFileList = []
        self.workingDir = os.path.join(self.scratchDir, self.basefilename)
        os.mkdir(self.workingDir)

    def convert(self):
        raise NotImplementedError

    def getImageTitle(self):
        raise NotImplementedError

    def getBuildData(self, key):
        return self.jobData.getBuildData(key)

    def fetch(self):
        """Copy input VHD to a file in the workdir and return its path."""
        vhdPath = os.path.join(self.scratchDir, 'input.vhd')
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

        outPath = os.path.join(self.scratchDir, name)
        proc = subprocess.Popen(['/usr/bin/qemu-img', 'convert', '-O', format,
            vhdPath, outPath], shell=False)
        proc.wait()

        cny_util.removeIfExists(vhdPath)
        return outPath

    def destroy(self):
        """Clean up the workdir."""
        if self.scratchDir:
            cny_util.rmtree(self.scratchDir)
            self.scratchDir = None


class _BaseVMwareConverter(ImageConverter):

    def convert(self):
        # Unpack to raw HD
        outPath = self.qemuConvert('raw')
        disk = js_hdd.HDDContainer(outPath, geometry=js_geometry.GEOMETRY_VHD)

        # Use jobslave code to roll up a VMX tarball (VMware) or OVF 0.9
        # tarball (VMware ESX) and, if requested, an OVF 1.0 archive.
        self.configure()
        vmdkPath = self.writeMachine(disk)
        if self.buildOVF10:
            self.writeVmwareOvf(disk.totalSize, vmdkPath)
        return self.outputFileList

    def getImageTitle(self):
        return self.productName + " Image"


class VMwareConverter(_BaseVMwareConverter, js_vmware.VMwareImage):
    pass


class VMwareESXConverter(_BaseVMwareConverter, js_vmware.VMwareESXImage):
    pass


def getConverter(jobData, vhdObj, vhdSize, tempDir):
    imageType = jobData['buildType']
    if imageType == buildtypes.VMWARE_IMAGE:
        cls = VMwareConverter
    elif imageType == buildtypes.VMWARE_ESX_IMAGE:
        cls = VMwareESXConverter
    else:
        raise RuntimeError("Unsupported image type %r" % (imageType,))

    return cls(jobData, vhdObj, vhdSize, tempDir)
