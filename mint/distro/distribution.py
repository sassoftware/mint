#
# Copyright (c) 2004-2005 Specifix, Inc.
# All rights reserved.

import errno
import files
import os
import os.path
import shutil
import stat
import sys
import tempfile
import time

#conary
from lib import util
from repository import changeset
import updatecmd
import versions
from deps import deps

#darby
from iso import ISO, DiskFullError
import controlfile

class DistroInfo:
    def __init__(self, abbrevName, productPath, productName, version, 
                 phase, isoname=None, arch='x86', nightly=False, isoSize=640):
        """
        Contains information about the names used in the distribution 
        @param abbrevName:      the abbreviated name, used when creating file names
        @param productPath:     a directory name under which the changesets are kept
        @param productName:     the actual name of the product.  Shown in anaconda.
        @param version:         the version of the product
        @param phase:           release phase: ALPHA, BETA, RELEASE, etc.
        @param isoname:         the basic isoname  (can be left none to get a default)
        @param arch:            the architecture (used by anaconda)
        @param nightly:         whether this is a full release or should have a date stamp attached to it
        @param isoSize:         maximum size in megabytes of each ISO image created
        """
        
        assert(abbrevName and productPath and productName and version 
               and  phase and arch)

        self.abbrevName = abbrevName
        self.productPath = productPath
        self.productName = productName
        self.version = version
        self.phase = phase
        if arch == 'x86':
            arch = 'i386'
        self.arch = arch
        self.nightly = nightly
        self.isoSize = isoSize
        if not isoname:
            self.isoname = '%s-%s-%s' % (self.abbrevName, self.version, self.arch)
        else:
            self.isoname = isoname
        if self.nightly:
            self.isoname += '-' + time.strftime('%Y%m%d')

