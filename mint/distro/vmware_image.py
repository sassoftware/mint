import os
import tempfile
import zipfile

from mint import releasetypes
from mint.distro import bootable_image

from conary.lib import util, log

class VMwareImage(bootable_image.BootableImage):
    @bootable_image.timeMe
    def zipVMwarePlayerFiles(self, dir, outfile):
        zip = zipfile.ZipFile(outfile, 'w', zipfile.ZIP_DEFLATED)
        for f in ('.vmdk', '.vmx'):
            zip.write(os.path.join(dir, self.basefilename + f), os.path.join(self.basefilename, self.basefilename + f))
        zip.close()
        os.chmod(outfile, 0644)

    @bootable_image.timeMe
    def createVMwarePlayerImage(self, outfile, displayName, mem, basedir=os.getcwd()):
        #Create a temporary directory
        vmbasedir = tempfile.mkdtemp('', 'mint-MDI-cvmpi-', basedir)
        try:
            filebase = os.path.join(vmbasedir, self.basefilename)
            #run qemu-img to convert to vmdk
            self.createVMDK(filebase + '.vmdk')
            #Populate the vmx file
            self.createVMX(filebase + '.vmx', displayName, mem)
            #zip the resultant files
            self.zipVMwarePlayerFiles(vmbasedir, outfile)
        finally:
            util.rmtree(vmbasedir)
        return (outfile, 'VMware Player Image')

    @bootable_image.timeMe
    def createVMDK(self, outfile):
        flags = ''
        if self.imgcfg.debug:
            flags += ' -v'
        cmd = 'raw2vmdk -C %d %s %s %s' % (self.cylinders, self.outfile,
                    outfile, flags)
        log.debug("Running", cmd)
        util.execute(cmd)

    @bootable_image.timeMe
    def createVMX(self, outfile, displayName, memsize):
        #Read in the stub file
        infile = open(os.path.join(self.imgcfg.dataDir, 'vmwareplayer.vmx'), 'rb')
        #Replace the @DELIMITED@ text with the appropriate values
        filecontents = infile.read()
        infile.close()
        #@NAME@ @MEM@ @FILENAME@
        displayName.replace('"', '')
        filecontents = filecontents.replace('@NAME@', displayName)
        filecontents = filecontents.replace('@MEM@', str(memsize))
        filecontents = filecontents.replace('@FILENAME@', self.basefilename)
        #write the file to the proper location
        ofile = open(outfile, 'wb')
        ofile.write(filecontents)
        ofile.close()

    def write(self):
        try:
            # instantiate the contents that need to go into the image
            self.createFileTree()
            # and instantiate the image itself
            self.createImage()

            # this was a wild stab in the dark...
            ## vmware creation expects a compressed image
            #self.status('Compressing hard disk image')
            #zipfn = self.compressImage(self.outfile)

            self.status('Creating VMware Player Image')
            fd, vmfn = tempfile.mkstemp('.vmware.zip', 'mint-MDI-cvmpi-',
                                        self.cfg.imagesPath)
            os.close(fd)
            del fd
            imagesList = [self.createVMwarePlayerImage( \
                vmfn, self.project.getName(),
                self.release.getDataValue('vmMemory'),
                self.cfg.imagesPath)]
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
