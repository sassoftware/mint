import files
from lib import util
from iso import ISO, DiskFullError
import os
import os.path
from pkgid import PkgId, thawPackage
from repository import changeset
import shutil
import sys
import tempfile
import time
import trovelist
import updatecmd

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
    def __init__(self, repos, cfg, distro, buildpath, isopath, fromcspath):
        self.repos = repos
        self.cfg = cfg
        self.buildpath = buildpath
        self.isopath = isopath
        self.distro = distro
        # Place to look for Changesets that have already been made
        self.fromcspath = fromcspath

    def create(self):
        self.topdir = '%s/%s' % (self.buildpath, self.distro.isoname)
        #if os.path.exists(self.topdir):
        #    util.rmtree(self.topdir)
        util.mkdirChain(self.topdir)
        self.subdir = self.topdir + '/' + self.distro.productPath
        util.mkdirChain(os.path.join(self.subdir, 'changesets'))
        self.createChangeSets(os.path.join(self.subdir, 'changesets'), self.fromcspath)
        self.initializeCDs()
        self.writeCsList()
        self.makeInstRoots()
        for iso in self.isos:
            self.stampIso(iso)
            iso.create()

    def initializeCDs(self):
        isopath = os.path.join(self.isopath, self.distro.isoname)
        isopath += '-disc%d.iso'
        self.isos = []
        discno = 1
        builddir = self.topdir + '/disc%d'
        isoname = self.distro.isoname + ' Disc %d'
        ciso = ISO(builddir % discno, isopath % discno, isoname % discno, discno, bootable=True)
        ciso.discno = discno
        # reserve 40MB on the first disc for use later
        ciso.reserve(40) 
        self.isos.append(ciso)
        pkgs = self.csInfo.keys()
        pkgs.sort()
        ciso = self.isos[-1]
        
        csdir = '/'.join(('',self.distro.productPath, 'changesets'))
        for pkg in pkgs:
            info = self.csInfo[pkg]
            try:
                curfilepath = info['path']
                isofilepath = os.path.join(csdir, os.path.basename(info['path']))
                ciso.addFile(isofilepath, curfilepath)
            except DiskFullError:
                discno += 1
                ciso = ISO(builddir % discno, isopath % discno, isoname % discno, discno)
                self.isos.append(ciso)
                ciso.addFile(isofilepath, curfilepath)
                
    def createChangeSets(self, csdir, fromcspath):
        self.csInfo = {}

        oldFiles = {}
        for path in [ "%s/%s" % (csdir, x) for x in os.listdir(csdir) ]:
            oldFiles[path] = 1

        #'/data/test-buildsystem/buildroot/stage2/tmp/cs'
        #csTrvList = trovelist.ChangeSetDirTroveList(fromcspath, self.cfg.installLabelPath[0], self.repos)
        #csTrvList = trovelist.GroupTroveList('group-dist', self.cfg.installLabelPath[0], self.cfg.flavor, self.repos)
        #controlFile = controlfile.ControlFile(repos, self.cfg)
        #troveList = controlFile.getDesiredTroveList()

        trvList = self.repos.findTrove(self.cfg.installLabelPath[0], "group-dist", self.cfg.flavor)
        if not trvList:
            print "no match for group-dist"
            sys.exit(0)
        elif len(trvList) > 1:
            print "multiple matches for group-dist"
            sys.exit(0)
        groupTrv = trvList[0]
        troves = {}
        trovesByName = {}
        for (name, version, flavor) in groupTrv.iterTroveList():
            # XXX Hack until I've got flavors / group-dist:source hooked up
            flavor = None
            if pkg.name == "kernel" or pkg.name == 'kernel-source':
                if "kernel.smp" not in str(pkg.flavor):
                    flavor = deps.DependencySet()
                    dep = deps.Dependency('use', ['!kernel.smp'])
                    flavor.addDep(deps.UseDependency, dep)
            pkg = PkgId(name, version, flavor, justName=True)
            troves[pkg] = True
            if name in trovesByName:
                trovesByName[name].append(pkg)
            else:
                trovesByName[name] = [pkg]

        list = []
        for name in [ 'setup', 'glibc' ]:
            for pkg in trovesByName[name]:
                list.append(pkg)
            del trovesByName[name]

        names = trovesByName.keys()
        names.sort()
        for name in names:
            for pkg in trovesByName[name]:
                list.append(pkg)

        l = len(list)
        print "Creating %d packages" % len(list)
        index = 0
        for pkg in list:
            dispName = pkg.name
            if pkg.name == "kernel" or pkg.name == 'kernel-source':
                if "!kernel.smp" not in str(pkg.flavor):
                    dispName += '-smp'

            csfile = "%s-%s.ccs" % (dispName, pkg.version.trailingVersion().asString())
            path = "%s/%s" % (csdir, csfile)

            if oldFiles.has_key(path):
                print >> sys.stderr, "%d/%d: keeping old %s" % (index, l, csfile)
                del oldFiles[path]
            else:
                # XXX problem:
                # Filenames / pkg strings could either contain 
                # 1) all information about the cs
                #    In this case we need to weed out on use-time
                #    information that doesn't affect whether the cs
                #    matches the group-dist specification
                #    This makes the check to see if a package has already
                #    been built much more than simply 
                # 2) information about the cs that matches it to a
                #    specific group-dist.  This is easier bc we know 
                #    that information without needing to load the cs...
                #    otherwise we might need to cook it to a temp file and
                #    move it based on the cs's contents.
                #
                # group-dist contains information about *built packages*
                # but, what we want is information about the *desired qualities*
                # of pkgs...we could store all the information about the cs
                # in its filename, or we could store the desired qualities.
                # E.g. do we store the fact that this is the third rebuild
                # of the changeset in the name?  
                # XXX hack until file names match build system and group-dist
                # Might have to load group-dist:source here to figure out 
                # what matches watch
                from lib import epdb
                epdb.set_trace()
                if dispName != 'kernel-smp':
                    sourcepkg = 

                frompath = os.path.join(fromcspath, pkg + '.ccs')
                if os.path.exists(frompath):
                    print >> sys.stderr, "%d/%d: linking %s" % (index, l, csfile)
                    os.link(frompath, path)
                else:
                    print >> sys.stderr, "%d/%d: creating %s" % (index, l, csfile)
                    self.repos.createChangeSetFile(
                        [(pkg.name, (None, pkg.flavor), (pkg.version, pkg.flavor), True)], path)
            cs = changeset.ChangeSetFromFile(path)
            pkgs = cs.primaryTroveList
            if len(pkgs) > 1:
                sys.stderr.write("Unable to handle changeset file %s with more "
                                 "than one primary package\n", fn)
                sys.exit(1)
            pkg = PkgId(pkgs[0][0], pkgs[0][1], pkgs[0][2], justName=True)
            name = pkg.name
            trailing = pkg.version.trailingVersion().asString()
            v = trailing.split('-')
            version = '-'.join(v[:-2])
            release = '-'.join(v[-2:])
            size = 0
            for (fileId, (old, new, stream)) in cs.getFileList():
                fileObj = files.ThawFile(stream, fileId)
                if fileObj.hasContents:
                    size += fileObj.contents.size()
            # size on installed machine
            self.csInfo[pkg] = {'path': path, 'size': size, 'version' : version, 'release' : release}
            index += 1

    def writeCsList(self):
        path = '/'.join((self.isos[0].builddir, self.distro.productPath, 'base/cslist'))
        util.mkdirChain(os.path.dirname(path))
        csfile = open(path, 'w')
        pkgs = self.csInfo.keys()
        pkgs.sort()
        for pkg in pkgs:
            info = self.csInfo[pkg]
            print >> csfile, os.path.basename(info['path']), pkg.name, info['version'], info['release'], info['size']
        self.isos[0].addFile('/' + self.distro.productPath + '/base/cslist')

    def stampIso(self, iso):
        isodir = self.isos[0].builddir
        subdir = os.path.join(isodir, self.distro.productPath)
        map = { 'pname' : self.distro.productName,
                'ppath' : self.distro.productPath,
                'arch' : self.distro.arch, 
                'discno' : iso.discno, 'isodir' : isodir, 
                'scripts': self.anacondascripts } 
        os.system('python %(scripts)s/makestamp.py --releasestr="%(pname)s" --arch="%(arch)s" --discNum="%(discno)s" --baseDir=%(ppath)s/base --packagesDir=%(ppath)s/changesets --pixmapsDir=%(ppath)s/pixmaps --outfile=%(isodir)s/.discinfo' %  map)

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
</comps>''')
        compsfile.close()
        
        # just touch these files
        open(basedir + '/hdlist', 'w')
        open(basedir + '/hdlist2', 'w')
        # install anaconda into a root dir
        self.anacondadir = tempfile.mkdtemp('', 'anaconda-', self.buildpath)
        oldroot = self.cfg.root
        self.cfg.root = self.anacondadir
        updatecmd.doUpdate(self.repos, self.cfg, ['anaconda'])
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
