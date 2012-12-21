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
from mint.image_gen import constants as iconst
from mint.image_gen.util import FileWithProgress


STEP_FETCH          = 0
STEP_UNPACK         = 1
STEP_REPACK         = 2
STEP_COMPRESS       = 3
STEP_OVF            = 3
CONVERTER_STEPS = [
        STEP_FETCH,
        STEP_UNPACK,
        STEP_REPACK,
        STEP_COMPRESS,
        STEP_OVF,
        ]


class ImageConverter(object):
    """
    Converts a bootable VHD image to another format.
    """
    alwaysOvf10 = False

    def __init__(self, jobData, vhdObj, vhdSize, tempDir, callback=None):
        self.jobData = jobData
        self.vhdObj = vhdObj
        self.vhdSize = vhdSize
        self.scratchDir = tempfile.mkdtemp(dir=tempDir, prefix='imagegen-')

        # Make it easy to mix in jobslave image generators, which expect these
        # to be here.
        self.basefilename = self.jobData['baseFileName']
        self.baseFlavor = self.jobData['troveTup'].flavor
        self.buildOVF10 = self.jobData.getBuildData('buildOVF10') or self.alwaysOvf10
        self.outputDir = self.scratchDir
        self.outputFileList = []
        self.workingDir = os.path.join(self.scratchDir, self.basefilename)
        os.mkdir(self.workingDir)

        # Status machinery
        self._callback = callback
        self._steps = CONVERTER_STEPS[:]
        if not self.buildOVF10:
            self._steps.remove(STEP_OVF)

    def sendStatus(self, code, message, percent=None):
        """Send status upstream.

        C{percent}, if set, is either an integer or a tuple C{(done, total)}
        where C{done} and C{total} are arbitrary units, such as bytes.
        """
        if not self._callback:
            return
        totalSteps = len(self._steps)
        currentStep = self._steps.index(code)
        progress = '%d/%d' % (currentStep, totalSteps)
        if percent is not None:
            if isinstance(percent, tuple):
                done, total = percent
                if total:
                    percent = int(100.0 * done / total)
                else:
                    percent = 0
            progress += ';%d%%' % (percent,)
        self._callback(iconst.WIG_JOB_CONVERTING, message, progress)

    def convert(self):
        raise NotImplementedError

    def getImageTitle(self):
        raise NotImplementedError

    def getBuildData(self, key):
        return self.jobData.getBuildData(key)

    def fetch(self, name='input.vhd'):
        """Copy input VHD to a file in the workdir and return its path."""
        vhdPath = os.path.join(self.scratchDir, name)
        tempFobj = open(vhdPath, 'wb')

        def callback(transferred):
            self.sendStatus(STEP_FETCH, "Retrieving VHD", (transferred,
                self.vhdSize))
        callback(0)
        wrapper = FileWithProgress(self.vhdObj, callback)
        copied = cny_util.copyfileobj(wrapper, tempFobj)

        tempFobj.close()
        self.vhdObj.close()
        self.vhdObj = None
        if copied != self.vhdSize:
            raise RuntimeError("Downloaded VHD is wrong size -- "
                    "expected %s but got %s" % (self.vhdSize, copied))
        return vhdPath

    def qemuConvert(self, format, name='output.img'):
        vhdPath = self.fetch()

        # TODO: figure out how to get progress out of this step
        self.sendStatus(STEP_UNPACK, "Unpacking VHD")
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


class VHDConverter(ImageConverter):
    imageName = "VHD Image"

    def convert(self):
        vhdPath = self.fetch(self.basefilename + '.vhd')
        self.outputFileList.append((vhdPath, self.imageName))
        return self.outputFileList

    def getImageTitle(self):
        return self.imageName


class _BaseVMwareConverter(ImageConverter):

    def convert(self):
        # Unpack to raw HD
        outPath = self.qemuConvert('raw')
        disk = js_hdd.HDDContainer(outPath, geometry=js_geometry.GEOMETRY_VHD)

        # Use jobslave code to roll up a VMX tarball (VMware) or OVF 0.9
        # tarball (VMware ESX) and, if requested, an OVF 1.0 archive.
        vmCallback = _VMwareCallback(self.sendStatus)
        assert 'vmwareOS' in self.jobData
        self.configure()
        vmdkPath = self.writeMachine(disk, callback=vmCallback)
        if self.buildOVF10:
            # TODO: figure out how to get progress out of this step
            self.sendStatus(STEP_OVF, "Creating OVF 1.0 archive")
            self.writeVmwareOvf(disk.totalSize, vmdkPath)
        return self.outputFileList

    def getImageTitle(self):
        return self.productName + " Image"


class VMwareConverter(_BaseVMwareConverter, js_vmware.VMwareImage):
    pass


class VMwareESXConverter(_BaseVMwareConverter, js_vmware.VMwareESXImage):
    pass


class _VMwareCallback(js_vmware.VMwareCallback):

    def __init__(self, sendStatus):
        self.sendStatus = sendStatus

    def creatingDisk(self, completed, total):
        # completed, total not set yet
        self.sendStatus(STEP_REPACK, "Creating VMware (R) Virtual Disk")

    def creatingArchive(self, compeleted, total):
        # completed, total not set yet
        self.sendStatus(STEP_COMPRESS, "Creating VMware (R) image archive")


def getConverter(jobData, vhdObj, vhdSize, tempDir, callback=None):
    imageType = jobData['buildType']
    if imageType == buildtypes.VMWARE_IMAGE:
        cls = VMwareConverter
    elif imageType == buildtypes.VMWARE_ESX_IMAGE:
        cls = VMwareESXConverter
    elif imageType == buildtypes.VIRTUAL_PC_IMAGE:
        cls = VHDConverter
    else:
        raise RuntimeError("Unsupported image type %r" % (imageType,))

    return cls(jobData, vhdObj, vhdSize, tempDir, callback)
