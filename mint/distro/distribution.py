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
from pkgid import PkgId, thawPackage
import controlfile
import trovelist

class DistroInfo:
    def __init__(self, abbrevName, productPath, productName, version, phase, isoname=None, arch='i386', nightly=False):
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
                nfspath, tftpbootpath, fromcspath, logdir, clean=False):
        self.repos = repos
        self.cfg = cfg
        self.buildpath = buildpath
        self.logdir = logdir
        self.tftpbootpath = tftpbootpath
        if distro.nightly:
            buildpath = os.path.join(buildpath,'nightly')
            nfspath = os.path.join(nfspath,'nightly')
        self.buildpath = os.path.join(buildpath, distro.version)
        self.nfspath = os.path.join(nfspath, distro.version)
        self.isopath = isopath
        self.distro = distro
        # Place to look for Changesets that have already been made
        self.controlGroup = controlGroup
        self.fromcspath = fromcspath

    def create(self):
        self.topdir = '%s/%s' % (self.buildpath, self.distro.isoname)
        if os.path.exists(self.topdir):
            util.rmtree(self.topdir)
        util.mkdirChain(self.topdir)
        self.subdir = self.topdir + '/' + self.distro.productPath
        util.mkdirChain(os.path.join(self.subdir, 'changesets'))
        self.createChangeSets(self.controlGroup, os.path.join(self.subdir, 'changesets'), self.fromcspath)
        self.initializeCDs()
        self.writeCsList(self.isos[0].builddir)
        self.makeInstRoots()
        self.stampIsos()
        for iso in self.isos:
            iso.create()
        if self.nfspath:
            self.copyToNFS()

    def copyToNFS(self):
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

    def initializeCDs(self):
        isopath = os.path.join(self.isopath, self.distro.isoname)
        isopath += '-disc%d.iso'
        self.isos = []
        discno = 1
        # don't substitute in discno so that this same string can be used
        # later
        builddir = '%s/%s-disc%%d' % (self.buildpath, self.distro.isoname) 
        isoname = self.distro.isoname + ' Disc %d'
        ciso = ISO(builddir % discno, isopath % discno, isoname % discno, discno, bootable=True)
        ciso.discno = discno
        # reserve 40MB on the first disc for use later
        ciso.reserve(40) 
        self.isos.append(ciso)
        ciso = self.isos[-1]
        
        csdir = '/'.join(('',self.distro.productPath, 'changesets'))
        for pkg in self.csList:
            if pkg not in self.csInfo:
                print "Skipping %s in initializeCDs"  % pkg
                continue
            info = self.csInfo[pkg]
            try:
                curfilepath = info['path']
                isofilepath = os.path.join(csdir, os.path.basename(info['path']))
                ciso.addFile(isofilepath, curfilepath)
                info['disc'] = ciso.discno
            except DiskFullError:
                discno += 1
                ciso = ISO(builddir % discno, isopath % discno, isoname % discno, discno)
                self.isos.append(ciso)
                ciso.addFile(isofilepath, curfilepath)
                info['disc'] = ciso.discno

            
    def createChangeSets(self, group, csdir, fromcspath):
        self.csInfo = {}
        oldFiles = {}
        for path in [ "%s/%s" % (csdir, x) for x in os.listdir(csdir) ]:
            oldFiles[path] = 1

        control = controlfile.ControlFile(group, self.repos, self.cfg, self.cfg.installLabelPath[0]) 
        control.loadControlFile()
        print "Matching changesets..."
        matches, unmatched = control.getMatchedChangeSets(fromcspath)
        trovesByName = control.sources.copy()
        l = len(trovesByName)
        self.csList = []
        for name in [ 'setup', 'glibc' ]:
            for pkg in trovesByName[name]:
                self.csList.append(pkg)
            del trovesByName[name]

        names = trovesByName.keys()
        names.sort()
        index = 0
        for name in names:
            self.csList.extend(trovesByName[name])
        for pkg in self.csList:
            dispName = pkg.name
            # XXX hack to add in flavor, since it is not 
            # listed in group-dist
            
            if pkg in matches:
                dispName = pkg.name
                if pkg.name in ('kernel' or 'kernel-source'): 
                    if "!kernel.smp" not in str(pkg.flavor):
                        dispName += '-smp'
                    
                cspkg = pkg.cspkgs.keys()[0]
                csfile = "%s-%s.ccs" % (dispName, cspkg.version.trailingVersion().asString())
                path = "%s/%s" % (csdir, csfile)

                # link the first matching path, assuming they are ordered
                # so that latest is first
                if oldFiles.has_key(path):
                    print >> sys.stderr, "%d/%d: keeping old %s" % (index, l, csfile)
                    del oldFiles[path]
                else:
                    print >> sys.stderr, "%d/%d: linking %s" % (index, l, csfile)
                    try:
                        os.link(cspkg.file, path)
                    except OSError, msg:
                        if msg.errno != errno.EXDEV:
                            raise
                        shutil.copyfile(cspkg.file, path)
            else:
                csfile = "%s-%s.ccs" % (pkg.name, pkg.version.trailingVersion().asString())
                path = "%s/%s" % (csdir, csfile)

                print >> sys.stderr, "%d/%d: skipping %s" % (index, l, csfile)
                continue
                print >> sys.stderr, "%d/%d: creating %s" % (index, l, pkg)
                version = control.getDesiredCompiledVersion(pkg)
                self.repos.createChangeSetFile(
                    [(pkg.name, (None, pkg.flavor), (version, pkg.flavor), True)], path)
            cs = changeset.ChangeSetFromFile(path)
            #pkgs = cs.primaryTroveList
            #if len(pkgs) > 1:
            #    sys.stderr.write("Unable to handle changeset file %s with more "
            #                     "than one primary package\n", path)
            #    sys.exit(1)
            #cspkg = PkgId(pkgs[0][0], pkgs[0][1], pkgs[0][2], justName=True)
            name = pkg.name
            trailing = cspkg.version.trailingVersion().asString()
            v = trailing.split('-')
            version = '-'.join(v[:-2])
            release = '-'.join(v[-2:])
            size = 0
            # calculate size when installed 
            for (fileId, (old, new, stream)) in cs.getFileList():
                fileObj = files.ThawFile(stream, fileId)
                if fileObj.hasContents:
                    size += fileObj.contents.size()
            self.csInfo[pkg] = {'path': path, 'size': size, 'version' : version, 
                                'release' : release}
            index += 1

    def writeCsList(self, basepath, overrideDisc=None):
        path = '/'.join((basepath, self.distro.productPath, 'base/cslist'))
        util.mkdirChain(os.path.dirname(path))
        csfile = open(path, 'w')
        for pkg in self.csList:
            if pkg in self.csInfo:
                info = self.csInfo[pkg]
                if overrideDisc is None:
                    d = info['disc']
                else:
                    d = overrideDisc
                print >> csfile, os.path.basename(info['path']), pkg.name, info['version'], info['release'], info['size'], d
        if not overrideDisc:
            self.isos[0].addFile('/' + self.distro.productPath + '/base/cslist')

    def stampIsos(self):
        iso = self.isos[0]
        map = { 'pname' : self.distro.productName,
                'ppath' : self.distro.productPath,
                'arch' : self.distro.arch, 
                'discno' : iso.discno, 'isodir' : iso.builddir, 
                'scripts': self.anacondascripts } 
        os.system('python %(scripts)s/makestamp.py --releasestr="%(pname)s" --arch="%(arch)s" --discNum="%(discno)s" --baseDir=%(ppath)s/base --packagesDir=%(ppath)s/changesets --pixmapsDir=%(ppath)s/pixmaps --outfile=%(isodir)s/.discinfo' %  map)
        stampLines = open('%s/.discinfo' % iso.builddir).readlines()
        for iso in self.isos[1:]:
            stampFile = open('%s/.discinfo' % iso.builddir, 'w')
            stampLines[3] = str(iso.discno) + '\n'
            stampFile.write(''.join(stampLines))
            stampFile.close()

    def makeInstRoots(self):
        os.environ['PYTHONPATH'] = '/home/dbc/spx/cvs/conary'
        os.environ['CONARY'] = 'conary'
        os.environ['CONARY_PATH'] = '/home/dbc/spx/cvs/conary'
        isodir = self.isos[0].builddir
        ppath = self.distro.productPath
        subdir = os.path.join(isodir, ppath)
        basedir = '/'.join((isodir, ppath,'base'))
        path = basedir + '/comps.xml'
        compsfile = open(path, 'w')
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
                'arch' : self.distro.arch, 'subdir' : subdir,
                'ppath' : self.distro.productPath, 
                'isodir' : isodir, 
                'scripts': self.anacondascripts,
                'instroot' : instroot, 'instrootgr' : instrootgr,
                'version' : self.distro.version } 
        try:
            os.system('sh -x %(scripts)s/upd-instroot --debug --conary %(subdir)s/changesets %(instroot)s %(instrootgr)s' % map)
            os.system('%(scripts)s/mk-images --debug --conary %(subdir)s/changesets %(isodir)s %(instroot)s %(instrootgr)s %(arch)s "%(pname)s" %(version)s %(ppath)s' % map)
        finally:
            util.rmtree(instroot)
            util.rmtree(instrootgr)
