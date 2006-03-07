#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

# python standard library imports
import os, sys
import tempfile
import subprocess
import re

# mint imports
from imagegen import ImageGenerator, MSG_INTERVAL
import bootable_image

# conary imports
from conary import conaryclient
from conary import deps
from conary import flavorcfg
from conary import versions
from conary.callbacks import UpdateCallback, ChangesetCallback
from conary.conarycfg import ConfigFile
from conary.lib import log, util, epdb

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
        curTime = time.time()
        if self.msg != msg and (curTime - self.timeStamp) > MSG_INTERVAL:
            self.msg = msg
            self.status(self.prefix + msg % self.changeset)
            self.timeStamp = curTime

    def __init__(self, status):
        self.status = status
        self.restored = 0
        self.msg = ''
        self.timeStamp = 0


devices = """loop0 b 7 0 0660
console c 5 1 0660
null c 1 3 0660
zero c 1 5 0660
systty c 4 0 0660
tty1 c 4 1 0660
tty2 c 4 2 0660
tty3 c 4 3 0660
tty4 c 4 4 0660"""

linuxrc = """#!/bin/nash
mount -t proc /proc /proc/
echo Mounted /proc
echo Mounting sysfs
mount -t sysfs none /sys
echo Creating /dev
mount -o mode=0755 -t tmpfs /dev /dev

echo Creating block devices
%(devices)s
mkdir /dev/pts
mkdir /dev/shm

%(modules)s
%(udev)s

### REVIEW THIS LINE ###
echo 0x0100 > /proc/sys/kernel/real-root-dev
### END REVIEW ###

# FIXME: this must be dymanic
echo Mounting CD-ROM
mount -o mode=0644 --ro -t iso9660 /dev/hdc /cdrom
%(mountCmd)s
echo Running pivot_root
pivot_root /sysroot /sysroot/initrd
umount /initrd/proc
"""

isolinuxCfg="""label linux
  kernel vmlinuz
  append initrd=initrd.img
"""

