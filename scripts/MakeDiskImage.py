import os, sys, errno, tempfile, time
from conary.lib import util
from conary import conarycfg, conaryclient, versions
from conary.repository import errors
from conary.conaryclient.cmdline import parseTroveSpec
from urlparse import urlparse
import hotshot

#Different cylinder sizes.  I don't know which is better, but I've seen
#both: 8225280 or 516096
cylindersize = 516096
sectors = 63
heads = 16

partoffset0 = 512

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

class BootableDiskImage:
    fakeroot = None

    def __init__(self, file, size, group, installLabel, repoMap=None, arch='x86'):
        self.outfile = file
        padding = cylindersize - (size % cylindersize)
        if cylindersize == padding:
            padding = 0
        self.imagesize = size + padding
        self.basetrove, self.baseversion, self.baseflavor = parseTroveSpec(group)
        self.InstallLabel = installLabel
        if not repoMap:
            key = self.InstallLabel.split()[0]
            host, label = key.split('@')
            self.repoMap = {key: 'http://' + host + '/conary/'}
            #self.host = host
        else:
            self.repoMap = repoMap
            #self.host = urlparse(repoMap[
        self.arch = arch

    @outputfilesize
    @timeMe
    def prepareDiskImage(self):
        #erase the file if it exists
        try:
            os.unlink(self.outfile)
        except OSError, e:
            if e.errno != errno.ENOENT:
                raise e
        #create the disk file
        ofile = open(self.outfile, 'wb', 0644)
        ofile.seek(self.imagesize-1)
        ofile.write('\x00')
        ofile.close()

        #Do the partition table
        cylinders = self.imagesize / cylindersize
        #TODO: Add a swap partition?
        cmd = '/sbin/sfdisk -C %d -S %d -H %d %s > /dev/null' % (cylinders, sectors, heads, self.outfile)
        input = "0 %d L *\n" % (cylinders)
        sfdisk = util.popen(cmd, 'w')
        sfdisk.write(input)
        retval = sfdisk.close()
        #Don't worry about formatting or labeling

    def _writefstab(self):
        ofile = open('etc/fstab', 'w', 0644)
        ofile.write('''
none                    /dev/pts                devpts  gid=5,mode=620  0 0
none                    /dev/shm                tmpfs   defaults        0 0
none                    /proc                   proc    defaults        0 0
none                    /sys                    sysfs   defaults        0 0
''')
        ofile.close()

    @timeMe
    def createTemporaryRoot(self, basedir = os.getcwd()):
        #Create a temporary directory
        self.fakeroot = tempfile.mkdtemp('', 'mint-MDI-', basedir)
        #Create some structure
        cwd = os.getcwd()
        os.chdir(self.fakeroot)
        util.mkdirChain( 'etc', 'boot/grub', 'tmp', 'sys' )
        #write the fstab
        self._writefstab()
        os.chdir(cwd)

    @timeMe
    def setupConaryClient(self):
        #Create a ConaryClient
        cfg = conarycfg.ConaryConfiguration(readConfigFiles=False)
        cfg.repositoryMap = self.repoMap
        cfg.flavor = None
        cfg.root = self.fakeroot
        cfg.installLabelPath = None
        #TODO Add the user if anonymous access is not available
        #servername = urlparse(self.repoMap[1])[1]
        #if ':' in servername:
        #    servername = servername.split(':')[0]
        #cfg.addServerGlob(servername, 'anonymous', 'anonymous')

        self.cclient = conaryclient.ConaryClient(cfg)

    @timeMe
    def populateTemporaryRoot(self):
        try:
            itemList = [(self.basetrove, (None, None), (self.baseversion, self.baseflavor), True)]
            sys.stderr.flush()
            uJob, suggMap = self.cclient.updateChangeSet(itemList, resolveDeps = False)
        except errors.TroveNotFound:
            raise

        #Capture devices, taghandlers and ownership changes
        journal = Journal()
        #Install the group
        #TODO Cache the tagScripts to run via some virtualized linux process
        self.cclient.applyUpdate(uJob, journal=journal)

    @timeMe
    def installKernel(self):
        #Install the Kernel
        try:
            kernel, version, flavor = parseTroveSpec('kernel[is: %s]' % self.arch)
            itemList = [(kernel, (None, None), (version, flavor), True)]
            uJob, suggMap = self.cclient.updateChangeSet(itemList, sync=True,
                                resolveDeps=False)
        except errors.TroveNotFound:
            raise
        journal = Journal()
        self.cclient.applyUpdate(uJob, journal=journal, tagScript='/dev/null')

    @timeMe
    def fileSystemOddsNEnds(self):
        pass

    @timeMe
    def MakeE2FsImage(self, file):
        cmd = '/usr/bin/e2fsimage -f %s -d %s -s %d' % (file,
                self.fakeroot, (self.imagesize - partoffset0)/1024)
        util.execute(cmd)

    @outputfilesize
    @timeMe
    def WriteBack(self, file):
        #Now write this FS image back to the original image
        fd = open(file, 'rb')
        fdo = open(self.outfile, 'r+b')
        fdo.seek(partoffset0)
        util.copyfileobj(fd, fdo, bufSize=524288)
        fd.close()
        fdo.close()
 
    @timeMe
    def createFileSystem(self, basedir = os.getcwd()):
        fd, file = tempfile.mkstemp('', 'mint-MDI-cFS-', basedir)
        os.close(fd)
        del fd
        try:
            self.MakeE2FsImage(file)
            self.WriteBack(file)
        finally:
            pass
            #os.unlink(file)

    @timeMe
    def makeBootable(self):
        #install boot manager
        pass

    @timeMe
    def makeBootableDiskImage(self, basedir = os.getcwd()):
        self.prepareDiskImage()
        self.createTemporaryRoot(basedir)
        self.setupConaryClient()
        self.populateTemporaryRoot()
        self.installKernel()
        self.fileSystemOddsNEnds()
        self.createFileSystem()
        self.makeBootable()

    def __del__(self):
        #Cleanup: remove the fakeroot
        if self.fakeroot:
            pass
            #util.rmtree(self.fakeroot)

def main():
    di = BootableDiskImage('foo.img', 2000000000, 'group-dist=foobar.org.rpath@rpl:devel', 'foobar.org.rpath@rpl:devel conary.rpath.com@rpl:1 contrib.rpath.org@rpl:devel')
    di.makeBootableDiskImage()

main()
