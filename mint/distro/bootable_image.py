#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

# python standard library imports
import os
import sys
import errno
import time
import tempfile

# mint imports
from imagegen import ImageGenerator
from mint import releasetypes

# conary imports
from conary import conaryclient
from conary import deps
from conary import flavorcfg
from conary import versions
from conary.conaryclient.cmdline import parseTroveSpec
from conary.repository import errors
from conary.callbacks import UpdateCallback
from conary.callbacks import ChangesetCallback
from conary.conarycfg import ConfigFile
from conary.lib import log
from conary.lib import util

class BootableImageConfig(ConfigFile):
    #Different cylinder sizes.  I don't know which is better, but I've seen
    #both: 8225280 or 516096
    cylindersize    = 516096
    sectors         = 63
    heads           = 16

    #Offset at which to drop the file system in the raw disk image
    partoffset0     = 512

    #directory containing the uml init script as well as fstab and other hooks
    dataDir         = os.path.join(os.path.dirname(__file__), 'DiskImageData')
    umlKernel       = '/usr/bin/uml-vmlinux'
    shortCircuit    = 0 #1: Use a static name for the root dir and the qemu image.
                        #Change this to false to use securely named temp files.

def debugme(type, value, tb):
    from conary.lib import epdb
    epdb.post_mortem(tb,type,value)

class Journal:
    def lchown(self, root, target, user, group):
        # get rid of the root
        target = target[len(root):]
        dirname = os.path.dirname(target)
        filename = os.path.basename(target)
        f = open(os.sep.join((root, dirname, '.UIDGID')), 'a')
        # XXX e2fsimage does not handle group lookups yet
        f.write('%s %s\n' %(filename, user))
        f.close()

    def mknod(self, root, target, devtype, major, minor, mode,
              uid, gid):
        # get rid of the root
        target = target[len(root):]
        dirname = os.path.dirname(target)
        filename = os.path.basename(target)
        f = open(os.sep.join((root, dirname, '.DEVICES')), 'a')
        # XXX e2fsimage does not handle symbolic users/groups for .DEVICES
        f.write('%s %s %d %d 0%o\n' %(filename, devtype, major, minor, mode))
        f.close()

def timeMe(func):
    def wrapper(self, *args, **kwargs):
        clock = time.clock()
        actual = time.time()
        returner = func(self, *args, **kwargs)
        print "%s: %.5f %.5f" % (func.__name__, time.clock() - clock, time.time() - actual)
        return returner
    return wrapper

def outputfilesize(func):
    def wrapper(self, *args, **kwargs):
        returner = func(self, *args, **kwargs)
        st = os.stat(self.outfile)
        print "size of %s after %s: %d bytes" % (self.outfile, func.__name__, st.st_size)
        return returner
    return wrapper


class InstallCallback(UpdateCallback, ChangesetCallback):
    def restoreFiles(self, size, totalSize):
        if totalSize != 0:
            self.restored += size
            self.update('writing files (%d%% of %dK)'
                        %((self.restored * 100) / totalSize, totalSize / 1024))

    def requestingChangeSet(self):
        self.update('requesting changeset')

    def setUpdateHunk(self, num, total):
        self.restored = 0

    def downloadingChangeSet(self, got, need):
        if need != 0:
            self.update('downloading from repository (%d%% of %dk)' %
                        ((got * 100) / need, need / 1024))

    def update(self, msg):
        # only push an update into the database if it differs from the
        # current message
        if self.msg != msg:
            self.msg = msg
            self.status(msg)

    def __init__(self, status):
        self.abortEvent = None
        self.status = status
        self.restored = 0
        self.msg = ''
        self.changeset = ''
        self.prefix = 'BDI:'

