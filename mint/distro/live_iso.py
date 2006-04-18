#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

# python standard library imports
import os, sys
import re
import subprocess
import tempfile

# mint imports
from mint.distro import bootable_image
from mint.distro.imagegen import ImageGenerator, MSG_INTERVAL

# conary imports
from conary import conaryclient
from conary import deps
from conary import flavorcfg
from conary import versions
from conary.callbacks import UpdateCallback, ChangesetCallback
from conary.conarycfg import ConfigFile
from conary.lib import log, util

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


linuxrc = """#!/bin/nash
mount -t proc /proc /proc/
mount -t sysfs none /sys
mount -o mode=0755 -t tmpfs /dev /dev

%(modules)s
/sbin/udevstart

mkrootdev /dev/root
echo 0x0100 > /proc/sys/kernel/real-root-dev

mount -o defaults --ro -t iso9660 /dev/root /cdrom
%(mountCmd)s
pivot_root /sysroot /sysroot/initrd
umount /initrd/proc
umount /initrd/sys
"""

isolinuxCfg= '\n'.join(('say Welcome to %s.',
                        'default linux',
                        'timeout 100',
                        'prompt 1',
                        'label linux',
                        'kernel vmlinuz',
                        'append initrd=initrd.img root=LABEL=%s'))


class LiveIso(bootable_image.BootableImage):
    def findFile(self, baseDir, fileName):
        for base, dirs, files in os.walk(baseDir):
            matches = [x for x in files if re.match(fileName, x)]
            if matches:
                print >> sys.stderr, "match found for %s" % os.path.join(base, matches[0])
                return os.path.join(base, matches[0])
        return None

    def iterFiles(self, baseDir, fileName):
        for base, dirs, files in os.walk(baseDir):
            for match in [x for x in files if re.match(fileName, x)]:
                yield os.path.join(base, match)

    def copyFallback(self, src, dest):
        tFile = os.path.basename(src)
        # FIXME: some of the files we actually want are there, but have -static
        # appended to their name
        pFile = os.popen('file %s' % src)
        fileStr = pFile.read()
        pFile.close()
        fallback = not ('statically' in fileStr or \
                        fileStr.endswith(': data\n'))
        if fallback:
            print >> sys.stderr, "Using fallback for: %s" % tFile
            # named executable isn't suitable, use precompiled static one
            util.copyfile(os.path.join(self.fallback, tFile), dest)
        else:
            print >> sys.stderr, "Using user defined: %s" % tFile
            util.copyfile(src, dest)
        return not fallback

    def getVolName(self):
        name = self.release.getName()
        # srcub all non alphanumeric characters. we use this in a system call.
        # limit name to 32 chars--max volumne name for iso-9660
        return ''.join([x.isalnum() and x or '_' for x in name][:32])

    def mkinitrd(self):
        # this is where we'll create the initrd image
        initRdDir = tempfile.mkdtemp()
        macros = {'modules' : 'echo Inserting Kernel Modules',
                  'mountCmd': ''}

        for subDir in ('bin', 'dev', 'lib', 'proc', 'sys', 'sysroot',
                       'etc', os.path.join('etc', 'udev'), 'cdrom'):
            os.mkdir(os.path.join(initRdDir, subDir))

        # soft link sbin to bin
        os.symlink('bin', os.path.join(initRdDir, 'sbin'))

        # set up the binaries to copy into new filesystem.
        binaries = ('nash', 'insmod', 'udev', 'udevstart')
        # copy the udev config file
        util.copyfile(os.path.join(self.fakeroot, 'etc', 'udev', 'udev.conf'),
                      os.path.join(initRdDir, 'etc', 'udev', 'udev.conf'))

        # copy binaries from fileSystem image to initrd
        for tFile in binaries:
            self.copyFallback(os.path.join(self.fakeroot, 'sbin', tFile),
                              os.path.join(initRdDir, 'bin', tFile))
            os.chmod(os.path.join(initRdDir, 'bin', tFile), 0755) # octal 755

        # FIXME: remove once nash has proper losetup args in place
        print >> sys.stderr, "Forcing temporary nash fallback (for losetup)"
        util.copyfile(os.path.join(self.fallback, 'nash'),
                      os.path.join(initRdDir, 'bin', 'nash'))
        os.chmod(os.path.join(initRdDir, 'bin', 'nash'), 0755) # octal 755
        # end nash-losetup FIXME

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
                if modName == 'loop.ko':
                    macros['modules'] += '\n/bin/insmod /lib/%s max_loop=256' % modName
                else:
                    macros['modules'] += '\n/bin/insmod /lib/%s' % modName
            else:
                raise AssertionError('Missing required Module: %s' % modName)

        if self.release.getDataValue('unionfs'):
            macros['mountCmd'] = """echo Making system mount points
mkdir /sysroot1
mkdir /sysroot2

echo Mounting root filesystem
losetup --ro /dev/loop0 /cdrom/livecd.img
mount -o defaults --ro -t iso9660 /dev/loop0 /sysroot1
mount -o defaults -t tmpfs /dev/shm /sysroot2
mount -o dirs=sysroot2=rw:sysroot1=ro,delete=whiteout -t unionfs none /sysroot
"""
        else:
            macros['mountCmd'] = """
echo Mounting root filesystem
losetup --ro /dev/loop0 /cdrom/livecd.img
mount -o defaults --ro -t iso9660 /dev/loop0 /sysroot
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
        os.chmod(self.liveDir, 0755)
        # for pivotroot
        os.mkdir(os.path.join(self.liveDir, 'initrd'))

        self.mkinitrd()

        allKernels = [x for x in self.iterFiles( \
            os.path.join(self.fakeroot, 'boot'), 'vmlinuz.*')]

        if len(allKernels) > 1:
            if self.release.getDataValue('unionfs'):
                raise AssertionError("Multiple kernels detected. The most "
                                     "likely cause is a mismatch between the "
                                     "kernel in group-core and the kernel "
                                     "that unionfs was compiled for.")
            else:
                raise AssertionError("Multiple kernels detected. Please check "
                                     " that your group contains only one.")

        util.copyfile(allKernels[0], os.path.join(self.liveDir, 'vmlinuz'))

        self.copyFallback(os.path.join(self.fakeroot, 'usr', 'lib', 'syslinux',
                                       'isolinux.bin'),
                          os.path.join(self.liveDir, 'isolinux.bin'))

        f = open(os.path.join(self.liveDir, 'isolinux.cfg'), 'w')
        f.write(isolinuxCfg % (self.release.getName(), self.getVolName()))
        f.close()

        # tweaks to make read-only filesystem possible.
        if not self.release.getDataValue('unionfs'):
            util.mkdirChain(os.path.join(self.fakeroot, 'ramdisk'))
            util.mkdirChain(os.path.join(self.fakeroot, 'etc', 'sysconfig'))
            f = open(os.path.join(self.fakeroot, 'etc', 'sysconfig', 'readonly-root'), 'w')
            f.write("READONLY=yes\n")
            f.close()

    def isoName(self, file):
        f = os.popen('isosize %s' % file, 'r')
        size = int(f.read())
        f.close()
        if size > 734003200:
            return 'Live DVD'
        else:
            return 'Live CD'

    def finalizeIso(self):
        # move the image into place
        util.copyfile(self.outfile, os.path.join(self.liveDir, 'livecd.img'))
        os.chmod(os.path.join(self.liveDir, 'livecd.img'), 0755) # octal 755

        # make a target and call mkisofs
        os.chdir(self.liveDir)
        fd, self.liveISO = tempfile.mkstemp('.iso', 'livecd',
                                            self.cfg.imagesPath)
        os.close(fd)
        util.execute('mkisofs -o %s -J -R -b isolinux.bin -c boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -V %s .' % (self.liveISO, self.getVolName()))
        os.chmod(self.liveISO, 0755) # octal 755

        isoName = self.isoName(self.liveISO)
        # zip the final product if the main image wasn't compressed already
        if not self.release.getDataValue('zisofs'):
            zippedImage = self.liveISO + '.gz'
            util.execute('gzip -9 < %s > %s' % (self.liveISO, zippedImage))
            os.unlink(self.liveISO)
            os.chmod(zippedImage, 0755)
            return (zippedImage, isoName)

        os.chmod(self.liveISO, 0755)
        return (self.liveISO, isoName)

    def cleanupDirs(self):
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
            self.createImage(self.release.getDataValue('zisofs') and \
                             'zisofs' or 'isofs')

            # now merge them. the hard disk image must be inserted into the iso
            self.status('Finalizing image')
            imagesList = [self.finalizeIso()]
        finally:
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
        self.swapSize = 0
        self.fallback = os.path.join(self.imgcfg.fallbackDir,
                                     self.release.getArch())
        self.addJournal = False
        # the inner image does not need to be bootable
        self.makeBootable = False
        return res
