import errno
import files
from lib import util
import time
import os
from pkgid import PkgId, thawPackage
from repository import changeset
import os.path
import sys
import tempfile
import time
import updatecmd

class ISO:
    blocksize = 2048
    #maxsize = 640 * 1024 * 1024
    maxsize = 640 * 1024 * 1024

    def __init__(self, builddir, path, name, discno = 0, bootable=False):
        # builddir is the top directory which will contain the ISO dir tree and files
        # path is where the iso image will end up
        # name is the human-readable name of the CD
        self.reserved = 0
        self.freespace = self.maxsize - self.reserved
        self.builddir = builddir
        self.isopath = path
        self.isoname = name
        self.files = {}
        self.discno = discno
        self.dirs = {}
        self.bootable=bootable

    def reserve(self, megs):
        self.freespace -= megs * 1024 * 1024
        self.reserved += megs * 1024 * 1024

    def addFile(self, isopath, currentpath=None):
        if isopath[-1] == '/':
            raise OSError, "Don't add directories"
        if isopath[0] != '/':
            raise OSError, "Must give absolute paths for ISO: %s" % isopath
        isopath = os.path.normpath(isopath)
        if isopath in self.files:
            raise OSError, "Already a file at location", isopath
        if not currentpath:
            # if the currentpath arg is not given, then isopath
            # should already exist, but not be in 
            currentpath = self.builddir + isopath
            if not os.path.exists(currentpath):
                raise OSError, "No such file at %s " % currentpath
            link = False
        else:
            if currentpath[-1] == '/':
                raise OSError, "Cannot add directories as files"
            link = True
        dirname = os.path.dirname(isopath)
        util.mkdirChain(dirname)
        sb = os.stat(currentpath)
            # round up to an ISO9660 block
        total = sb.st_size + (self.blocksize - sb.st_size % self.blocksize)
        if self.freespace < total:
            extra = total - self.freespace
            raise DiskFullError, "Error: cannot fit %s on disk -- uses %d extra bytes" % (currentpath, extra)
        # Only add a link to the file if there is actually room for the file
        if link:
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
        self.freespace -= total
        self.files[isopath] = currentpath

    def _makeISO(self):
        if self.bootable:
            os.system('cd %s; mkisofs -o %s -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -R -J -V "%s" -T .' % (self.builddir, self.isopath, self.isoname))
        else:
            os.system('cd %s; mkisofs -o %s -R -J -V "%s" -T .' % (self.builddir, self.isopath, self.isoname))
        os.system('/home/msw/implantisomd5 %s' % self.isopath)
        print "ISO created at %s" % self.isopath

    def create(self):
        pass
        # Actually create
        #self._createDirStructure()
        self._makeISO()
            
class DiskFullError(Exception):
    pass
