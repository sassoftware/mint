
from repository import changeset
import files
from lib import util
import time
import os
import os.path
import sys
import tempfile
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

class ISO:
    def __init__(self, repos, cfg, distro, buildpath, isopath):
        self.repos = repos
        self.cfg = cfg
        self.buildpath = buildpath
        self.isopath = isopath
        self.distro = distro

    def create(self):
        self.topdir = '%s/%s' % (self.buildpath, self.distro.isoname)
        #if os.path.exists(self.topdir):
        #    util.rmtree(self.topdir)
        util.mkdirChain(self.topdir)
        self.subdir = self.topdir + '/' + self.distro.productPath
        util.mkdirChain(os.path.join(self.subdir, 'changesets'))
        util.mkdirChain(os.path.join(self.subdir, 'base'))
        self.createChangeSets(os.path.join(self.subdir, 'changesets'))
        self.writeCsList()
        self.makeInstRoots()
        self.createISO()

    def createISO(self):
        from lib import epdb
        epdb.set_trace()
        os.system('cd %s; mkisofs -o %s/%s -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -R -J -V "%s" -T .' % (self.topdir, self.isopath, self.distro.isoname, self.distro.productName))
        os.system('/home/msw/implantisomd5 %s/%s' % (self.isopath, self.distro.isoname))

    def createChangeSets(self, csdir):
        self.csList = []

        oldFiles = {}
        for path in [ "%s/%s" % (csdir, x) for x in os.listdir(csdir) ]:
            oldFiles[path] = 1

        fromcspath = '/data/test-buildsystem/buildroot/stage2/tmp'
        csTrvList = trovelist.ChangeSetDirTroveList(fromcspath)

        trvList = self.repos.findTrove(self.cfg.installLabelPath[0], "group-dist", self.cfg.flavor)
        if not trvList:
            print "no match for group-dist"
            sys.exit(0)
        elif len(trvList) > 1:
            print "multiple matches for group-dist"
            sys.exit(0)
        groupTrv = trvList[0]
        troves = {}
        for (name, version, flavor) in groupTrv.iterTroveList():
            if name in troves:
                troves[name].append((version, flavor))
            else:
                troves[name] = [(version, flavor)]
        list = []
        for name in [ 'setup', 'glibc' ]:
            for t in troves[name]:
                list.append((name, t))
            del troves[name]

        for name, l in troves.items():
            for t in l:
                list.append((name, t))
        csVersions = csTrvList.getTroveNameVersions()
        for (name, (version, flavor)) in list:
            path = "%s/%s-%s.ccs" % (csdir, name, version.trailingVersion().asString())

            if oldFiles.has_key(path):
                del oldFiles[path]
            elif version in csVersions[name]:
                frompath = os.path.join(fromcspath, hashrvname(name, version))
                shutil.copy(frompath, path)
            else:
                print >> sys.stderr, "creating", path
                self.repos.createChangeSetFile(
                    [(name, (None, flavor), (version, flavor), True)], path)
            cs = changeset.ChangeSetFromFile(path)
            pkgs = cs.primaryTroveList
            if len(pkgs) > 1:
                sys.stderr.write("Unable to handle changeset file %s with more "
                                 "than one primary package\n", fn)
                sys.exit(1)
            pkg = pkgs[0]
            name = pkg[0]
            trailing = pkg[1].trailingVersion().asString()
            v = trailing.split('-')
            version = '-'.join(v[:-2])
            release = '-'.join(v[-2:])

            size = 0
            for (fileId, (old, new, stream)) in cs.getFileList():
                fileObj = files.ThawFile(stream, fileId)
                if fileObj.hasContents:
                    size += fileObj.contents.size()

            self.csList.append([os.path.basename(path), name, version, release, size])

    def writeCsList(self):
        path = os.path.join(self.subdir, 'base/cslist')
        csfile = open(path, 'w')
        for (filename, name, version, release, size) in self.csList:
            print >> csfile, filename, name, version, release, size

    def makeInstRoots(self):
        os.environ['PYTHONPATH'] = '/home/dbc/spx/cvs/conary'
        os.environ['CONARY'] = 'conary'
        os.environ['CONARY_PATH'] = '/home/dbc/spx/cvs/conary'
        compsfile = open(self.subdir + '/base/comps.xml', 'w')

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
        open(self.subdir + '/base/hdlist', 'w')
        open(self.subdir + '/base/hdlist2', 'w')
        # install anaconda into a root dir
        self.anacondadir = tempfile.mkdtemp('', 'anaconda-')
        oldroot = self.cfg.root
        self.cfg.root = self.anacondadir
        updatecmd.doUpdate(self.repos, self.cfg, ['anaconda'])
        self.cfg.root = oldroot
        self.anacondascripts = os.path.join(self.anacondadir, 'usr/lib/anaconda-runtime')
        instroot = tempfile.mkdtemp('', 'bs-bd-instroot')
        instrootgr = tempfile.mkdtemp('', 'bs-bd-instrootgr')
        os.system('sh -x %s/upd-instroot --debug --conary %s/changesets %s %s' % (self.anacondascripts, self.subdir, instroot, instrootgr))
        os.system('%s/mk-images --debug --conary %s/changesets %s %s %s %s "%s" %s %s' % (self.anacondascripts, self.subdir, self.topdir, instroot, instrootgr,
          self.distro.arch, self.distro.productPath, self.distro.version, self.subdir))
        os.system('python %s/makestamp.py --releasestr="%s" --arch=%s --discNum="1" --baseDir=%s/base --packagesDir=%s/changesets --pixmapsDir=%s/pixmaps --outfile=%s/.discinfo' % (self.anacondascripts, self.distro.productName, self.distro.arch, self.distro.productPath, self.distro.productPath, self.distro.productPath, self.topdir))
        util.rmtree(instroot)
        util.rmtree(instrootgr)
