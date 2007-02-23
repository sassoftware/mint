#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

import os
import tempfile

import boto

from conary.conarycfg import ConfigFile
from conary.lib import util

from mint import buildtypes
from mint import mint_error
from mint.data import RDT_STRING
from mint.distro import bootable_image
from mint.distro.imagegen import NoConfigFile

AMIFstabAdditions = """
# added to mount a huge /tmp and swap for AMIs
/dev/sda2\t%s\t\text3\tdefaults 1 2
/dev/sda3\tswap\t\tswap\tdefaults 0 0
"""

class AMIBundleError(mint_error.MintError):
    def __str__(self):
        return "Failed to create the AMI bundle"

class AMIUploadError(mint_error.MintError):
    def __str__(self):
        return "Failed to upload the image to the Amazon EC2 Service"

class AMIRegistrationError(mint_error.MintError):
    def __str__(self):
        return "Failed to register the image with the Amazon EC2 Service"

class AMIImage(bootable_image.BootableImage):
    fileType = buildtypes.typeNames[buildtypes.AMI]

    def __init__(self, *args, **kwargs):
        res = bootable_image.BootableImage.__init__(self, *args, **kwargs)

        # load AMI config
        self.amiConfig = AMIImageConfig()
        amiConfigFile = os.path.join(self.cfg.configPath, self.amiConfig.filename)
        if os.access(amiConfigFile, os.R_OK):
            self.amiConfig.read(amiConfigFile)
        else:
            raise NoConfigFile(amiConfigFile)

        # we don't want our FS image to have a swapfile
        self.swapSize = 0

        # have to pull this in from the advanced settings
        self.freespace = self.build.getDataValue("freespace") * 1048576

        # get the spot we're going to mount the hyooge disk on
        self.hugeDiskMountpoint = \
                self.build.getDataValue('amiHugeDiskMountpoint')

        # this image type is like raw FS; don't make it bootable
        self.makeBootable = False
        return res

    @bootable_image.timeMe
    def createAMIBundle(self, inputFSImage, bundlePath):
        # actually call out to create the AMI bundle
        ec2ImagePrefix = "%s_%s.img" % (self.basefilename, self.build.id)
        try:
            os.system('ec2-bundle-image -i %s -u %s -c %s -k %s -d %s -p %s' % \
                    (inputFSImage, self.amiConfig.EC2UserId,
                        self.amiConfig.EC2CertPath, self.amiConfig.EC2KeyPath,
                        bundlePath, ec2ImagePrefix))
            for f in os.listdir(bundlePath):
                if f.endswith('.xml'):
                    return f
        except OSError:
            pass

        return None

    @bootable_image.timeMe
    def uploadAMIBundle(self, pathToManifest):
        try:
            os.system('ec2-upload-bundle -m %s -b %s -a %s -s %s' % \
                    (pathToManifest, self.amiConfig.bucket,
                     self.amiConfig.publicKey, self.amiConfig.privateKey))
            return True
        except OSError:
            return False

    def registerAMI(self, pathToManifest):
        amiId = None
        s3Manifest = '%s/%s' % (self.amiConfig.bucket,
                os.path.basename(pathToManifest))
        c = boto.connect_ec2(self.amiConfig.publicKey,
                self.amiConfig.privateKey)
        amiId = str(c.register_image(s3Manifest))
        self.build.setDataValue("amiId", amiId, RDT_STRING, False)
        self.build.setDataValue("amiS3Manifest", s3Manifest, RDT_STRING, False)
        return amiId

    def writeFstab(self):
        bootable_image.BootableImage.writeFstab(self)

        # append some useful things for AMIs
        fstabFile = file(os.path.join(self.fakeroot, 'etc', 'fstab'), 'a+')
        fstabFile.write(AMIFstabAdditions % self.hugeDiskMountpoint)
        fstabFile.close()

    def updateKernelChangeSet(self, callback):
        # AMIs don't need a kernel
        return None

    def write(self):
        tmpBundlePath = tempfile.mkdtemp('', 'amibundle', self.cfg.imagesPath)
        try:
            # instantiate the contents that need to go into the image
            self.createFileTree()
            # and instantiate the image itself
            self.createImage()
            self.status("Creating the AMI bundle")
            manifestPath = self.createAMIBundle(self.outfile, tmpBundlePath)
            if not manifestPath:
                raise AMIBundleError
            self.status("Uploading the AMI bundle to Amazon EC2")
            if not self.uploadAMIBundle(os.path.join(tmpBundlePath,
                manifestPath)):
                raise AMIUploadError
            self.status("Registering AMI")
            amiId = self.registerAMI(manifestPath)
            if not amiId:
                raise AMIRegistrationError
        finally:
            if self.fakeroot:
                util.rmtree(self.fakeroot)
            if tmpBundlePath:
                util.rmtree(tmpBundlePath)
            os.unlink(self.outfile)

        # return empty list because files aren't stored here, they're on
        # Amazon's EC2 service
        return []

class AMIImageConfig(ConfigFile):
    filename = 'ami.conf'

    # AMAZON EC2 file to cert path
    EC2CertPath                 = '/srv/rbuilder/config/rpath-ec2.pem'
    EC2KeyPath                  = '/srv/rbuilder/config/rpath-ec2.key'
    EC2UserId                   = ''

    # AMAZON CREDENTIALS (left blank intentionally; edit conf file)
    publicKey                   = ''
    privateKey                  = ''

    # bucket to store EC2 virtual machines in
    bucket                      = 'rbuilder-ec2-test'

