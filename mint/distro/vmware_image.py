import os
import tempfile
import zipfile

from mint import buildtypes
from mint.distro import bootable_image

from conary.lib import util, log

class VMwareImage(bootable_image.BootableImage):
    @bootable_image.timeMe
    def zipVMwarePlayerFiles(self, dir, outfile):
        zip = zipfile.ZipFile(outfile, 'w', zipfile.ZIP_DEFLATED)
        for f in os.listdir(dir):
            zip.write(os.path.join(dir, f), os.path.join(self.basefilename, f))
        zip.close()
        os.chmod(outfile, 0644)

    @bootable_image.timeMe
    def createVMwarePlayerImage(self, outfile, displayName, mem, basedir=os.getcwd()):
        #Create a temporary directory
        vmbasedir = tempfile.mkdtemp('', 'mint-MDI-cvmpi-', basedir)
        try:
            filebase = os.path.join(vmbasedir, self.basefilename)

            if self.adapter == 'lsilogic':
                self.cylinders = self.cylinders * self.imgcfg.heads * \
                    self.imgcfg.sectors / (128 * 32)
                self.imgcfg.sectors = 32
                self.imgcfg.heads = 128

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
        cmd = 'raw2vmdk -C %d -H %d -S %d -A %s %s %s %s' % \
            (self.cylinders, self.imgcfg.heads, self.imgcfg.sectors,
             self.adapter, self.outfile, outfile, flags)
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
        filecontents = filecontents.replace('@NETWORK_CONNECTION@', \
            self.build.getDataValue('natNetworking') and 'nat' or 'bridged')
        filecontents = filecontents.replace('@ADAPTER@', self.adapter)
        filecontents = filecontents.replace('@ADAPTERDEV@',
                                            (self.adapter == 'lsilogic') \
                                                and 'scsi' or 'ide')
        filecontents = filecontents.replace('@SNAPSHOT@',
                                            str(not self.vmSnapshots).upper())

        #write the file to the proper location
        ofile = open(outfile, 'wb')
        ofile.write(filecontents)
        ofile.close()

    def write(self):
        try:
            # instantiate the contents that need to go into the image
            self.createFileTree()

            if self.adapter == 'lsilogic':
                filePath = os.path.join(self.fakeroot, 'etc', 'modprobe.conf')
                f = open(filePath, 'a')
                if os.stat(filePath)[6]:
                    f.write('\n')
                f.write('\n'.join(('alias scsi_hostadapter mptbase',
                                   'alias scsi_hostadapter1 mptspi')))
                f.close()

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
                self.build.getDataValue('vmMemory'),
                self.cfg.imagesPath)]
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
        res = bootable_image.BootableImage.__init__(self, *args, **kwargs)
        self.freespace = self.build.getDataValue("freespace") * 1048576
        self.swapSize = self.build.getDataValue("swapSize") * 1048576
        self.adapter = self.build.getDataValue('diskAdapter')
        self.vmSnapshots = self.build.getDataValue('vmSnapshots')
        return res

class VMwareESXImage(VMwareImage):
    def __init__(self, *args, **kwargs):
        res = bootable_image.BootableImage.__init__(self, *args, **kwargs)
        self.freespace = self.build.getDataValue("freespace") * 1048576
        self.swapSize = self.build.getDataValue("swapSize") * 1048576
        self.adapter = 'lsilogic'
        self.vmSnapshots = False
        self.createType = 'vmfs'
        return res

    @bootable_image.timeMe
    def createVMDK(self, outfile):
        infile = open(os.path.join(self.imgcfg.dataDir, 'vmdisk.vmdk'), 'rb')
        #Replace the @DELIMITED@ text with the appropriate values
        filecontents = infile.read()
        infile.close()

        filecontents = filecontents.replace('@CREATE_TYPE@', self.createType)
        filecontents = filecontents.replace('@FILENAME@', self.basefilename)
        filecontents = filecontents.replace('@ADAPTER@', self.adapter)
        filecontents = filecontents.replace('@EXTENTS@',
                                            str(self.imagesize / 512))
        filecontents = filecontents.replace('@CYLINDERS@', str(self.cylinders))
        filecontents = filecontents.replace( \
            '@EXT_TYPE@', self.createType == 'vmfs' and 'VMFS' or 'FLAT')

        ofile = open(outfile, 'wb')
        ofile.write(filecontents)
        ofile.close()

        os.rename(self.outfile, outfile.replace('.vmdk', '-flat.vmdk'))