class Distribution:
    def __init__(self, arch, repos, cfg, distro, controlGroup, buildpath, 
		isopath, isoTemplatePath = None, nfspath = None, 
                tftpbootpath = None, cachepath = None, instCachePath = None,
                cachedAnaconda = False, statusCb = None, clean=False):
        """ Contains the necessary information and methods for 
            creating a distribution.
            @param repos:           a NetworkClientRepository with the necessary repoMap
            @param cfg:             a conarycfg file
            @param distro:          a DistroInfo class.  This contains most of the 
                                    information about the type of distribution you 
                                    want to create, and its properties
            @param controlGroup:    the group trove that contains the list of 
                                    desired packages
            @param buildpath:       the path under which the ISOs will be created
                                    in their expanded form.
            @param isopath:         the directory where the final isos will reside
            @param isoTemplatePath: a directory which contains files that should
                                    be copied over to all the isos, after applying
                                    a set of macros including %(fullName), 
                                    %(version)s and %(phase)s.
            @param nfspath:         the path where the packages should be installed
                                    for nfs mount installing
            @param tftpbootpath:    directories where the images should be put
                                    for tftpbooting 
            @param cachepath:       the directory which contains all of the 
                                    necessary changesets
            @param instCachePath:   the directory containing cached Anaconda instroot:
                                    <arch>/inst and <arch>/instgr.
            @param cachedAnaconda:  True to use the anaconda stuff in instCachePath,
                                    False to populate it.
            @param statusCb:        a function to call to update the status of
                                    a distribution job.
            @param clean:           remove old builddir before rebuilding
        """
	self.arch = arch
        self.repos = repos
        self.cfg = cfg
        self.buildpath = buildpath
        self.isoTemplatePath = isoTemplatePath
        if tftpbootpath:
            self.tftpbootpath = os.path.join(tftpbootpath, distro.version)
        self.isos = []
        if distro.nightly:
            buildpath = os.path.join(buildpath,'nightly')
            if nfspath:
                nfspath = os.path.join(nfspath,'nightly')
        self.buildpath = os.path.join(buildpath, distro.version)
        if nfspath:
            nfspath = os.path.join(nfspath, distro.version)
        self.nfspath  = nfspath
        self.isopath = isopath
        self.distro = distro
        self.controlGroup = controlGroup
        self.cachePath = cachepath
        self.instCachePath = instCachePath
        self.cachedAnaconda = cachedAnaconda
        self.clean = clean
        self.statusCb = statusCb

    def status(self, msg):
        if self.statusCb:
            self.statusCb(msg)

    def prep(self):
        """ Create the necessary directories, etc, for creating a 
            distribution
        """
        self.topdir = '%s/%s' % (self.buildpath, self.distro.isoname)
        if self.clean and os.path.exists(self.topdir):
            util.rmtree(self.topdir)
        util.mkdirChain(self.topdir)
        self.subdir = self.topdir + '/' + self.distro.productPath
        util.mkdirChain(os.path.join(self.subdir, 'changesets'))

    def create(self):
        """ main function for actually creating the distribution. 
        """
        self.prep()
        self.createChangeSets(self.controlGroup, 
                os.path.join(self.subdir, 'changesets'))
        self.addIso(bootable = True)

        ciso = self.isos[0]

        csdir = os.path.join(self.subdir, 'changesets')
        isodir = ciso.builddir

        self.pathMap = { 'pname'         : self.distro.productName,
                         'arch'          : self.distro.arch, 
                         'csdir'         : csdir,
                         'ppath'         : self.distro.productPath, 
                         'isodir'        : isodir, 
                         'anaconda'      : os.path.join(self.instCachePath, self.distro.arch, 'anaconda'),
                         'scripts'       : os.path.join(self.instCachePath, self.distro.arch, 'anaconda', 'usr/lib/anaconda-runtime'),
                         'instroot'      : os.path.join(self.instCachePath, self.distro.arch, 'instroot'),
                         'instrootgr'    : os.path.join(self.instCachePath, self.distro.arch, 'instrootgr'),
                         'version'       : self.distro.version } 

        if not self.cachedAnaconda:
            self.makeInstRoots()
        
        self.makeCompsXml()
        self.makeImages()
        self.isos[0].reserve(1)
        self.initializeCDs()
        self.isos[0].release(1)
        self.writeCsList(self.isos[0].builddir)
        
        self.stampIsos()
        iso1 = self.isos[0]
        assert(os.path.exists(iso1.builddir + '/images/diskboot.img')) 
        assert(os.path.exists(iso1.builddir + '/isolinux/vmlinuz'))

        for iso in self.isos:
            iso.create(self.pathMap['scripts'])
        if self.nfspath:
            self.copyToNFS()
        return [iso.imagepath for iso in self.isos]
        
    def addIso(self, bootable = False):
        """ Adds an ISO to the distribution, giving it the appropriate
            disc number, etc.
        """
        discno = len(self.isos) + 1
        isopath = os.path.join(self.isopath, self.distro.isoname)
        isopath += '-disc%d.iso' % discno
        builddir = '%s/%s-disc%d' % (self.buildpath, self.distro.isoname, discno) 
        if os.path.exists(builddir):
            print "Removing old iso dir %s" % builddir
            shutil.rmtree(builddir)
        isoname = self.distro.isoname + ' Disc %d' % discno
        ciso = ISO(builddir, isopath, isoname, discno,
                   maxsize=self.distro.isoSize, bootable = bootable)
        self.isos.append(ciso)
        if self.isoTemplatePath:
            ln = len(self.isoTemplatePath)
            for (root, dirs, files) in os.walk(self.isoTemplatePath):
                isoPath = root[ln:]
                assert(not isoPath or isoPath[0] == '/')
                if files:
                    isoFileDir = ciso.builddir + isoPath 
                    util.mkdirChain(isoFileDir)
                for f in files:
                    isoFilePath =  os.path.join(isoFileDir, f)
                    isoFile = open(isoFilePath, 'w')
                    for line in open(os.path.join(root, f)):
                        isoFile.write(line % self.distro.__dict__)
                    isoFile.close()
                    ciso.markInstalled(isoFilePath)
        return ciso

    def createChangeSets(self, group, csdir):
        """ Creates the main changeset dir, creating files with shorter
            file names based on their version and flavor, but not branch.
            Source troves which do not have matching changesets are 
            simply skipped, and their changesets are not installed on the
            isos.
        """
        
        self.csInfo = {}
        oldFiles = {}
        for path in [ "%s/%s" % (csdir, x) for x in os.listdir(csdir) ]:
            oldFiles[path] = 1

        control = controlfile.ControlFile(self.arch, group, self.repos, self.cfg, self.cfg.installLabelPath[0]) 
        print "Matching changesets..."
            
        matches = control.getRepoTrovesFromCookedGroup()
        unmatched = []

        self.csList = []
        trovesByName = {}

        for trove in matches:
            name = trove.getName()
            if name not in trovesByName:
                trovesByName[name] = [trove]
            else:
                trovesByName[name].append(trove)

        for name in [ 'setup', 'glibc' ]:
            if name in trovesByName:
                for sourceId in trovesByName[name]:
                    self.csList.append(((sourceId.getName(), 
                                         sourceId.getVersion(), 
                                         sourceId.getFlavor()), sourceId))
                del trovesByName[name]

        names = trovesByName.keys()
        names.sort()
        index = 0
        for name in names:
            for sourceId in trovesByName[name]:
                self.csList.append(((name, sourceId.getVersion(), 
                                     sourceId.getFlavor()), sourceId))
            del trovesByName[name]

        l = len(self.csList)
        for (troveName, version, flavor), pkg in self.csList:
            if l > 0:
                percent = (index * 100) / l
                self.status("Extracting changesets: %d%%" % percent)
            else:
                self.status("Extracting changesets")
            if pkg not in matches:
                # we just skip these packages
                csfile = "%s-%s.ccs" % (troveName, 
                                pkg.getVersion().trailingRevision().asString())
                path = "%s/%s" % (csdir, csfile)
                print >> sys.stderr, "%d/%d: skipping %s" % (index, l, csfile)
                index += 1
                continue
            dispName = troveName
            
            if troveName == 'kernel':
                if '!kernel.smp' not in str(flavor):
                    dispName += '-smp'
            troveId = pkg

            if deps.DEP_CLASS_IS in flavor.members:
                pkgarch = flavor.members[deps.DEP_CLASS_IS].members.keys()[0]
            else:
                pkgarch = 'none';
            csfile = "%s-%s-%s.ccs" % (dispName, 
                        troveId.getVersion().trailingRevision().asString(),
                        pkgarch)

            branchDir = troveId.getVersion().branch().asString().replace("/", "_")
            path = os.path.join(csdir, csfile)
            cachedPath = os.path.join(self.cachePath, branchDir, csfile)

            # link the first matching path, assuming they are ordered
            # so that latest is first
            if oldFiles.has_key(path):
                print >> sys.stderr, "%d/%d: keeping old %s" % (index, l, 
                                                                   csfile)
                del oldFiles[path]
            elif os.access(cachedPath, os.F_OK):
                print >> sys.stderr, "%d/%d: linking %s" % (index, l, csfile)
                try:
                    os.link(cachedPath, path)
                except OSError, msg:
                    if msg.errno != errno.EXDEV:
                        raise
                    shutil.copyfile(cachedPath, path)
            else:
                # the trove is still waiting in the repo
                print >> sys.stderr, "%d/%d: extracting %s" % (index+1, l, csfile)
                util.mkdirChain(os.path.dirname(cachedPath))
                util.mkdirChain(os.path.dirname(path))
                troveId.createChangeSet(cachedPath, self.repos, self.cfg, component=troveName)
                try:
                    os.link(cachedPath, path)
                except OSError, msg:
                    if msg.errno != errno.EXDEV:
                        raise
                    shutil.copyfile(cachedPath, path)

            cs = changeset.ChangeSetFromFile(path)
            trailing = troveId.getVersion().trailingRevision().asString()
            v = trailing.split('-')
            version = '-'.join(v[:-2])
            release = '-'.join(v[-2:])
            size = 0
            # calculate size when installed 

            for pkgCs in cs.iterNewTroveList():
                for (pathId, fPath, fileId, fVer) in pkgCs.getNewFileList():
                    if (troveName.startswith('kernel')
                        and fPath.startswith('/boot/vmlinuz-')):
                        # set the version to be the kernel's extraversion
                        release = fPath.split('-')[-1]
                    fileObj = files.ThawFile(cs.getFileChange(None, fileId), 
                                                                        pathId)
                    if fileObj.hasContents:
                        size += fileObj.contents.size()
            self.csInfo[troveName, pkg] = {'dispName' : dispName, 
                                           'path': path, 'size': size, 
                                           'version' : version, 'release' : release}
            index += 1
        # okay, now cut out unneeded desired trove info from csList
        self.csList = [(x[0][0], x[1]) for x in self.csList ] 

    def initializeCDs(self):
        """ Install files from the main changeset directory into the various
            individual CD's directories.  Assumes createChangeSets has 
            been called.  Assigns a disc number to each changeset.  """
        ciso = self.isos[0]
        csdir = '/'.join(('',self.distro.productPath, 'changesets'))
        for troveName, pkg in self.csList:
            if (troveName, pkg) not in self.csInfo:
                print "Skipping %s in initializeCDs"  % pkg
                continue
            info = self.csInfo[(troveName, pkg)]
            try:
                curfilepath = info['path']
                isofilepath = os.path.join(csdir, 
                                            os.path.basename(info['path']))
                ciso.install(curfilepath, isofilepath)
                info['disc'] = ciso.discno
            except DiskFullError:
                ciso = self.addIso()
                ciso.install(curfilepath, isofilepath)
                info['disc'] = ciso.discno

    def writeCsList(self, basepath, overrideDisc=None):
        """ Write information about package, version, size, and disc
            the the main changeset list
        """
        path = '/'.join((basepath, self.distro.productPath, 'base/cslist'))
        util.mkdirChain(os.path.dirname(path))
        csfile = open(path, 'w')
        for troveName, pkg in self.csList:
            if (troveName, pkg) in self.csInfo:
                info = self.csInfo[troveName, pkg]
                if overrideDisc is None:
                    d = info['disc']
                else:
                    d = overrideDisc
                print >> csfile, os.path.basename(info['path']), \
                        info['dispName'], info['version'], info['release'], info['size'], d
        csfile.flush()
        csfile.close()
        if not overrideDisc:
            self.isos[0].markInstalled(path) 

    def stampIsos(self):
        """ Create the .discinfo files -- note that the timestamp on 
            these files must be shared so that anaconda believes they 
            are meant to be used together.
        """
        iso = self.isos[0]
        self.pathMap['discno'] = iso.discno
        os.system('python %(scripts)s/makestamp.py --releasestr="%(pname)s" '
                  '--arch="%(arch)s" --discNum="%(discno)s" '
                  '--baseDir=%(ppath)s/base --packagesDir=%(ppath)s/changesets '
                  '--pixmapsDir=%(ppath)s/pixmaps --outfile=%(isodir)s/.discinfo' % self.pathMap)
        stampLines = open('%s/.discinfo' % iso.builddir).readlines()
        iso.markInstalled('%s/.discinfo' % iso.builddir)
        for iso in self.isos[1:]:
            stampFile = open('%s/.discinfo' % iso.builddir, 'w')
            stampLines[3] = str(iso.discno) + '\n'
            stampFile.write(''.join(stampLines))
            stampFile.close()
            iso.markInstalled('%s/.discinfo' % iso.builddir)

    def makeCompsXml(self):
        os.environ['PYTHONPATH'] = os.environ.get('CONARY_PATH', 
                                                  '/usr/share/conary')
        os.environ['CONARY'] = 'conary'
        basedir = '/'.join((self.pathMap['isodir'], self.pathMap['ppath'], 'base'))
        compspath = basedir + '/comps.xml'
        util.mkdirChain(basedir)
        compsfile = open(compspath, 'w')
        compsfile.write('''<?xml version="1.0"?>
<!DOCTYPE comps PUBLIC "-//Red Hat, Inc.//DTD Comps info//EN" "comps.dtd">
<comps>
  <group>
    <id>core</id>
    <name>Core</name>
    <default>true</default>
    <uservisible>false</uservisible>
    <description>Smallest possible installation</description>
    <packagelist>
      <packagereq type="mandatory">acl</packagereq>
      <packagereq type="default">ash</packagereq>
      <packagereq type="mandatory">attr</packagereq>
      <packagereq type="mandatory">bash</packagereq>
      <packagereq type="mandatory">bzip2</packagereq>
      <packagereq type="mandatory">dev</packagereq>
      <packagereq type="mandatory">db</packagereq>
      <packagereq type="mandatory">chkconfig</packagereq>
      <packagereq type="mandatory">coreutils</packagereq>
      <packagereq type="mandatory">cpio</packagereq>
      <packagereq type="mandatory">cracklib</packagereq>
      <packagereq type="mandatory">conary</packagereq>
      <packagereq type="mandatory">dhclient</packagereq>
      <packagereq type="mandatory">distro-release</packagereq>
      <packagereq type="mandatory">e2fsprogs</packagereq>
      <packagereq type="mandatory">ed</packagereq>
      <packagereq type="mandatory">file</packagereq>
      <packagereq type="mandatory">filesystem</packagereq>
      <packagereq type="mandatory">glibc</packagereq>
      <packagereq type="default" basearchonly="true">grub</packagereq>
      <packagereq type="mandatory">hdparm</packagereq>
      <packagereq type="mandatory">hotplug</packagereq>
      <packagereq type="mandatory">hwdata</packagereq>
      <packagereq type="mandatory">initscripts</packagereq>
      <packagereq type="mandatory">iproute</packagereq>
      <packagereq type="mandatory">iptables</packagereq>
      <packagereq type="mandatory">iputils</packagereq>
      <packagereq type="mandatory">kbd</packagereq>
      <packagereq type="mandatory">kernel</packagereq>
      <packagereq type="mandatory">gawk</packagereq>
      <packagereq type="mandatory">gcc</packagereq>
      <packagereq type="mandatory">gdbm</packagereq>
      <packagereq type="mandatory">glib</packagereq>
      <packagereq type="mandatory">gpm</packagereq>
      <packagereq type="mandatory">grep</packagereq>
      <packagereq type="mandatory">gzip</packagereq>
      <packagereq type="mandatory">libelf</packagereq>
      <packagereq type="mandatory">libtermcap</packagereq>
      <packagereq type="mandatory">libuser</packagereq>
      <packagereq type="mandatory">mdadm</packagereq>
      <packagereq type="mandatory">mkinitrd</packagereq>
      <packagereq type="mandatory">mktemp</packagereq>
      <packagereq type="mandatory">mingetty</packagereq>
      <packagereq type="mandatory">module-init-tools</packagereq>
      <packagereq type="mandatory">ncurses</packagereq>
      <packagereq type="mandatory">newt</packagereq>
      <packagereq type="mandatory">net-tools</packagereq>
      <packagereq type="mandatory">pam</packagereq>
      <packagereq type="mandatory">passwd</packagereq>
      <packagereq type="mandatory">pcre</packagereq>
      <packagereq type="mandatory">perl</packagereq>
      <packagereq type="mandatory">popt</packagereq>
      <packagereq type="mandatory">python</packagereq>
      <packagereq type="mandatory">procps</packagereq>
      <packagereq type="mandatory">readline</packagereq>
      <packagereq type="mandatory">rhpl</packagereq>
      <packagereq type="mandatory">rootfiles</packagereq>
      <packagereq type="mandatory">sed</packagereq>
      <packagereq type="mandatory">setserial</packagereq>
      <packagereq type="mandatory">setup</packagereq>
      <packagereq type="mandatory">slang</packagereq>
      <packagereq type="mandatory">sqlite</packagereq>
      <packagereq type="mandatory">sysklogd</packagereq>
      <packagereq type="mandatory">sysvinit</packagereq>
      <packagereq type="mandatory">tar</packagereq>
      <packagereq type="mandatory">termcap</packagereq>
      <packagereq type="mandatory">tzdata</packagereq>
      <packagereq type="mandatory">util-linux</packagereq>
      <packagereq type="mandatory">vim-minimal</packagereq>
      <packagereq type="mandatory">zlib</packagereq>
      <packagereq type="default">authconfig</packagereq>
      <packagereq type="default">kudzu</packagereq>
      <packagereq type="default">system-config-mouse</packagereq>
      <packagereq type="default">usermode</packagereq>
      <packagereq type="default">shadow</packagereq>
    </packagelist>
  </group>

  <group>
    <id>base</id>
    <name>Base</name>
    <description>This group includes a minimal set of packages.</description>
    <uservisible>false</uservisible>
    <default>true</default>
    <grouplist>
      <groupreq>core</groupreq>
    </grouplist>
  </group>

  <grouphierarchy>
  </grouphierarchy>
</comps>
''')
        compsfile.close()

        # just touch these files
        basedir = '/'.join((self.pathMap['isodir'], self.pathMap['ppath'], 'base'))

        open(basedir + '/hdlist', 'w')
        open(basedir + '/hdlist2', 'w')
        
    def makeInstRoots(self):
        # install anaconda into a root dir
        oldroot = self.cfg.root
        self.cfg.root = self.pathMap['anaconda']
        updatecmd.doUpdate(self.cfg, ['anaconda[is:%s]' % self.arch], 
                           depCheck=False)
        self.cfg.root = oldroot
        
        sys.stdout.flush()
        sys.stderr.flush()
        
        cmd = 'sh -x %(scripts)s/upd-instroot --debug --conary --arch %(arch)s %(csdir)s %(instroot)s %(instrootgr)s' % self.pathMap
        print "\n\n*********** RUNNING UPD-INSTROOT ***************\n\n"
        print cmd
        self.status("Creating Anaconda installation images")
        sys.stdout.flush()
        rc = os.system(cmd)
        print "<<Result code: %d>>" % rc
        sys.stdout.flush()
        sys.stderr.flush()

    def makeImages(self):
        ciso = self.isos[0]
        print "\n\n*********** RUNNING mk-images ***************\n\n"
        cmd = ('%(scripts)s/mk-images --debug --conary %(csdir)s %(isodir)s '
               '%(instroot)s %(instrootgr)s %(arch)s "%(pname)s" %(version)s %(ppath)s' % self.pathMap)
        print cmd
        self.status("Assembling ISO images")
        sys.stdout.flush()
        sys.stderr.flush()
        rc = os.system(cmd)
        print "<<Result code: %d>>" % rc
        sys.stdout.flush()
        sys.stderr.flush()

        ciso.markDirInstalled('/isolinux')
        ciso.markDirInstalled('/images')
        ciso.markDirInstalled('/%s/base/' % self.pathMap['ppath'])

    def copyToNFS(self):
        """ set up the changests and auxilliary files necessary 
            for doing an NFS install.  Also needs to copy
            the images over to a TFTP boot path so that a 
            matching image can be loaded with the NFS files.
        """
        util.mkdirChain(self.nfspath)
        linkOk = (os.stat(self.topdir)[stat.ST_DEV] == os.stat(self.nfspath)[stat.ST_DEV])
        os.system('rm -rf %s' % self.nfspath)
        if linkOk:
            os.system('cp -arl %s %s' % (self.topdir, self.nfspath))
        else:
            print "Copying over changesets to nfs dir"
            util.execute('cp -arf %s/ %s' % (self.topdir, self.nfspath))
            util.execute('cp -arf %s/.discinfo %s' % (self.isos[0].builddir, 
                                                            self.nfspath))
            print "Copying over auxiliary files to nfs dir"
            for path in 'images', 'isolinux', '%s/base' % self.distro.productPath:
                util.mkdirChain('%s/%s' % (self.nfspath, path))
                util.execute('cp -arf %s/%s/* %s/%s' % (self.isos[0].builddir, 
                                        path, self.nfspath, path))
        self.writeCsList(self.nfspath, overrideDisc=1)
        if self.tftpbootpath is not None:
            print "Copying boot images to %s" % self.tftpbootpath
            util.mkdirChain(self.tftpbootpath)
            util.execute('cp -arf %s/isolinux/{initrd.img,vmlinuz} %s' % \
                        (self.isos[0].builddir, self.tftpbootpath))