class LiveIso(bootable_image.BootableImage):
    def findFile(self, baseDir, fileName):
        for base, dirs, files in os.walk(baseDir):
            matches = [x for x in files if re.match(fileName, x)]
            if matches:
                print >> sys.stderr, "match found for %s" % os.path.join(base, matches[0])
                return os.path.join(base, matches[0])
        return None

    def copyFallback(self, src, dest):
        tFile = os.path.basename(src)
        pFile = os.popen('file %s' % src)
        fileStr = pFile.read()
        pFile.close()
        fallback = not ('statically' in fileStr or \
                        fileStr.endswith(': data\n'))
        if fallback:
            print >> sys.stderr, "Using fallback for: %s" % tFile
            # executable is dynamically linked, use precompiled static one
            util.copyfile(os.path.join(self.fallback, tFile), dest)
        else:
            print >> sys.stderr, "Using user defined: %s" % tFile
            util.copyfile(src, dest)
        return not fallback

    def mkinitrd(self):
        # this is where we'll create the initrd image
        initRdDir = tempfile.mkdtemp()
        macros = {'modules' : 'echo Inserting Kernel Modules',
                  'udev' : '',
                  'devices' : '',
                  'mountCmd': ''}

        for subDir in ('bin', 'dev', 'lib', 'proc', 'sys', 'sysroot',
                       'etc', os.path.join('etc', 'udev'), 'cdrom'):
            os.mkdir(os.path.join(initRdDir, subDir))

        # soft link sbin to bin
        os.symlink('bin', os.path.join(initRdDir, 'sbin'))

        # set up the binaries to copy into new filesystem.
        binaries = ('nash', 'insmod')
        if self.release.getDataValue('udev'):
            binaries += ('udev', 'udevstart')

            # copy the udev config file
            util.copyfile(os.path.join(self.fakeroot, 'etc', 'udev',
                                       'udev.conf'),
                          os.path.join(initRdDir, 'etc', 'udev', 'udev.conf'))

        # copy binaries from fileSystem image to initrd
        for tFile in binaries:
            self.copyFallback(os.path.join(self.fakeroot, 'sbin', tFile),
                              os.path.join(initRdDir, 'bin', tFile))
            os.chmod(os.path.join(initRdDir, 'bin', tFile), 0755) # octal 755

        # soft link modprobe and hotplug to nash: keeps udev from being psycho
        for tFile in ('modprobe', 'hotplug'):
            os.symlink('/sbin/nash', os.path.join(initRdDir, 'bin', tFile))

        kMods = ('loop',)
        if self.release.getDataValue('unionfs'):
            kMods += ('unionfs',)
        for modName in kMods:
            modName += '.ko'
            # copy loop.ko module into intird
            modPath = self.findFile( \
            os.path.join(self.fakeroot, 'lib', 'modules'), modName)
            if modPath:
                util.copyfile(modPath, os.path.join(initRdDir, 'lib', modName))
                macros['modules'] += '\n/bin/insmod /lib/%s' % modName
            else:
                raise AssertionError('Missing required Module: %s' % modName)

        # make .DEVICES file
        f = open(os.path.join(initRdDir, 'dev', '.DEVICES'), 'w')
        f.write(devices)
        f.close()

        if self.release.getDataValue('udev'):
            macros['udev'] ="""echo Starting udev
/sbin/udevstart"""
        else:
            macros['devices'] = '\n'.join( \
            ['mknod /dev/' + ' '.join(x.split()[:-1]) \
             for x in devices.split('\n')])

        if self.release.getDataValue('unionfs'):
            macros['mountCmd'] = """echo Making system mount points
mkdir /sysroot1
mkdir /sysroot2

echo Mounting root filesystem
losetup --ro /dev/loop0 /cdrom/livecd.img
mount -o defaults --ro -t ext2 /dev/loop0 /sysroot1
mount -o defaults -t tmpfs /dev/shm /sysroot2
mount -o dirs=sysroot2=rw:sysroot1=ro,delete=whiteout -t unionfs none /sysroot
"""
        else:
            macros['mountCmd'] = """
echo Mounting root filesystem
losetup --ro /dev/loop0 /cdrom/livecd.img
mount -o defaults --ro -t ext2 /dev/loop0 /sysroot
"""

        # make linuxrc file
        f = open(os.path.join(initRdDir, 'linuxrc'), 'w')
        f.write(linuxrc % macros)
        f.close()
        os.chmod(os.path.join(initRdDir, 'linuxrc'), 0755) # octal 755

        nonZipped = os.path.join(self.liveDir, 'initrd.nogz')
        zippedImg = os.path.join(self.liveDir, 'initrd.img')
        util.execute('e2fsimage -v -d %s -u 0 -g 0 -f %s -s 8000' % \
                     (initRdDir, nonZipped))
        util.execute('gzip -9 < %s > %s' % (nonZipped, zippedImg))
        os.unlink(nonZipped)

        # this image is trackable from self.liveDir, but return a path to it
        return zippedImg

    def makeLiveCdTree(self):
        self.liveDir = tempfile.mkdtemp()
        # for pivotroot
        os.mkdir(os.path.join(self.liveDir, 'initrd'))

        self.mkinitrd()

        kernel = self.findFile(os.path.join(self.fakeroot, 'boot'),
                               'vmlinuz.*')
        util.copyfile(kernel, os.path.join(self.liveDir, 'vmlinuz'))

        self.copyFallback(os.path.join(self.fakeroot, 'usr', 'lib', 'syslinux',
                                       'isolinux.bin'),
                          os.path.join(self.liveDir, 'isolinux.bin'))

        f = open(os.path.join(self.liveDir, 'isolinux.cfg'), 'w')
        f.write(isolinuxCfg)
        f.close()

    def finalizeIso(self):
        # move the image into place
        util.copyfile(self.outfile, os.path.join(self.liveDir, 'livecd.img'))
        os.chmod(os.path.join(self.liveDir, 'livecd.img'), 0644) # octal 644

        # make a target and call mkisofs
        os.chdir(self.liveDir)
        fd, self.liveISO = tempfile.mkstemp('.iso', 'livecd',
                                            self.cfg.imagesPath)
        os.close(fd)
        util.execute('mkisofs -o %s -J -R -b isolinux.bin -c boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table .' % self.liveISO)
        os.chmod(self.liveISO, 0644) # octal 644

        # we'll need to zip this puppy up before shipping...

        #zippedImage = tempfile.mkstemp('.gz', os.path.basename(self.liveISO))
        #util.execute('gzip -9 < %s > %s' % (self.liveISO, zippedImg))
        # when we do put in unzip code, remember to add self.liveISO to the
        # list of things that should be cleaned up...

        return (self.liveISO, 'Live CD')

    def cleanupDirs(self):
        return
        for cDir in (self.fakeroot, self.outfile, self.liveDir):
            if cDir:
                util.rmtree(cDir)

    def write(self):
        try:
            # instantiate the contents that need to go into the image
            self.createFileTree()

            # use the filesystem tree to create the proper initrd
            self.status("Making initrd")
            self.makeLiveCdTree()

            # and instantiate the hard disk image
            self.createImage()

            # now merge them. the hard disk image must be inserted into the iso
            self.status('Finalizing image')
            imagesList = [self.finalizeIso()]
        except:
            if self.imgcfg.debug:
                epdb.post_mortem(sys.exc_info()[2])
            self.cleanupDirs()
            raise
        else:
            self.cleanupDirs()

        return self.moveToFinal(imagesList,
                                os.path.join(self.cfg.finishedPath,
                                             self.project.getHostname(),
                                             str(self.release.getId())))

    def __init__(self, *args, **kwargs):
        res = bootable_image.BootableImage.__init__(self, *args, **kwargs)
        self.outFile = None
        self.liveDir = None
        self.liveISO = None
        self.freespace = 0
        self.fallback = os.path.join(self.imgcfg.fallbackDir,
                                     self.release.getArch())
        self.addJournal = False
        # the inner image does not need to be bootable
        self.makeBootable = False
        return res
