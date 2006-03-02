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
import zipfile

# mint imports
from imagegen import ImageGenerator, MSG_INTERVAL
import gencslist
from mint import releasetypes
from mint.mint import upstream

# conary imports
from conary import conaryclient
from conary import deps
from conary import flavorcfg
from conary import versions
from conary.conaryclient.cmdline import parseTroveSpec
from conary.repository import errors
from conary.callbacks import UpdateCallback
from conary.callbacks import ChangesetCallback
from conary.conarycfg import ConfigFile, CfgDict, CfgString, CfgBool
from conary.lib import log, util, epdb

class BootableImageConfig(ConfigFile):
    filename = 'bootable_image.conf'

    #Different cylinder sizes.  I don't know which is better, but I've seen
    #both: 8225280 or 516096
    cylindersize    = 516096
    sectors         = 63
    heads           = 16

    #Offset at which to drop the file system in the raw disk image
    partoffset0     = 512

    #directory containing the uml init script as well as fstab and other hooks
    dataDir         = '/usr/share/mint/DiskImageData/'
    umlKernel       = CfgDict(CfgString)
    debug           = (CfgBool, 0)

def debugme(type, value, tb):
    from conary.lib import epdb
    epdb.post_mortem(tb,type,value)

class Journal:
    def lchown(self, root, target, user, group):
        # put UIDGID entries for directories on .
        if os.path.isdir(target):
            target = target[len(root):]
            filename = '.'
            f = open(os.sep.join((root, target, '.UIDGID')), 'a')
        else:
            # get rid of the root
            target = target[len(root):]
            dirname = os.path.dirname(target)
            filename = os.path.basename(target)
            f = open(os.sep.join((root, dirname, '.UIDGID')), 'a')
        trfilename = filename.replace(' ', r'\ ').replace('\t', r'\t')
        f.write('%s %s %s\n' %(trfilename, user, group))
        f.close()

    def mknod(self, root, target, devtype, major, minor, mode,
              uid, gid):
        # get rid of the root
        target = target[len(root):]
        dirname = os.path.dirname(target)
        filename = os.path.basename(target)
        f = open(os.sep.join((root, dirname, '.DEVICES')), 'a')
        # XXX e2fsimage does not handle symbolic users/groups for .DEVICES
        # But this doesn't matter as .UIDGID is processed after .DEVICES
        trfilename = filename.replace(' ', r'\ ').replace('\t', r'\t')
        f.write('%s %s %d %d 0%o\n' %(trfilename, devtype, major, minor, mode))
        f.close()

def timeMe(func):
    def wrapper(self, *args, **kwargs):
        clock = time.clock()
        actual = time.time()
        returner = func(self, *args, **kwargs)
        log.info("%s: %.5f %.5f" % (func.__name__, time.clock() - clock, time.time() - actual))
        return returner
    return wrapper

def outputfilesize(func):
    def wrapper(self, *args, **kwargs):
        returner = func(self, *args, **kwargs)
        st = os.stat(self.outfile)
        log.debug("size of %s after %s: %d bytes" % (self.outfile, func.__name__, st.st_size))
        return returner
    return wrapper


class InstallCallback(UpdateCallback, ChangesetCallback):
    def restoreFiles(self, size, totalSize):
        if totalSize != 0:
            self.restored += size
            self.update('Writing files')

    def requestingChangeSet(self):
        self.update('Requesting changeset')

    def downloadingChangeSet(self, got, need):
        if need != 0:
            self.update('Downloading changeset')

    def requestingFileContents(self):
        self.update('Requesting file contents')

    def downloadingFileContents(self, got, need):
        if need != 0:
            self.update('Downloading files')

    def preparingChangeSet(self):
        self.update('Preparing changeset')

    def resolvingDependencies(self):
        self.update('Resolving dependencies')

    def creatingRollback(self):
        self.update('Creating rollback')

    def creatingDatabaseTransaction(self, troveNum, troveCount):
        self.update('Creating database transaction')

    def committingTransaction(self):
        self.update('Committing transaction')

    def setUpdateHunk(self, num, total):
        self.updateHunk = (num, total)
        self.restored = 0

    def update(self, msg):
        curTime = time.time()
        # only push an update into the database if it differs from the
        # current message
        if self.updateHunk[1] != 0:
            percent = (self.updateHunk[0] * 100) / self.updateHunk[1]
            msg = "Updating changesets: %d%% (%s)" % (percent, msg)

        if self.msg != msg and (curTime - self.timeStamp) > MSG_INTERVAL:
            self.msg = msg
            self.status(msg)
            self.timeStamp = curTime

    def __init__(self, status):
        self.abortEvent = None
        self.status = status
        self.restored = 0
        self.updateHunk = (0, 0)
        self.msg = ''
        self.changeset = ''
        self.prefix = 'BDI:'
        self.timeStamp = 0