class BootableDiskImage:
    def __init__(self, outfile, fakeroot, trove, versionstr, flavorstr, freespace, arch, cfg, conarycfg):
        sys.excepthook = debugme
        self.outfile = outfile
        self.fakeroot = fakeroot
        self.basetrove = trove
        self.baseversion = versionstr
        self.baseflavor = flavorstr
        self.freespace = freespace
        self.arch = arch
        self.cfg = cfg
        self.conarycfg = conarycfg

    @outputfilesize
    @timeMe
    def prepareDiskImage(self):
        #create the disk file this will blank the file if it exists.
        ofile = open(self.outfile, 'wb', 0644)
        ofile.seek(self.imagesize-1)
        ofile.write('\x00')
        ofile.close()

        #Do the partition table
        cylinders = self.imagesize / self.cfg.cylindersize
        cmd = '/sbin/sfdisk -C %d -S %d -H %d %s > /dev/null' % (cylinders, self.cfg.sectors, self.cfg.heads, self.outfile)
        input = "0 %d L *\n" % (cylinders)
        sfdisk = util.popen(cmd, 'w')
        sfdisk.write(input)
        retval = sfdisk.close()

    def _writefstab(self):
        util.copyfile(os.path.join(self.cfg.dataDir, 'fstab'), os.path.join(self.fakeroot, 'etc'))

    def _setupGrub(self):
        util.copytree(os.path.join(self.fakeroot, 'usr', 'share', 'grub', '*', '*'), os.path.join(self.fakeroot, 'boot', 'grub'))
        #Create a stub grub.conf
        name = open(os.path.join(self.fakeroot, 'etc', 'issue'), 'r').readlines()[0].strip()
        fd = open(os.path.join(self.fakeroot, 'boot', 'grub', 'grub.conf'), 'w')
        fd.write("""
#grub.conf generated by rBuilder
#
# Note that you do not have to rerun grub after making changes to this file
#boot=/dev/hda
default=0
timeout=10
title %(name)s (%(kversion)s)
    root (hd0,0)
    kernel /boot/vmlinuz-%(kversion)s ro root=LABEL=/ quiet
    initrd /boot/initrd-%(kversion)s.img

""" % {'name': name, 'kversion': 'somesillyversion'})
        os.chmod(os.path.join(self.fakeroot, 'boot/grub/grub.conf'), 0600)
        fd.close()
        #create the appropriate links
        os.symlink('grub.conf', os.path.join(self.fakeroot, 'boot', 'grub', 'menu.lst'))
        os.symlink('../boot/grub/grub.conf', os.path.join(self.fakeroot, 'etc', 'grub.conf'))

    @timeMe
    def createTemporaryRoot(self, basedir = os.getcwd()):
        #Create a temporary directory
        if self.fakeroot is None:
            self.fakeroot = tempfile.mkdtemp('', 'mint-MDI-', basedir)
        #Create some structure
        cwd = os.getcwd()
        os.chdir(self.fakeroot)
        util.mkdirChain( 'etc', 'boot/grub', 'tmp', 'sys' )
        os.chdir(cwd)

    @timeMe
    def setupConaryClient(self):
        #Create a ConaryClient
        if self.conarycfg is None:
            self.conarycfg = conarycfg.ConaryConfiguration(readConfigFiles=False)
            self.conarycfg.repositoryMap = self.repoMap
            self.conarycfg.flavor = None
            self.conarycfg.root = self.fakeroot
            #TODO Add the user if anonymous access is not available

        self.conarycfg.installLabelPath = None
        self.conarycfg.dbPath = '/var/lib/conarydb/'

        self.cclient = conaryclient.ConaryClient(self.conarycfg)

    @timeMe
    def updateGroupChangeSet(self, callback):
        try:
            itemList = [(self.basetrove, (None, None), (self.baseversion, self.baseflavor), True)]
            log.info("itemList: %s" % str(itemList))
            sys.stderr.flush()
            uJob, suggMap = self.cclient.updateChangeSet(itemList, resolveDeps = False,
                                    callback = callback)
        except errors.TroveNotFound:
            raise
        return uJob

    @timeMe
    def applyGroupUpdate(self, uJob, callback):
        #Capture devices, taghandlers and ownership changes
        journal = Journal()
        #Install the group
        self.cclient.applyUpdate(uJob, journal=journal, callback = callback,
                tagScript=os.path.join(self.fakeroot, 'tmp', 'tag-scripts'))

    @timeMe
    def populateTemporaryRoot(self, callback = None):
        uJob = self.updateGroupChangeSet( callback )
        self.applyGroupUpdate(uJob, callback)

    @timeMe
    def updateKernelChangeSet(self, callback):
        #Install the Kernel
        try:
            kernel, version, flavor = parseTroveSpec('kernel[!kernel.smp is: %s]' % self.arch)
            itemList = [(kernel, (None, None), (version, flavor), True)]
            uJob, suggMap = self.cclient.updateChangeSet(itemList, sync=True,
                                callback = callback,
                                resolveDeps=False)
        except errors.TroveNotFound:
            raise
        return uJob

    @timeMe
    def applyKernelUpdate(self, uJob, callback):
        journal = Journal()
        self.cclient.applyUpdate(uJob, journal=journal, callback = callback,
                tagScript=os.path.join(self.fakeroot, 'tmp', 'kernel-tag-scripts'))

    @timeMe
    def installKernel(self, callback = None):
        uJob = self.updateKernelChangeSet(callback)
        self.applyKernelUpdate(uJob, callback)

    @timeMe
    def fileSystemOddsNEnds(self):
        #write the fstab
        self._writefstab()
        #create a swap file
        swap = open(os.path.join(self.fakeroot, 'var', 'swap'), 'w')
        swap.seek(128*1024*1024 - 1)
        swap.write('\x00')
        swap.close()
        #Initialize the swap file
        cmd = '/sbin/mkswap %s' % os.path.join(self.fakeroot, 'var', 'swap')
        util.execute(cmd)
        #copy the files needed by grub and set up the links
        self._setupGrub()
        #Create the init script
        util.copyfile(os.path.join(self.cfg.dataDir, 'init.sh'), os.path.join(self.fakeroot, 'tmp'))
        os.chmod(os.path.join(self.fakeroot, 'tmp', 'init.sh'), 0755)
        util.copyfile(os.path.join(self.cfg.dataDir, 'pre-tag-scripts'), os.path.join(self.fakeroot, 'tmp'))
        util.copyfile(os.path.join(self.cfg.dataDir, 'post-tag-scripts'), os.path.join(self.fakeroot, 'tmp'))
        util.copyfile(os.path.join(self.cfg.dataDir, 'post-kernel-tag-scripts'), os.path.join(self.fakeroot, 'tmp'))

    @timeMe
    def MakeE3FsImage(self, file):
        cmd = '/usr/bin/e2fsimage -f %s -d %s -s %d' % (file,
                self.fakeroot, (self.imagesize - self.cfg.partoffset0)/1024)
        util.execute(cmd)
        cmd = '/sbin/e2label %s /' % file
        util.execute(cmd)
        cmd = '/sbin/tune2fs -i 0 -c 0 -j %s' % file
        util.execute(cmd)

    @outputfilesize
    @timeMe
    def WriteBack(self, file):
        #Now write this FS image back to the original image
        fd = open(file, 'rb')
        fdo = open(self.outfile, 'r+b')
        fdo.seek(self.cfg.partoffset0)
        util.copyfileobj(fd, fdo, bufSize=524288)
        fd.close()
        fdo.close()
 
    @timeMe
    def createFileSystem(self, basedir = os.getcwd()):
        #This file isn't needed outside this function, and is cleaned up when it exits
        fd, file = tempfile.mkstemp('', 'mint-MDI-cFS-', basedir)
        os.close(fd)
        del fd
        try:
            #How much space do we need?
            fd = os.popen('/usr/bin/du -B1 --max-depth=0 %s' % self.fakeroot, 'r')
            size = int(fd.read().strip().split()[0])
            size += self.freespace + self.cfg.partoffset0
            padding = self.cfg.cylindersize - (size % self.cfg.cylindersize)
            if self.cfg.cylindersize == padding:
                padding = 0
            self.imagesize = size + padding
            self.MakeE3FsImage(file)
            self.prepareDiskImage()
            self.WriteBack(file)
        finally:
            os.unlink(file)

    @timeMe
    def runTagScripts(self):
        cmd = '%s root=/dev/ubda1 init=/tmp/init.sh mem=128M ubd0=%s > uml-vmlinux.log' % (self.cfg.umlKernel, self.outfile)
        util.execute(cmd)

    @timeMe
    def makeBootable(self):
        #install boot manager
        cmd = '%s --device-map=/dev/null --batch > grub-install.log' % os.path.join(self.fakeroot, 'sbin', 'grub')
        input = """
device  (hd0)   %s
root    (hd0,0)
setup   (hd0)
quit
""" % self.outfile
        uml = util.popen(cmd, 'w')
        uml.write(input)
        retval = uml.close()

