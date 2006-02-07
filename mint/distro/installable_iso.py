#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#
import os
import re
import subprocess
import string
import sys
import tempfile
import time
from anaconda_images import AnacondaImages

from conary import callbacks
from conary import conaryclient
from conary import conarycfg
from conary import deps
from conary import versions
from conary.repository import errors
from conary.build import use
from conary.conarycfg import ConfigFile
from conary.lib import util

from flavors import stockFlavors
from mint.mint import upstream
from imagegen import ImageGenerator, assertParentAlive
import gencslist

class IsoConfig(ConfigFile):
    filename = 'installable_iso.conf'
    
    imagesPath          = None
    scriptPath          = '/usr/share/mint/scripts/'
    cachePath           = '/srv/mint/changesets/'
    templatePath        = '/srv/mint/templates/'
    implantIsoMd5       = '/usr/lib/anaconda-runtime/implantisomd5'
    anacondaImagesPath  = '/usr/share/mint/pixmaps'


class AnacondaTemplateMissing(Exception):
    def __init__(self, arch = "arch"):
        self._arch = arch
        
    def __str__(self):
        return "Anaconda template missing for architecture: %s" % self._arch


class Callback(callbacks.UpdateCallback, callbacks.ChangesetCallback):
    def requestingChangeSet(self):
        self._update('requesting %s from repository')

    def downloadingChangeSet(self, got, need):
        if need != 0:
            self._update('downloading %%s from repository (%d%%%% of %dk)'
                         %((got * 100) / need, need / 1024))

    def downloadingFileContents(self, got, need):
        if need != 0:
            self._update('downloading files for %%s from repository '
                         '(%d%%%% of %dk)' %((got * 100) / need, need / 1024))

    def _update(self, msg):
        # only push an update into the database if it differs from the
        # current message
        if self.msg != msg:
            self.msg = msg
            self.status(self.prefix + msg % self.changeset)

    def setChangeSet(self, name):
        self.changeset = name

    def setPrefix(self, prefix):
        self.prefix = prefix

    def __init__(self, status):
        self.abortEvent = None
        self.status = status
        self.restored = 0
        self.msg = ''
        self.changeset = ''
        self.prefix = ''


def _linkRecurse(fromDir, toDir):
    for root, dirs, files in os.walk(fromDir):
        for dir in dirs:
            newRoot = toDir + root[len(fromDir):]
            util.mkdirChain(os.path.join(newRoot, dir))
        for file in files:
            newRoot = toDir + root[len(fromDir):]
            src = os.path.join(root, file)
            dest = os.path.join(newRoot, file)
            gencslist._linkOrCopyFile(src, dest)


def call(*cmds):
    print >> sys.stderr, " ".join(cmds)
    sys.stderr.flush()
    subprocess.call(cmds)


