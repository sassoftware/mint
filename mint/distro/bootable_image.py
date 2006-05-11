#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

# python standard library imports
import errno
from math import ceil
import os
import sys
import re
import pwd
import time
import tempfile
import zipfile

# mint imports
from mint import mint_error
from mint import releasetypes
from mint.distro import gencslist
from mint.distro.imagegen import ImageGenerator, MSG_INTERVAL
from mint.client import upstream

# conary imports
from conary import conaryclient
from conary import flavorcfg
from conary import versions
from conary.callbacks import ChangesetCallback
from conary.conarycfg import ConfigFile, CfgDict, CfgString, CfgBool
from conary.callbacks import UpdateCallback
from conary.conaryclient.cmdline import parseTroveSpec
from conary.deps import deps
from conary.lib import log, util
from conary.repository import errors

PARTITION_OFFSET = 512

class KernelTroveRequired(mint_error.MintError):
    def __str__(self):
        return "Your group must include a kernel for proper operation."


class BootableImageConfig(ConfigFile):
    filename = 'bootable_image.conf'

    #Different cylinder sizes.  I don't know which is better, but I've seen
    #both: 8225280 or 516096
    cylindersize    = 516096
    sectors         = 63
    heads           = 16

    #directory containing the uml init script as well as fstab and other hooks
    dataDir         = '/usr/share/mint/DiskImageData/'
    umlKernel       = CfgDict(CfgString)
    debug           = (CfgBool, 0)

    # where to look for tools needed to boot a live ISO.
    fallbackDir     = '/srv/rbuilder/fallback'
    toolkitImage     = '/srv/rbuilder/toolkit/image_maker.img'

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
        cmd = '/sbin/sfdisk -C %d -S %d -H %d %s' % (self.cylinders, self.imgcfg.sectors, self.imgcfg.heads, self.outfile)
        input = "0 %d L *\n" % self.cylinders

        if not self.imgcfg.debug:
            cmd += " >& /dev/null"
        sfdisk = util.popen(cmd, 'w')
        sfdisk.write(input)
        retval = sfdisk.close()

    def _writefstab(self):
        util.copyfile(os.path.join(self.imgcfg.dataDir, 'fstab'), os.path.join(self.fakeroot, 'etc'))
        if not self.swapSize:
            # remove any reference to swap if swapSize is 0
            util.execute('sed -i "s/.*swap.*//" %s' % \
                         os.path.join(self.fakeroot, 'etc', 'fstab'))

    def _setupGrub(self):
        if not os.path.exists(os.path.join(self.fakeroot, 'sbin', 'grub')):
            log.info("grub not found. skipping setup.")
            return
        util.copytree(os.path.join(self.fakeroot, 'usr', 'share', 'grub', '*', '*'), os.path.join(self.fakeroot, 'boot', 'grub'))
        #Create a stub grub.conf
        name = open(os.path.join(self.fakeroot, 'etc', 'issue'), 'r').readlines()[0].strip()
        # make initrd line in grub conf contingent on actually having one.
        macros = {'name': name, 'kversion': 'template', 'initrdCmd' : ''}
        bootDirFiles = os.listdir(os.path.join(self.fakeroot, 'boot'))
        if [x for x in bootDirFiles if re.match('initrd-.*.img', x)]:
            macros['initrdCmd'] = 'initrd /boot/initrd-%(kversion)s.img'
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
    %(initrdCmd)s