class BootableImage(ImageGenerator):
    configObject = BootableImageConfig

    @outputfilesize
    @timeMe
    def prepareDiskImage(self):
        #create the disk file this will blank the file if it exists.
        ofile = open(self.outfile, 'wb', 0644)
        ofile.seek(self.imagesize-1)
        ofile.write('\x00')
        ofile.close()

        #Do the partition table
        self.cylinders = self.imagesize / self.imgcfg.cylindersize
        cmd = '/sbin/sfdisk -C %d -S %d -H %d %s > /dev/null' % (self.cylinders, self.imgcfg.sectors, self.imgcfg.heads, self.outfile)
        input = "0 %d L *\n" % (self.cylinders)
        sfdisk = util.popen(cmd, 'w')
        sfdisk.write(input)
        retval = sfdisk.close()

    def _writefstab(self):
        util.copyfile(os.path.join(self.imgcfg.dataDir, 'fstab'), os.path.join(self.fakeroot, 'etc'))

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
timeout=0
title %(name)s (%(kversion)s)
    root (hd0,0)
    kernel /boot/vmlinuz-%(kversion)s ro root=LABEL=/ quiet
    initrd /boot/initrd-%(kversion)s.img

""" % {'name': name, 'kversion': 'somesillyversion'})
        fd.close()
        os.chmod(os.path.join(self.fakeroot, 'boot/grub/grub.conf'), 0600)
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
        util.mkdirChain( 'etc', 'etc/sysconfig', 'etc/sysconfig/network-scripts', 'boot/grub', 'tmp', 'sys' )
        os.chdir(cwd)

    @timeMe
    def setupConaryClient(self):
        #Create a ConaryClient
        if self.conarycfg is None:
            self.conarycfg = conarycfg.ConaryConfiguration(readConfigFiles=False)
            self.conarycfg.repositoryMap = self.repoMap
            self.conarycfg.flavor = None
            self.readConaryRc(self.conarycfg)
            #TODO Add the user if anonymous access is not available

        self.conarycfg.threaded = False
        self.conarycfg.setValue('root', self.fakeroot)
        self.conarycfg.installLabelPath = None
        self.conarycfg.dbPath = '/var/lib/conarydb/'

        self.cclient = conaryclient.ConaryClient(self.conarycfg)

    @timeMe
    def updateGroupChangeSet(self, callback):
        try:
            itemList = [(self.basetrove, (None, None), (self.baseversion, self.baseflavor), True)]
            log.info("itemList: %s" % str(itemList))
            sys.stderr.flush()
            uJob, suggMap = self.cclient.updateChangeSet(itemList,
                                    resolveDeps = False,
                                    split = True,
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
                                callback = callback, split=True,
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
        try:
            uJob = self.updateKernelChangeSet(callback)
            self.applyKernelUpdate(uJob, callback)
        except conaryclient.NoNewTrovesError:
            log.info("kernel already installed--skipping manual kernel install step")


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
        util.copyfile(os.path.join(self.imgcfg.dataDir, 'init.sh'), os.path.join(self.fakeroot, 'tmp'))
        os.chmod(os.path.join(self.fakeroot, 'tmp', 'init.sh'), 0755)
        util.copyfile(os.path.join(self.imgcfg.dataDir, 'pre-tag-scripts'), os.path.join(self.fakeroot, 'tmp'))
        util.copyfile(os.path.join(self.imgcfg.dataDir, 'post-tag-scripts'), os.path.join(self.fakeroot, 'tmp'))
        util.copyfile(os.path.join(self.imgcfg.dataDir, 'post-kernel-tag-scripts'), os.path.join(self.fakeroot, 'tmp'))
        #Write the conaryrc file
        self.writeConaryRc(os.path.join(self.fakeroot, 'etc'), self.cclient)

        #Add the other miscellaneous files needed
        util.copyfile(os.path.join(self.imgcfg.dataDir, 'hosts'), os.path.join(self.fakeroot, 'etc'))
        util.copyfile(os.path.join(self.imgcfg.dataDir, 'network'), os.path.join(self.fakeroot, 'etc', 'sysconfig'))
        util.copyfile(os.path.join(self.imgcfg.dataDir, 'ifcfg-eth0'), os.path.join(self.fakeroot, 'etc', 'sysconfig', 'network-scripts'))
        util.copyfile(os.path.join(self.imgcfg.dataDir, 'keyboard'), os.path.join(self.fakeroot, 'etc', 'sysconfig'))
        #Was X installed?
        if os.path.isfile(os.path.join(self.fakeroot, 'usr', 'bin', 'X11', 'X')):
            #copy in the xorg.conf file
            util.copyfile(os.path.join(self.imgcfg.dataDir, 'xorg.conf'), os.path.join(self.fakeroot, 'etc', 'X11'))
            #tweak the inittab to start at level 5
            cmd = r"/bin/sed -e 's/^\(id\):[0-6]:\(initdefault:\)$/\1:5:\2/' -i %s" % os.path.join(self.fakeroot, 'etc', 'inittab')
            util.execute(cmd)
        #GPM?
        if os.path.isfile(os.path.join(self.fakeroot, 'usr', 'sbin', 'gpm')):
            util.copyfile(os.path.join(self.imgcfg.dataDir, 'mouse'), os.path.join(self.fakeroot, 'etc', 'sysconfig'))

    @timeMe
    def MakeE3FsImage(self, file):
        flags = ''
        if self.imgcfg.debug:
            flags += ' -v'
        # XXX Hack to work around weird permissions that e2fsimage fails to handle:
        util.execute("find %s -perm 0111 -exec chmod u+r {} \;" % self.fakeroot)

        cmd = '/usr/bin/e2fsimage -f %s -d %s -s %d %s' % (file,
                self.fakeroot, (self.imagesize - self.imgcfg.partoffset0)/1024,
                flags)
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
        fdo.seek(self.imgcfg.partoffset0)
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
            size += self.freespace + self.imgcfg.partoffset0
            padding = self.imgcfg.cylindersize - (size % self.imgcfg.cylindersize)
            if self.imgcfg.cylindersize == padding:
                padding = 0
            self.imagesize = size + padding
            self.MakeE3FsImage(file)
            self.prepareDiskImage()
            self.WriteBack(file)
        finally:
            os.unlink(file)

    @timeMe
    def runTagScripts(self):
        cmd = '%s root=/dev/ubda1 init=/tmp/init.sh mem=128M ubd0=%s' % (self.imgcfg.umlKernel[self.arch], self.outfile)
        util.execute(cmd)

    @timeMe
    def makeBootable(self):
        #install boot manager
        cmd = '%s --device-map=/dev/null --batch' % os.path.join(self.fakeroot, 'sbin', 'grub')
        input = """