class InstallableIso(ImageGenerator):
    configObject = IsoConfig

    def _getUpdateJob(self, cclient, troveName):
        self.callback.setChangeSet(troveName)
        try:
            itemList = [(troveName, (None, None), (None, None), True)]
            uJob, suggMap = cclient.updateChangeSet(itemList,
                resolveDeps = False,
                callback = self.callback)
        except errors.TroveNotFound:
            return None
        return uJob

    def writeProductImage(self, arch):
        # write the product.img cramfs
        productPath = os.path.join(self.baseDir, "product.img")
        tmpPath = tempfile.mkdtemp()

        # write .buildstamp
        bsFile = open(os.path.join(tmpPath, ".buildstamp"), "w")
        print >> bsFile, time.time()
        print >> bsFile, self.project.getName()
        print >> bsFile, upstream(self.release.getTroveVersion())
        print >> bsFile, self.subdir
        print >> bsFile, self.release.getDataValue("bugsUrl")
        print >> bsFile, "%s %s %s" % (self.release.getTroveName(),
                                       self.release.getTroveVersion().asString(),
                                       self.release.getTroveFlavor().freeze())
        bsFile.close()

        # extract anaconda-images from repository, if exists
        tmpRoot = tempfile.mkdtemp()
        if not self.project.external:
            cfg = self.project.getConaryConfig(overrideSSL = True, overrideAuth = True, 
                newUser='mintauth', newPass='mintpass', useSSL = self.cfg.SSL) 
            cfg.root = tmpRoot
            cfg.dbPath = tmpRoot + "/var/lib/conarydb/conarydb"
            cfg.installLabelPath = [self.version.branch().label()]
            cfg.buildFlavor = deps.deps.parseFlavor(stockFlavors[arch])
            cfg.flavor = [cfg.buildFlavor]
            cfg.initializeFlavors()

            cclient = conaryclient.ConaryClient(cfg)

            uJob = None
            print >> sys.stderr, "extracting artwork from anaconda-custom=%s" % cfg.installLabelPath[0].asString()
            uJob = self._getUpdateJob(cclient, "anaconda-custom")
            if not uJob:
                print >> sys.stderr, "anaconda-custom not found on repository, falling back to anaconda-images"
                uJob = self._getUpdateJob(cclient, "anaconda-images")

            util.mkdirChain(tmpPath + '/pixmaps')
            if uJob:
                cclient.applyUpdate(uJob, callback = self.callback)
                print >> sys.stderr, "success."
                sys.stderr.flush()

                # copy pixmaps and scripts into cramfs root
                tmpTar = tempfile.mktemp(suffix = '.tar')
                call('tar', 'cf', tmpTar, '-C', tmpRoot + '/usr/share/anaconda/', './')
                call('tar', 'xf', tmpTar, '-C', tmpPath)
                call('rm', tmpTar)
            elif not self.project.external:
                print >> sys.stderr, "anaconda-images not found on repository either, using generated artwork."
                ai = AnacondaImages(self.project.getName(), indir = self.isocfg.anacondaImagesPath,
                        outdir = tmpPath + '/pixmaps',
                        fontfile = '/usr/share/fonts/bitstream-vera/Vera.ttf')
                ai.processImages()

            # convert syslinux-splash.png to splash.lss, if exists
            if os.path.exists(tmpPath + '/pixmaps/syslinux-splash.png'):
                print >> sys.stderr, "found syslinux-splash.png, converting to splash.lss"

                splash = file(tmpPath + '/pixmaps/splash.lss', 'w')
                palette = [] # '#000000=0', '#cdcfd5=7', '#c90000=2', '#ffffff=15', '#5b6c93=9']
                pngtopnm = subprocess.Popen(['pngtopnm', tmpPath + '/pixmaps/syslinux-splash.png'], stdout = subprocess.PIPE)
                ppmtolss16 = subprocess.Popen(['ppmtolss16'] + palette, stdin = pngtopnm.stdout, stdout = splash)
                ppmtolss16.communicate()

            # copy the splash.lss files to the appropriate place
            if os.path.exists(tmpPath + '/pixmaps/splash.lss'):
                print >> sys.stderr, "found splash.lss; moving to isolinux directory"
                splashTarget = os.path.join(self.topdir, 'isolinux')
                call('cp', '--remove-destination', '-v', tmpPath + '/pixmaps/splash.lss', splashTarget)
                # FIXME: regenerate boot.iso here
        else:
            cfg = conarycfg.ConaryConfiguration()
            cfg.read(self.conarycfgFile)
            cfg.root = cfg.dbPath = ":memory:"
            cfg.installLabelPath = [versions.Label(self.project.getLabel())]
            cclient = conaryclient.ConaryClient(cfg)

        self.writeConaryRc(tmpPath, cclient)

        # extract constants.py from the stage2.img template and override the BETANAG flag
        # this would be better if constants.py could load a secondary constants.py
        stage2Path = tempfile.mkdtemp()
        call('/sbin/fsck.cramfs', self.topdir + '/rPath/base/stage2.img', '-x', stage2Path)
        call('cp', stage2Path + '/usr/lib/anaconda/constants.py', tmpPath)
        betaNag = self.release.getDataValue('betaNag')
        call('sed', '-i', 's/BETANAG = 1/BETANAG = %d/' % int(betaNag), tmpPath + '/constants.py')
        util.rmtree(stage2Path)

        # create cramfs
        call('mkcramfs', tmpPath, productPath)

        # clean up
        util.rmtree(tmpPath)
        util.rmtree(tmpRoot)

        assertParentAlive()

    def write(self):
        isocfg = self.getConfig()
        self.isocfg = isocfg
        if isocfg.imagesPath != None:
            print >> sys.stderr, "WARNING: The imagesPath configuration entry has moved from installable_iso.conf to iso_gen.conf."
            sys.stderr.flush()

        troveName, versionStr, flavorStr = self.release.getTrove()
        version = versions.ThawVersion(versionStr)
        flavor = deps.deps.ThawDependencySet(flavorStr)
        self.version = version

        skipMediaCheck = self.release.getDataValue('skipMediaCheck')

        cfg = conarycfg.ConaryConfiguration()

        # add a repositoryMap and user entry to cfg
        projCfg = self.project.getConaryConfig(overrideSSL = not self.project.external, useSSL = self.cfg.SSL)
        cfg.installLabelPath = [versions.Label(self.project.getLabel())]
        cfg.repositoryMap.update(projCfg.repositoryMap)
        cfg.user = projCfg.user
        self.conarycfgFile = os.path.join(self.cfg.configPath, 'conaryrc')
        if os.path.exists(self.conarycfgFile):
            cfg.read(self.conarycfgFile)

        cfg.dbPath = ':memory:'
        cfg.root = ':memory:'
        cfg.initializeFlavors()
        cfg.pubRing = ['/dev/null']
        client = conaryclient.ConaryClient(cfg)
        
        revision = version.trailingRevision().asString()
        topdir = os.path.join(self.cfg.imagesPath, self.project.getHostname(),
            self.release.getArch(), str(self.release.getId()), "unified") 
        self.topdir = topdir
        util.mkdirChain(topdir)
        # subdir = string.capwords(self.project.getHostname())
        subdir = 'rPath'
        self.subdir = subdir
       
        # hardlink template files to topdir
        templateDir = os.path.join(isocfg.templatePath, self.release.getArch())
        if not os.path.exists(os.path.join(templateDir, 'PRODUCTNAME')):
            raise AnacondaTemplateMissing(self.release.getArch())

        self.status("Preparing ISO template")
        _linkRecurse(templateDir, topdir)
        productDir = os.path.join(topdir, subdir)
        if os.path.isdir(productDir):
            # reinit template if exists
            util.rmtree(productDir)
        os.rename(os.path.join(topdir, 'PRODUCTNAME'), productDir)
        # replace isolinux.bin with a real copy, since it's modified
        call('cp', '--remove-destination', '-a',
            templateDir + '/isolinux/isolinux.bin', topdir + '/isolinux/isolinux.bin')

        csdir = os.path.join(topdir, subdir, 'changesets')
        util.mkdirChain(csdir)
        assertParentAlive()

        # build a set of the things we already have extracted.
        self.status("Extracting changesets")
        existingChangesets = set()
        for path in (os.path.join(csdir, x) for x in os.listdir(csdir)):
            existingChangesets.add(path)

        trvList = client.repos.findTrove(cfg.installLabelPath[0],\
                                 (troveName, version.asString(), flavor),
                                 defaultFlavor = cfg.flavor)

        if not trvList:
            print >> sys.stderr, "no match for", groupName
            raise RuntimeException
        elif len(trvList) > 1:
            print >> sys.stderr, "multiple matches for", groupName
            raise RuntimeException

        # Abort if parent thread has died
        assertParentAlive()

        groupName, groupVer, groupFlavor = trvList[0]

        self.callback = Callback(self.status)
        rc = gencslist.extractChangeSets(client, cfg, csdir, groupName,
                                         groupVer, groupFlavor,
                                         oldFiles = existingChangesets,
                                         cacheDir = isocfg.cachePath,
                                         callback = self.callback)
        cslist, groupcs = rc

        # Abort if parent thread has died
        assertParentAlive()

        releaseVer = upstream(version)
        releasePhase = "ALPHA"
        arch = self.release.getArch()
        assert(arch in ('x86', 'x86_64'))
        if arch == 'x86':
            anacondaArch = 'i386'
        else:
            anacondaArch = arch

        # write the sqldb file
        baseDir = os.path.join(topdir, subdir, 'base')
        self.baseDir = baseDir
        sqldbPath = os.path.join(baseDir, 'sqldb')
        gencslist.writeSqldb(groupcs, sqldbPath, cfgFile = self.conarycfgFile)

        # write the cslist
        cslistPath = os.path.join(baseDir, 'cslist')
        cslistFile = file(cslistPath, "w")
        cslistFile.write("\n".join(cslist))
        cslistFile.close()

        infoMap = {
            "isodir":       os.path.normpath(os.path.join(self.cfg.finishedPath, self.project.getHostname(), str(self.release.getId()))),
            "topdir":       topdir,
            "subdir":       subdir,
            "name":         self.project.getName(),
            "safeName":     self.project.getHostname(),
            "version":      releaseVer,
            "arch":         anacondaArch,
            "scriptsdir":   isocfg.scriptPath,
        }
        util.mkdirChain(infoMap['isodir'])

        # Abort if parent thread has died
        assertParentAlive()

        # write .discinfo
        discInfoPath = os.path.join(topdir, ".discinfo")
        os.unlink(discInfoPath)
        discInfoFile = open(discInfoPath, "w")
        print >> discInfoFile, time.time()
        print >> discInfoFile, self.project.getName()
        print >> discInfoFile, anacondaArch
        print >> discInfoFile, "1"
        for x in ["base", "changesets", "pixmaps"]:
            print >> discInfoFile, "%s/%s" % (subdir, x)
        discInfoFile.close()

        self.writeProductImage('1#' + arch)

        call(isocfg.scriptPath + "/splitdistro", topdir)

        # Abort if parent thread has died
        assertParentAlive()

        isoList = []
        isoname = "%(safeName)s-%(version)s-%(arch)s-%%(disc)s.iso" % infoMap
        discdir = os.path.normpath(topdir + "/../")
        self.status("Building ISOs")

        for d in sorted(os.listdir(discdir)):
            if not d.startswith('disc'):
                continue
            
            discNum = d.split("disc")[-1]
            infoMap['disc'] = d
            discNumStr = "Disc %d" % int(discNum)
            truncatedName = infoMap['name'][:31-len(discNumStr)]
            infoMap['discname'] = "%s %s" % (truncatedName, discNumStr)
            infoMap['iso'] =  isoname % infoMap
            if os.access(os.path.join(discdir, d, "isolinux/isolinux.bin"), os.R_OK):
                os.chdir(os.path.join(discdir, d))
                call("mkisofs", "-o", "%(isodir)s/%(iso)s" % infoMap,
                                "-b", "isolinux/isolinux.bin",
                                "-c", "isolinux/boot.cat",
                                "-no-emul-boot",
                                "-boot-load-size", "4",
                                "-boot-info-table", "-R", "-J",
                                "-V",  "%(discname)s" % infoMap,
                                "-T", ".")
                # Abort if parent thread has died
                assertParentAlive()
            else:
                os.chdir(os.path.join(discdir, d))
                call("mkisofs", "-o", "%(isodir)s/%(iso)s" % infoMap,
                     "-R", "-J", "-V", "%(discname)s" % infoMap, "-T", ".")
                # Abort if parent thread has died
                assertParentAlive()

            isoList.append((infoMap['iso'], "%s Disc %s" % (infoMap['name'], discNum)))

        isoList = [ (os.path.join(infoMap['isodir'], iso[0]), iso[1]) for iso in isoList ]
        for iso, name in isoList:
            if not os.access(iso, os.R_OK):
                raise RuntimeError, "ISO generation failed"
            else:
                cmd = [isocfg.implantIsoMd5]
                if skipMediaCheck:
                    cmd.append('--supported-iso')
                cmd.append(iso)
                call(*cmd)

        # add the netboot images
        bootDest = os.path.join(infoMap['isodir'], 'boot.iso')
        diskbootDest = os.path.join(infoMap['isodir'], 'diskboot.img')
        gencslist._linkOrCopyFile(os.path.join(topdir, 'images', 'boot.iso'), bootDest)
        gencslist._linkOrCopyFile(os.path.join(topdir, 'images', 'diskboot.img'), diskbootDest)
        
        # clean up
        self.status("Cleaning up...")
        util.rmtree(os.path.normpath(os.path.join(topdir, "..")))
        isoList += ( (bootDest, "boot.iso"),
                     (diskbootDest, "diskboot.img"), )

        return isoList