""" % macros % macros) # repeated to cover recursive nature of initrdCmd
        fd.close()
        os.chmod(os.path.join(self.fakeroot, 'boot/grub/grub.conf'), 0600)
        #create the appropriate links
        os.symlink('grub.conf', os.path.join(self.fakeroot, 'boot', 'grub', 'menu.lst'))
        os.symlink('../boot/grub/grub.conf', os.path.join(self.fakeroot, 'etc', 'grub.conf'))

    def findFile(self, baseDir, fileName):
        for base, dirs, files in os.walk(baseDir):
            matches = [x for x in files if re.match(fileName, x)]
            if matches:
                print >> sys.stderr, "match found for %s" % \
                      os.path.join(base, matches[0])
                return os.path.join(base, matches[0])
        return None

    @timeMe
    def createTemporaryRoot(self, basedir = os.getcwd()):
        cwd = os.getcwd()
        os.chdir(self.fakeroot)
        util.mkdirChain('etc', 'etc/sysconfig',
            'etc/sysconfig/network-scripts',
            'boot/grub', 'tmp', 'sys', 'root')
        os.chdir(cwd)

    @timeMe
    def setupConaryClient(self):
        self.conarycfg.threaded = True
        self.conarycfg.root = self.fakeroot
        self.conarycfg.dbPath = '/var/lib/conarydb'
        self.conarycfg.installLabelPath = None
        self.readConaryRc(self.conarycfg)

        self.cclient = conaryclient.ConaryClient(self.conarycfg)

    @timeMe
    def updateGroupChangeSet(self, callback):
        itemList = [(self.basetrove, (None, None), (self.baseversion, self.baseflavor), True)]
        log.info("itemList: %s" % str(itemList))

        repos = self.cclient.getRepos()
        parentGroup = repos.getTroves([(self.basetrove, versions.VersionFromString(self.baseversion), self.baseflavor)])[0]

        uJob, _ = self.cclient.updateChangeSet(itemList,
            resolveDeps = False, split = True, callback = callback)
        return uJob

    @timeMe
    def applyUpdate(self, uJob, callback, tagScript):
        self.cclient.applyUpdate(uJob, journal = Journal(), callback = callback,
                tagScript=os.path.join(self.fakeroot, 'root', tagScript))

    @timeMe
    def updateKernelChangeSet(self, callback):
        #Install the Kernel
        try:
            # since sync = True, this will sync up to the kernel requested by the group.
            kernel, version, flavor = parseTroveSpec('kernel:runtime[!kernel.smp is: %s]' % self.arch)
            itemList = [(kernel, (None, None), (version, flavor), True)]
            uJob, suggMap = self.cclient.updateChangeSet(itemList, sync = True,
                                callback = callback, split = True,
                                resolveDeps = False)
        except errors.TroveNotFound:
            raise KernelTroveRequired
        return uJob

    @timeMe
    def populateTemporaryRoot(self, callback = None):
        uJob = self.updateGroupChangeSet(callback)
        self.applyUpdate(uJob, callback, 'conary-tag-script')
        if self.findFile(os.path.join(self.fakeroot, 'boot'), 'vmlinuz.*'):
            log.info("kernel detected. skipping updateKernelChangeSet")
            return
        try:
            kuJob = self.updateKernelChangeSet(callback)
        except conaryclient.NoNewTrovesError:
            log.info("strongly-included kernel found--no new kernel trove to sync")
        except KernelTroveRequired:
            log.info("no kernel found at all. skipping.")
        else:
            self.applyUpdate(kuJob, callback, 'conary-kernel-tag-script')

    @timeMe
    def fileSystemOddsNEnds(self):
        #write the fstab
        self._writefstab()
        #create a swap file
        if self.swapSize:
            swap = open(os.path.join(self.fakeroot, 'var', 'swap'), 'w')
            swap.seek(self.swapSize - 1)
            swap.write('\x00')
            swap.close()
            #Initialize the swap file
            cmd = '/sbin/mkswap %s' % \
                  os.path.join(self.fakeroot, 'var', 'swap')
            util.execute(cmd)
        #copy the files needed by grub and set up the links
        self._setupGrub()
        #Create the init script
        util.copyfile(os.path.join(self.imgcfg.dataDir, 'init.sh'), os.path.join(self.fakeroot, 'tmp'))
        os.chmod(os.path.join(self.fakeroot, 'tmp', 'init.sh'), 0755)
        util.copyfile(os.path.join(self.imgcfg.dataDir, 'pre-tag-scripts'), os.path.join(self.fakeroot, 'root'))
        util.copyfile(os.path.join(self.imgcfg.dataDir, 'post-tag-scripts'), os.path.join(self.fakeroot, 'root'))
        util.copyfile(os.path.join(self.imgcfg.dataDir, 'post-kernel-tag-scripts'), os.path.join(self.fakeroot, 'root'))
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
        silence = ''
        if not self.imgcfg.debug:
            flags += ' -v'
            silence = ' >& /dev/null'
        # XXX Hack to work around weird permissions that e2fsimage fails to handle:
        util.execute("find %s -perm 0111 -exec chmod u+r {} \;" % self.fakeroot)

        cmd = '/usr/bin/e2fsimage -f %s -d %s -s %d %s %s' % (file,
                self.fakeroot, (self.imagesize - PARTITION_OFFSET)/1024,
                flags, silence)
        util.execute(cmd)
        cmd = '/sbin/e2label %s / %s' % (file, silence)
        util.execute(cmd)
        if self.addJournal:
            cmd = '/sbin/tune2fs -i 0 -c 0 -j %s %s' % (file, silence)
        else:
            cmd = '/sbin/tune2fs -i 0 -c 0 %s %s' % (file, silence)
        util.execute(cmd)

    @outputfilesize
    @timeMe
    def WriteBack(self, file):
        #Now write this FS image back to the original image
        fd = open(file, 'rb')
        fdo = open(self.outfile, 'r+b')
        fdo.seek(PARTITION_OFFSET)
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
            size += self.freespace + PARTITION_OFFSET
            # account for inodes and extra space for tag scripts and swap space
            # inodes are 8%.
            # super user reserved blocks are 5% of total
            # swap defaults to 128MB
            # tag scripts swag is 20MB
            size = int(ceil((size + 20 * 1024 * 1024 + self.swapSize) / 0.87))
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
    def createSparseFile(self, size=10240):
        # size is defined in terms of megabytes
        fd, tmpFile = tempfile.mkstemp()
        os.close(fd)
        os.system('dd if=/dev/zero of=%s count=1 seek=%d bs=1M >/dev/null' % \
                  (tmpFile, size))
        return tmpFile

    @timeMe
    def estimateSize(self, fileName):
        "find real size of contents of sparse file by ignoring trailing nulls."
        # this function will fail if the file truly has trailing nulls.
        f = os.popen('du --block-size=1 %s' % fileName)
        upperSize = int(f.read().strip().split()[0])
        f.close()
        f = open(fileName)
        # iteratively back up in 1MB chunks until it appears to be within file
        lowerSize = max(upperSize - 1024 * 1024, 0)
        while lowerSize:
            f.seek(lowerSize)
            c = f.read(1)
            if c == chr(0) or c == '':
                lowerSize = max(lowerSize - 1024 * 1024, 0)
            else:
                break
        try:
            while True:
                estimatedSize = lowerSize + (upperSize - lowerSize) / 2
                sizeDiff = upperSize - estimatedSize
                f.seek(estimatedSize)
                buf = f.read(sizeDiff)
                if buf == len(buf) * chr(0):
                    # we are past the end of the file
                    upperSize = estimatedSize
                else:
                    if sizeDiff == 1:
                        estimatedSize = upperSize
                        break
                    # we're not pointing at the end of the file
                    lowerSize = estimatedSize
        finally:
            f.close()
        # size is in bytes
        return estimatedSize

    @timeMe
    def copySparse(self, src, dest):
        # overcome the apparent size of a sparse file. this would fail if there
        # were holes in the src file, but there shouldn't be any.
        f = os.popen('file %s' % src)
        fileType = f.read()
        f.close()
        if 'gzip compressed data' in fileType:
            # per RFC 1952: GZIP file format specification version 4.3
            # the last 8 bytes of gzip file are 32 bit CRC and 32 bit orig len.
            # for estimateSize to fail horribly, the uncompressed tarball would
            # need to be an exact multiple of 4GB and an all-zero CRC.
            # however gzip will complain if we truncate inadverdently.
            # HACK: we add 8 bytes to the esitmated size to virtually nullify
            # the chance of losing real data. gzip ignores trailing zeroes
            # this has a side effect of making gzip -l report orig size as 0
            size = self.estimateSize(src) + 8
            util.execute('head -c %d %s > %s' % (size, src, dest))
            return size
        else:
            fd = os.popen('/usr/bin/isosize %s' % src)
            size = int(fd.read().strip().split()[0])
            fd.close()
            size = size // 2048 + bool(size % 2048)
            # use dd to limit size. no python libs seem to do this correctly
            os.system('dd if=%s of=%s count=%d ibs=2048' % (src, dest, size))
            return size * 2048

    @timeMe
    def runTagScripts(self, target = 'ext3'):
        if target == 'ext3':
            cmd = '%s root=/dev/ubda1 init=/tmp/init.sh ubd0=%s' % \
                  (self.imgcfg.umlKernel[self.arch], self.outfile)
            if not self.imgcfg.debug:
                cmd += " > /dev/null"
            # uml-kernel sometimes returns spurious error codes on exit
            os.system(cmd)
        else:
            # use a wrapper image to run tagscripts and re-export image in a
            # new filesystem format...
            tmpFile = self.createSparseFile()
            cmd = '%s root=/dev/ubda1 init=/sbin/target_inits/%s_init.sh ' \
                  'ubd0=%s ubd1=%s ubd2=%s' % \
                  (self.imgcfg.umlKernel[self.arch], target,
                   self.imgcfg.toolkitImage, self.outfile, tmpFile)
            if target == 'zisofs':
                # some targets require a work partition. size is in MB
                fd = os.popen('/usr/bin/du -B1048576 -s %s' % \
                              self.outfile, 'r')
                # double the source partition size should be more than enough,
                # but cap it at 10 GB... unless more is really needed.
                size = int(fd.read().strip().split()[0])
                size = max(size, min(size * 2, 10240))
                fd.close()
                tmpFile2 = self.createSparseFile(size)
                cmd += ' ubd3=%s' % tmpFile2
            if not self.imgcfg.debug:
                cmd += " > /dev/null"
            # uml-kernel sometimes returns spurious error codes on exit
            os.system(cmd)
            if target == 'zisofs':
                os.unlink(tmpFile2)
            # and move the output filesystem image back into place
            os.unlink(self.outfile)
            # be very wary of taking out or replacing this call,
            # it keeps the output image from ballooning to 10GB
            log.info("copySparse: copied %d bytes" % \
                  self.copySparse(tmpFile, self.outfile))

    @timeMe
    def makeBootBlock(self):
        if not self.makeBootable:
            return
        if not os.path.exists(os.path.join(self.fakeroot, 'sbin', 'grub')):
            log.info("grub not found. skipping execution.")
            return
        #install boot manager
        cmd = '%s --device-map=/dev/null --batch' % os.path.join(self.fakeroot, 'sbin', 'grub')
        input = """