device  (hd0)   %s
root    (hd0,0)
setup   (hd0)
quit
""" % self.outfile
        uml = util.popen(cmd, 'w')
        uml.write(input)
        retval = uml.close()

    @timeMe
    def compressImage(self, filename):
        outfile = filename + '.gz'
        cmd = '/bin/gzip -c %s > %s' % (filename, outfile)
        util.execute(cmd)
        return outfile

    @timeMe
    def moveToFinal(self, filelist, finaldir):
        returnlist = []
        util.mkdirChain( finaldir )
        for file, name in filelist:
            base, ext = os.path.basename(file).split(os.path.extsep, 1)
            newfile = os.path.join(finaldir, self.basefilename + "." + ext)
            log.info("Move %s to %s" % (file, newfile))

            import gencslist
            gencslist._linkOrCopyFile(file, newfile)
            os.unlink(file)
            returnlist.append((newfile, name,))
        return returnlist

    def createFileTree(self):
        self.imgcfg = self.getConfig()

        #Create the output file:
        fd, self.outfile = tempfile.mkstemp('.img', 'qemuimg',
                                            self.cfg.imagesPath)
        os.close(fd)
        os.chmod(self.outfile, 0644)

        #Create the directory to use as the root for the conary commands
        self.fakeroot = tempfile.mkdtemp("", "imagetool", self.cfg.imagesPath)
        log.info('generating qemu image with tmpdir %s', self.fakeroot)

        #Figure out what group trove to use
        self.basetrove, versionStr, flavorStr = self.release.getTrove()
        log.info('self.release.getTrove returned (%s, %s, %s)' % \
                 (self.basetrove, versionStr, flavorStr))

        #Thaw the version string
        version = versions.ThawVersion(versionStr)
        self.baseversion = version.asString()

        #Thaw the flavor string
        self.baseflavor = deps.deps.ThawDependencySet(flavorStr)

        # set up configuration
        self.conarycfg = self.project.getConaryConfig(overrideSSL=True,
                                                      useSSL=self.cfg.SSL)
        # turn off threading

        self.arch = self.release.getArch()
        freespace = self.release.getDataValue("freespace")
        basefilename = "%(name)s-%(version)s-%(arch)s" % {
                'name': self.project.getHostname(),
                'version': upstream(version),
                'arch': self.arch,
            }

        #initialize some stuff
        self.basefilename = basefilename
        self.freespace = freespace * 1024 * 1024

        callback = InstallCallback(self.status)

        self.setupConaryClient()
        self.status('Creating temporary root')
        self.createTemporaryRoot()

        #Don't need status here.  It's very fast
        self.setupConaryClient()

        self.status('Installing software')
        self.populateTemporaryRoot(callback)

        self.status('Installing %s kernel' % self.arch)
        self.installKernel(callback)

        self.status('Adding filesystem bits')
        self.fileSystemOddsNEnds()

    def createImage(self):
        self.status('Creating root file system')
        self.createFileSystem(self.cfg.imagesPath)

        self.status('Running tag-scripts')
        self.runTagScripts()

        self.status('Making image bootable')
        self.makeBootable()

        #As soon as that's done, we can delete the fakeroot to free up space
        util.rmtree(self.fakeroot)
        self.fakeroot = None

    def write(self):
        raise NotImplementedError
