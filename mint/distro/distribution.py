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

#darby
from iso import ISO, DiskFullError
import controlfile

class DistroInfo:
    def __init__(self, abbrevName, productPath, productName, version, 
                 phase, isoname=None, arch='i386', nightly=False):
        """ Contains information about the names used in the distribution 
        Parameters:
            abbrevName:  the abbreviated name, used when creating file names

            productPath: a directory name under which the changesets are kept

            productName: the actual name of the product.  Shown in anaconda.

            version:     the version of the product

            isoname:     the basic isoname  (can be left none to get a default)

            arch:        the architecture (used by anaconda)

            nightly:     whether this is a full release or should have a date
                         stamp attached to it
        """
        
        assert(abbrevName and productPath and productName and version 
               and  phase and arch)

        self.abbrevName = abbrevName
        self.productPath = productPath
        self.productName = productName
        self.version = version
        self.phase = phase
        self.arch = arch
        self.nightly = nightly
        if not isoname:
            self.isoname = '%s-linux-%s' % (self.abbrevName, self.version)
        else:
            self.isoname = isoname
        if self.nightly:
            self.isoname += '-' + time.strftime('%Y%m%d')

class Distribution:
    def __init__(self, repos, cfg, distro, controlGroup, buildpath, isopath, 
                isoTemplatePath, nfspath, tftpbootpath, fromcspath, logdir, 
                clean=False):
        """ Contains the necessary information and methods for 
            creating a distribution.  

            Parameters:
                repos: a NetworkClientRepository with the necessary repoMap
                cfg: a conarycfg file
                distro: a DistroInfo class.  This contains most of the 
                        information about the type of distribution you 
                        want to create, and its properties
                controlGroup: the group trove that contains the list of 
                              desired packages

                buildpath:    the path under which the ISOs will be created
                              in their expanded form.

                isopath:      the directory where the final isos will reside

                isoTemplatePath: a directory which contains files that should
                              be copied over to all the isos, after applying
                              a set of macros including %(fullName), 
                              %(version)s and %(phase)s.

                nfspath:      the path where the packages should be installed
                              for nfs mount installing

                tftpbootpath: directories where the images should be put
                              for tftpbooting 

                fromcspath:   the directory which contains all of the 
                              necessary changesets

                logdir:       directory to log the output from creating 
                              the iso.  If none, output is printed on 
                              stdout and stderr

                clean: remove old builddir before rebuilding
        """
        self.repos = repos
        self.cfg = cfg
        self.buildpath = buildpath
        self.isoTemplatePath = isoTemplatePath
        self.logdir = logdir
        self.tftpbootpath = tftpbootpath
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
        # Place to look for Changesets that have already been made
        self.fromcspath = fromcspath
        self.clean = clean

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

    def create(self, useAnaconda=True):
        """ main function for actually creating the distribution. 
            useAnaconda determines whether we should make the distro 
            bootable and usable by anaconda.  Doing so takes a considerable
            amount of time -- this option is useful mainly for testing 
            purposes to ensure that at least most of this path gets
            tested.
        """
        self.prep()
        self.createChangeSets(self.controlGroup, 
                os.path.join(self.subdir, 'changesets'))
        self.addIso(bootable=useAnaconda)
        self.makeInstRoots(useAnaconda)
        self.initializeCDs()
        self.writeCsList(self.isos[0].builddir)
        if useAnaconda:
            self.stampIsos()
            iso1 = self.isos[0]
            assert(os.path.exists(iso1.builddir + '/images/diskboot.img')) 
            assert(os.path.exists(iso1.builddir + '/isolinux/vmlinuz'))
        for iso in self.isos:
            iso.create()
        if self.nfspath:
            self.copyToNFS()

    def addIso(self, bootable=False):
        """ Adds an ISO to the distribution, giving it the appropriate
            disc number, etc.
        """
        discno = len(self.isos) + 1
        isopath = os.path.join(self.isopath, self.distro.isoname)
        isopath += '-disc%d.iso' % discno
        builddir = '%s/%s-disc%d' % (self.buildpath, self.distro.isoname, 
                                                                    discno) 
        if os.path.exists(builddir):
            print "Removing old iso dir %s" % builddir
            shutil.rmtree(builddir)
        isoname = self.distro.isoname + ' Disc %d' % discno
        ciso = ISO(builddir, isopath, isoname, discno, bootable=bootable)
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
        getFromCookedGroup = True
        fromcspath = self.fromcspath
        self.csInfo = {}
        oldFiles = {}
        for path in [ "%s/%s" % (csdir, x) for x in os.listdir(csdir) ]:
            oldFiles[path] = 1

        control = controlfile.ControlFile(group, self.repos, self.cfg, self.cfg.installLabelPath[0]) 
        print "Matching changesets..."
        if fromcspath:
            control.loadControlFile()
            matches, unmatched = control.getMatchedChangeSets(fromcspath)
        elif getFromCookedGroup:
            matches = control.getRepoTrovesFromCookedGroup()
            unmatched = []
        else:
            control.loadControlFile()
            matches, unmatched = control.getMatchedRepoTroves(
                                                    allowVersionMismatch=True)

        self.csList = []
        trovesByName = {}

        if fromcspath:
            for troveName in control.getSourceList():
                trovesByName[troveName] = control.getSourceIds(troveName)
        elif getFromCookedGroup:
            for trove in matches:
                name = trove.getName()
                if name not in trovesByName:
                    trovesByName[name] = [trove]
                else:
                    trovesByName[name].append(trove)
        else:
            desTroves = control.getDesiredTroveList() 
            for desTrove in desTroves:
                desSourceId = control.getDesiredTroveSourceId(*desTrove)
                if desSourceId is None:
                    print "Skipping %s..." % desTrove[0]
                    continue
                if desTrove[0] in trovesByName:
                    trovesByName[desTrove[0]].append(desSourceId)
                else:
                    trovesByName[desTrove[0]] = [desSourceId]

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
            if pkg not in matches:
                # we just skip these packages
                csfile = "%s-%s.ccs" % (troveName, 
                                pkg.getVersion().trailingVersion().asString())
                path = "%s/%s" % (csdir, csfile)
                print >> sys.stderr, "%d/%d: skipping %s" % (index, l, csfile)
                index += 1
                continue
            dispName = troveName
            if getFromCookedGroup:
                if troveName == 'kernel':
                    if '~!kernel.smp' not in str(flavor):
                        dispName += '-smp'
                troveId = pkg
            else:
                troveId = pkg.getTroveId()
            csfile = "%s-%s.ccs" % (dispName, 
                        troveId.getVersion().trailingVersion().asString())
            path = "%s/%s" % (csdir, csfile)

            # link the first matching path, assuming they are ordered
            # so that latest is first
            if oldFiles.has_key(path):
                print >> sys.stderr, "%d/%d: keeping old %s" % (index, l, 
                                                                   csfile)
                del oldFiles[path]
            elif fromcspath:
                print >> sys.stderr, "%d/%d: linking %s" % (index, l, csfile)
                try:
                    os.link(troveId.getPath(), path)
                except OSError, msg:
                    if msg.errno != errno.EXDEV:
                        raise
                    shutil.copyfile(cspkg.getPath(), path)
            else:
                # the trove is still waiting in the repo
                print >> sys.stderr, "%d/%d: extracting %s" % (index, l, csfile)
                troveId.createChangeSet(path, self.repos, component=troveName)

            cs = changeset.ChangeSetFromFile(path)
            name = pkg.getName()
            trailing = troveId.getVersion().trailingVersion().asString()
            v = trailing.split('-')
            version = '-'.join(v[:-2])
            release = '-'.join(v[-2:])
            size = 0
            # calculate size when installed 

            for pkgCs in cs.iterNewPackageList():
                for (pathId, fPath, fileId, fVer) in pkgCs.getNewFileList():
                    fileObj = files.ThawFile(cs.getFileChange(None, fileId), 
                                                                        pathId)
                    if fileObj.hasContents:
                        size += fileObj.contents.size()
            self.csInfo[troveName, pkg] = {'path': path, 'size': size, 
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
                        troveName, info['version'], info['release'], info['size'], d
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
        map = { 'pname' : self.distro.productName,
                'ppath' : self.distro.productPath,
                'arch' : self.distro.arch, 
                'discno' : iso.discno, 'isodir' : iso.builddir, 
                'scripts': self.anacondascripts } 
        os.system('python %(scripts)s/makestamp.py --releasestr="%(pname)s" --arch="%(arch)s" --discNum="%(discno)s" --baseDir=%(ppath)s/base --packagesDir=%(ppath)s/changesets --pixmapsDir=%(ppath)s/pixmaps --outfile=%(isodir)s/.discinfo' %  map)
        stampLines = open('%s/.discinfo' % iso.builddir).readlines()
        iso.markInstalled('%s/.discinfo' % iso.builddir)
        for iso in self.isos[1:]:
            stampFile = open('%s/.discinfo' % iso.builddir, 'w')
            stampLines[3] = str(iso.discno) + '\n'
            stampFile.write(''.join(stampLines))
            stampFile.close()
            iso.markInstalled('%s/.discinfo' % iso.builddir)


    def makeInstRoots(self, useAnaconda=True):
        """ Do a lot of anaconda related stuff.  I don't know what 
            most of this does, except that it is important for anaconda
        """
        ciso = self.isos[0]
        os.environ['PYTHONPATH'] = os.environ.get('CONARY_PATH', 
                                                  '/usr/share/conary')
        os.environ['CONARY'] = 'conary'
        isodir = ciso.builddir
        ppath = self.distro.productPath
        csdir = os.path.join(self.subdir, 'changesets')
        basedir = '/'.join((isodir, ppath,'base'))
        compspath = basedir + '/comps.xml'
        util.mkdirChain(basedir)
        compsfile = open(compspath, 'w')
        compsfile.write('''<?xml version="1.0"?>
<!DOCTYPE comps PUBLIC "-//Red Hat, Inc.//DTD Comps info//EN" "comps.dtd">
<comps>
  <group>
    <id>base</id>
    <name>Base</name>
  </group>
  <group>
    <id>core</id>
    <name>Core</name>
  </group>
</comps>
''')
        compsfile.close()
        
        # just touch these files
        open(basedir + '/hdlist', 'w')
        open(basedir + '/hdlist2', 'w')
        # the next part takes way to long for a test case, so 
        # if we are just testing, skip it.
        if not useAnaconda:
            ciso.markDirInstalled('/%s/base/' % ppath)
            return
        # install anaconda into a root dir
        self.anacondadir = tempfile.mkdtemp('', 'anaconda-', self.buildpath)
        oldroot = self.cfg.root
        self.cfg.root = self.anacondadir
        updatecmd.doUpdate(self.cfg, ['anaconda'], depCheck=False)
        self.cfg.root = oldroot
        self.anacondascripts = os.path.join(self.anacondadir, 'usr/lib/anaconda-runtime')
        instroot = tempfile.mkdtemp('', 'bs-bd-instroot', self.buildpath)
        instrootgr = tempfile.mkdtemp('', 'bs-bd-instrootgr', self.buildpath)
        map = { 'pname' : self.distro.productName,
                'arch' : self.distro.arch, 
                'csdir' : csdir,
                'ppath' : self.distro.productPath, 
                'isodir' : isodir, 
                'scripts': self.anacondascripts,
                'instroot' : instroot, 'instrootgr' : instrootgr,
                'version' : self.distro.version } 
        sys.stdout.flush()
        sys.stderr.flush()
        if self.logdir:
            logfile = self.logdir + '/upd-instroot'
            logpath = os.path.join(self.logdir, logfile)
            logfd = os.open(logpath, os.O_TRUNC | os.O_WRONLY | os.O_CREAT)
        try:
            if self.logdir:
                stdout = os.dup(sys.stdout.fileno())
                stderr = os.dup(sys.stderr.fileno())
                os.dup2(logfd, sys.stdout.fileno())
                os.dup2(logfd, sys.stderr.fileno())
                os.close(logfd)
            cmd = 'sh -x %(scripts)s/upd-instroot --debug --conary %(csdir)s %(instroot)s %(instrootgr)s' % map
            print "\n\n*********** RUNNING UPD-INSTROOT ***************\n\n"
            print cmd
            rc = os.system(cmd)
            print "<<Result code: %d>>" % rc
            sys.stdout.flush()
            sys.stderr.flush()

            ## okay now output mk-images to another log file
            if self.logdir:
                logfile = 'mk-images'
                logpath = os.path.join(self.logdir, logfile)
                logfd = os.open(logpath, os.O_TRUNC | os.O_WRONLY | os.O_CREAT)
                os.dup2(logfd, sys.stdout.fileno())
                os.dup2(logfd, sys.stderr.fileno())
                os.close(logfd)
            print "\n\n*********** RUNNING mk-images ***************\n\n"
            cmd = ('%(scripts)s/mk-images --debug --conary %(csdir)s %(isodir)s %(instroot)s %(instrootgr)s %(arch)s "%(pname)s" %(version)s %(ppath)s' % map)
            print cmd
            sys.stdout.flush()
            sys.stderr.flush()
            rc = os.system(cmd)
            print "<<Result code: %d>>" % rc
            sys.stdout.flush()
            sys.stderr.flush()
        except: 
            if self.logdir:
                os.dup2(stdout, sys.stdout.fileno())
                os.dup2(stderr, sys.stderr.fileno())
            raise
        if self.logdir:
            os.dup2(stdout, sys.stdout.fileno())
            os.dup2(stderr, sys.stderr.fileno())
        util.rmtree(instroot)
        util.rmtree(instrootgr)
        ciso.markDirInstalled('/isolinux')
        ciso.markDirInstalled('/images')
        ciso.markDirInstalled('/%s/base/' % ppath)

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
            for path in 'images', 'isolinux', 'Specifix/base':
                util.mkdirChain('%s/%s' % (self.nfspath, path))
                util.execute('cp -arf %s/%s/* %s/%s' % (self.isos[0].builddir, 
                                        path, self.nfspath, path))
        self.writeCsList(self.nfspath, overrideDisc=1)
        if self.tftpbootpath is not None:
            print "Copying boot images to %s" % self.tftpbootpath
            util.mkdirChain(self.tftpbootpath)
            util.execute('cp -arf %s/isolinux/{initrd.img,vmlinuz} %s' % \
                        (self.isos[0].builddir, self.tftpbootpath))
