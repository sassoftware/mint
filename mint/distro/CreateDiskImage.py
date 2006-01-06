#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

from conary.conaryclient.cmdline import parseTroveSpec
from qemu_image import BootableDiskImage

class BootableQemuDiskImage(BootableDiskImage):
    fakeroot = None
    cfg = None

    def __init__(self, file, size, group, installLabel, repoMap=None, arch='x86'):
        sys.excepthook = debugme
        self.outfile = file
        self.freespace = size
        self.basetrove, self.baseversion, self.baseflavor = parseTroveSpec(group)
        self.InstallLabel = installLabel.split()
        if not repoMap:
            key = self.InstallLabel[0]
            host, label = key.split('@')
            self.repoMap = {key: 'http://' + host + '/conary/'}
            #self.host = host
        else:
            self.repoMap = repoMap
            #self.host = urlparse(repoMap[
        self.arch = arch

    @timeMe
    def makeBootableQemuDiskImage(self, basedir = os.getcwd()):
        self.createTemporaryRoot(basedir)
        self.setupConaryClient()
        self.populateTemporaryRoot()
        self.installKernel()
        self.fileSystemOddsNEnds()
        self.createFileSystem()
        self.runTagScripts()
        self.makeBootable()

    def __del__(self):
        #Cleanup: remove the fakeroot
        if self.fakeroot:
            pass
            #util.rmtree(self.fakeroot)

def main():
    #di = BootableQemuDiskImage('foo.img', 250000000, 
        #'group-dist=/conary.rpath.com@rpl:devel//1/0.99.3-0.2-5[X,~!alternatives,~!bootstrap,~!builddocs,~buildtests,desktop,dietlibc,emacs,gcj,~glibc.tls,gnome,~!grub.static,gtk,ipv6,kde,~!kernel.debug,~!kernel.debugdata,~!kernel.numa,krb,ldap,nptl,~!openssh.smartcard,~!openssh.static_libcrypto,pam,pcre,perl,~!pie,~!postfix.mysql,python,qt,readline,sasl,~!selinux,~sqlite.threadsafe,ssl,tcl,tcpwrappers,tk,~!xorg-x11.xprint is: x86(cmov,i486,i586,i686,~!mmx,~!sse2)]',
        #'conary.rpath.com@rpl:1 contrib.rpath.org@rpl:devel', repoMap = {'conary.rpath.com': 'http://conary-commits.rpath.com/conary/'})
    #di = BootableQemuDiskImage('foo.img', 250*1024*1024, 'group-dist=foobar.org.rpath@rpl:devel', 'foobar.org.rpath@rpl:devel conary.rpath.com@rpl:1 contrib.rpath.org@rpl:devel')
    di = BootableQemuDiskImage('foo.img', 250*1024*1024,
        'group-system=/systemimages.org.rpath@rpl:devel/0.0.1-1-1[X,~!alternatives,~!bootstrap,~!builddocs,~buildtests,desktop,dietlibc,emacs,gcj,~glibc.tls,gnome,~!grub.static,gtk,ipv6,kde,~!kernel.debug,~!kernel.debugdata,~!kernel.numa,krb,ldap,nptl,~!openssh.smartcard,~!openssh.static_libcrypto,pam,pcre,perl,~!pie,~!postfix.mysql,python,qt,readline,sasl,~!selinux,~sqlite.threadsafe,ssl,tcl,tcpwrappers,tk,~!xorg-x11.xprint   is: x86(cmov,i486,i586,i686,~!mmx,~!sse2)]',
        'rbuilder.org.rpath@rpl:devel conary.rpath.com@rpl:1 contrib.rpath.org@rpl:devel')
    di.makeBootableDiskImage()

#main()