device  (hd0)   %s
root    (hd0,0)
setup   (hd0)
quit
""" % self.outfile

        if not self.imgcfg.debug:
            cmd += " > /dev/null"
        uml = util.popen(cmd, 'w')
        uml.write(input)
        retval = uml.close()

    @timeMe
    def stripBootBlock(self):
        tempName = self.outfile + "nonstrip"
        # move outfile out of the way, then copy it back, minus boot block.
        os.rename(self.outfile, tempName)
        blocks = PARTITION_OFFSET / 512
        os.system('dd if=%s of=%s skip=%d ibs=512' % \
                  (tempName, self.outfile, blocks))
        os.unlink(tempName)

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
        isogenUid = os.geteuid()
        apacheGid = pwd.getpwnam('apache')[3]
        os.chown(finaldir, isogenUid, apacheGid)
        for file, name in filelist:
            base, ext = os.path.basename(file).split(os.path.extsep, 1)
            newfile = os.path.join(finaldir, self.basefilename + "." + ext)
            log.info("Move %s to %s" % (file, newfile))

            import gencslist
            gencslist._linkOrCopyFile(file, newfile)
            os.unlink(file)
            os.chown(newfile, isogenUid, apacheGid)
            returnlist.append((newfile, name,))
        return returnlist

    def createFileTree(self):
        #Create the output file:
        fd, self.outfile = tempfile.mkstemp('.img', 'raw_hd',
                                            self.cfg.imagesPath)
        os.close(fd)
        os.chmod(self.outfile, 0644)

        callback = InstallCallback(self.status)

        self.setupConaryClient()
        self.status('Creating temporary root')
        self.createTemporaryRoot()

        self.status('Installing software')
        self.populateTemporaryRoot(callback)

        self.status('Populating configuration files')
        self.fileSystemOddsNEnds()

    def createImage(self, target = 'ext3'):
        self.status('Creating root file system')
        self.createFileSystem(self.cfg.imagesPath)

        self.status('Running tag-scripts')
        self.runTagScripts(target = target)

        if self.makeBootable:
            self.status('Making image bootable')
            self.makeBootBlock()
        else:
            # don't try and strip boot blocks from iso images.
            if target in ('ext3', 'ext2'):
                self.stripBootBlock()

        #As soon as that's done, we can delete the fakeroot to free up space
        util.rmtree(self.fakeroot)
        self.fakeroot = None

    def __init__(self, client, cfg, job, release, project):
        ImageGenerator.__init__(self, client, cfg, job, release, project)
        # set default options for all bootable image types
        self.imgcfg = self.getConfig()
        self.addJournal = True
        self.makeBootable = True

        #Create the directory to use as the root for the conary commands
        self.fakeroot = tempfile.mkdtemp("", "imagetool", self.cfg.imagesPath)
        log.info('generating raw hd image with tmpdir %s', self.fakeroot)

        #Figure out what group trove to use
        self.basetrove, versionStr, flavorStr = self.release.getTrove()
        log.info('self.release.getTrove returned (%s, %s, %s)' % \
                 (self.basetrove, versionStr, flavorStr))

        #Thaw the version string
        version = versions.ThawVersion(versionStr)
        self.baseversion = version.asString()

        #Thaw the flavor string
        self.baseflavor = deps.ThawDependencySet(flavorStr)

        # set up configuration
        self.conarycfg = self.project.getConaryConfig()

        self.arch = self.release.getArch()
        basefilename = "%(name)s-%(version)s-%(arch)s" % {
                'name': self.project.getHostname(),
                'version': upstream(version),
                'arch': self.arch,
            }

        #initialize some stuff
        self.basefilename = basefilename

    def write(self):
        raise NotImplementedError