class BootableImage(ImageGenerator):
    supportedImageTypes = [ releasetypes.QEMU_IMAGE, releasetypes.LIVE_ISO ]

    def status(self, value):
        value = 'BootableImage: ' + value
        ImageGenerator.status(self, value)

    def getConfig(self):
        cfg = BootableImageConfig()
        cfg.read("bootable_image.conf")
        return cfg

    def setImageTypes(self, imageTypes):
        self.imageTypes = imageTypes

    def workToDo(self):
        returner = False
        for imageType in self.imageTypes:
            if imageType in self.supportedImageTypes:
                returner = True
                break
        return returner

    def write(self):
        imgcfg = self.getConfig()

        #Create the output file:
        if not imgcfg.shortCircuit:
            fd, fn = tempfile.mkstemp('.img', 'qemuimg', self.cfg.imagesPath)
            os.close(fd)
            os.chmod(fn, 0644)
        else:
            fn = os.path.join(self.cfg.imagesPath, 'qemu.img')

        #Create the directory to use as the root for the conary commands
        if not imgcfg.shortCircuit:
            tmpDir = tempfile.mkdtemp("", "imagetool", self.cfg.imagesPath)
            log.info('generating qemu image with tmpdir %s', tmpDir)
        else:
            tmpDir = os.path.join(self.cfg.imagesPath, 'shortcircuit_qemud')
            try:
                os.makedirs(tmpDir)
            except OSError, e:
                if e.errno != errno.EEXIST:
                    raise

        #Figure out what group trove to use
        release = self.client.getRelease(self.job.getReleaseId())
        trove, versionStr, flavorStr = release.getTrove()
        log.info('release.getTrove returned (%s, %s, %s)' % (trove, versionStr, flavorStr))

        #Thaw the version string
        versionStr = versions.ThawVersion(versionStr).asString()

        #Thaw the flavor string
        flavorStr = deps.deps.ThawDependencySet(flavorStr)

        #The project object
        project = self.client.getProject(release.getProjectId())

        # set up configuration
        cfg = project.getConaryConfig(overrideSSL=True, useSSL=self.cfg.SSL)
        # turn off threading
        cfg.threaded = False
        cfg.setValue('root', tmpDir)

        arch = release.getArch()
        #TODO This needs to be configured in the interface
        freespace = release.getDataValue("freespace")

        image = BootableDiskImage(fn, tmpDir, trove, versionStr, flavorStr, freespace * 1024 * 1024, arch, imgcfg, cfg)

        callback = InstallCallback(self.status)

        if not imgcfg.shortCircuit:
            pass
        self.status('Creating temporary root')
        image.createTemporaryRoot()

        #Don't need status here.  It's very fast
        image.setupConaryClient()

        self.status('Installing software')
        image.populateTemporaryRoot(callback)

        self.status('Installing %s kernel' % arch)
        image.installKernel(callback)

        self.status('Adding filesystem bits')
        image.fileSystemOddsNEnds()

        self.status('Creating root file system')
        image.createFileSystem()

        self.status('Running tag-scripts')
        image.runTagScripts()

        self.status('Making image bootable')
        image.makeBootable()

        return [(fn, 'Bootable Qemu Image')]
