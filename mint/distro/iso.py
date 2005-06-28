#
# Copyright (c) 2004-2005 rpath, Inc.
#
# All rights reserved.
#

import errno
import files
from lib import util
import time
import os
from repository import changeset
import os.path
import sys
import tempfile
import time
import updatecmd

class ISO:
    blocksize = 2048

    def __init__(self, builddir, imagepath, name, discno = 0,
                       maxsize = 640, bootable=False):
        """Initialize the CD.
           @param builddir:  the directory which will contain the ISO dir tree,
                             which will eventually get put in the ISO image 
           @param imagepath: the path that the iso image stored to
           @param name:      the human-readable name of the CD
           @param discno:    a disc number that can be used to differentiate isos
                             in a set.
           @param maxsize:   the maximum size of each ISO image, in megabytes 
           @param bootable:  determines whether the CD should be made bootable or not
                             requires that the builddir contains the appropriate
                             isolinux dir.
        """
        self.reserved = 0
        self.maxsize = int(maxsize) * 1024 * 1024
        self.freespace = self.maxsize - self.reserved
        self.builddir = builddir
        self.imagepath = imagepath
        self.isoname = name[:32] # limit iso name for ISO9660 limitations
        self.files = {}
        self.discno = discno
        self.dirs = {}
        self.bootable=bootable
        
    def reserve(self, megs):
        """ Reserve an amount of space on the disk, causing DiskFullError
            to be raised after fewer files are added """
        self.freespace -= megs * 1024 * 1024
        self.reserved += megs * 1024 * 1024

    def release(self, megs):
        """ Reserve an amount of space on the disk, causing DiskFullError
            to be raised after fewer files are added """
        amt = megs * 1024 * 1024
        if self.reserved < amt:
            raise RuntimeError, "%s megs were not reserved, cannot release" % megs
        self.freespace += amt
        self.reserved -= amt

    def getSize(self):
        """ Gets the used disk size in bytes """
        return self.maxsize - self.freespace

    def getFileSize(self, path):
        """ Gets the amount of space a file will take up on the ISO.
            Path is absolute.
        """
        assert(path[0] == '/')
        sb = os.stat(path)
        filesize = sb.st_size + (self.blocksize - sb.st_size % self.blocksize)
        return filesize


    def checkInstallable(self, path):
        """ Check whether the given file will fit on the current disk.
            Return the size of the file. Path is absolute.  """
        # round up to an ISO9660 block
        filesize = self.getFileSize(path)
        if self.freespace < filesize:
            extra = filesize - self.freespace
            raise DiskFullError, ("Error: cannot fit %s on disk --"
                                  " uses %d extra bytes" % (path, extra))
        return filesize

    def install(self, currentpath, isopath):
        """ Install a file onto the iso.  The currentpath is a full path,
            and isopath is a path relative to the root of the iso build dir 
        """
        if isopath[-1] == '/':
            raise OSError, "Don't add directories"
        if isopath[0] != '/':
            raise OSError, "Must give absolute paths for ISO: %s" % isopath
        isopath = os.path.normpath(isopath)
        if isopath in self.files:
            raise OSError, ("Already a file at location %s" % isopath)
        dirname = os.path.dirname(isopath)
        filesize = self.checkInstallable(currentpath)
        # Only add a link to the file if there is actually room for the file
        targetpath = self.builddir + isopath
        try:
            util.mkdirChain(os.path.dirname(targetpath))
            os.link(currentpath, targetpath)
        except OSError, err:
            if err[0] == errno.EEXIST:
                # XXX we can keep this link, but really, we shouldn't 
                # run into this situation at all.  Only happens when 
                # you are making lots of the same ISO over and over again
                os.remove(targetpath)
                os.link(currentpath, targetpath)
            else:
                raise
        self.freespace -= filesize
        self.files[isopath] = filesize

    def markInstalled(self, fullpath, errorOnExisting=True):
        """ Mark a file as in the iso's dir path.  Fullpath is absolute,
            and should start with the iso's builddir.  
            markInstalled allows a file to
            be installed by another process and then recognized as being
            built by the iso.  That ensures that the iso's calculations about
            how much space the iso is using is correct.
        """
        if not fullpath.startswith(self.builddir):
            raise RuntimeError, "Must give absolute path to markInstalled"
        ln = len(self.builddir)
        isopath = fullpath[ln:]
        if isopath[-1] == '/':
            raise RuntimeError, "Don't add directories"
        assert(isopath[0] == '/')
        if isopath in self.files:
            if errorOnExisting:
                raise OSError, ("Already a file at location %s" % isopath)
            else:
                return
        if not os.path.exists(fullpath):
            raise OSError, "No such file: %s" % fullpath
        filesize = self.checkInstallable(fullpath)
        self.freespace -= filesize
        self.files[isopath] = filesize

    def markDirInstalled(self, isodir, errorOnExisting=True):
        """ mark all files under isodir as installed.  Isodir is 
            relative to the base dir of the iso.  If errorOnExisting is 
            true, then raise and error if a file is to be marked twice as
            installed.  Otherwise, simply skip files already marked as 
            installed.
        """
        if(isodir[0] != '/'):
            raise RuntimeError, "Must give absolute path to markDirInstalled"
        ln = len(self.builddir)
        for (root, dirs, files) in os.walk(self.builddir + isodir):        
            for fileName in files:
                self.markInstalled(os.path.join(root, fileName), 
                                                errorOnExisting)

    def checkForUnknownFiles(self):
        """ Checks that every file that will make it on to this
            iso is accounted for by the ISO.  This will ensure 
            that the size accounting done by the iso is accurate.
        """
        ln = len(self.builddir)
        unknownfiles = self.files.copy()
        actualsize = 0
        extrafiles = []
        wrongsize = []
        for (root, dirs, files) in os.walk(self.builddir):
            for fileName in files:
                # can't use os.path.join bc it doesn't handle the case
                # where root == builddir, so that root[ln:] == ''
                isopath = root[ln:] + '/' + fileName
                if isopath not in unknownfiles:
                    extrafiles.append(isopath)
                else:
                    del unknownfiles[isopath]
                    fullpath = root + '/' + fileName
                    actualsize += self.getFileSize(fullpath)
                    if self.getFileSize(fullpath) != self.files[isopath]:
                        wrongsize.append(isopath)
        sizediff = abs(actualsize - self.getSize())

        if unknownfiles or extrafiles or sizediff:
            error = ['Errors on ISO %d at %s:' % (self.discno, self.builddir) ]
            if unknownfiles:
                error.append("Files expected on ISO but"
                             " missing: %s" % unknownfiles)
            if extrafiles:
                error.append("Unexpected files on ISO: %s" % extrafiles)
            if sizediff:
                error.append("Size difference between calculated and "
                             " actual size: %s" % sizediff)
            if wrongsize:
                error.append("The following files are the wrong size: %s"
                             % [ (x, self.files[x]) for x in wrongsize ])

            raise RuntimeError, '\n'.join(error)


    def _makeISO(self, scriptsDir):
        """ Actually make the image, based on the parameters set before.
            The builddir should have exactly the files that are meant to 
            be on the image.  The md5 sum is implanted """
        util.mkdirChain(os.path.dirname(self.imagepath))
        if self.bootable:
            util.execute('cd %s; mkisofs -o %s -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -R -J -V "%s" -T .' % (self.builddir, self.imagepath, self.isoname))
        else:
            util.execute('cd %s; mkisofs -o %s -R -J -V "%s" -T .' % (self.builddir, self.imagepath, self.isoname))
        util.execute('%s/implantisomd5 %s' % (scriptsDir, self.imagepath))
        print "ISO created at %s" % self.imagepath

    def create(self, scriptsDir):
        """ Create the CD.  Checks the CD for sanity first """
        self.checkForUnknownFiles()
        self._makeISO(scriptsDir)
            
class DiskFullError(Exception):
    pass
