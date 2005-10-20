#
# Copyright (c) 2004-2005 rPath, Inc.
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

import callbacks
import conaryclient
import deps
import versions
from repository import repository
from build import use
from conarycfg import ConfigFile
from lib import util

import conarycfg
from mint.mint import upstream
from imagegen import ImageGenerator, assertParentAlive
import gencslist

class IsoConfig(ConfigFile):
    filename = 'installable_iso.conf'
    defaults = {
        'imagesPath':       None,
        'scriptPath':       '/srv/mint/code/scripts/',
        'cachePath':        '/srv/mint/changesets/',
        'templatePath':     '/srv/mint/templates/',
        'implantIsoMd5':    '/usr/lib/anaconda-runtime/implantisomd5'
    }

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


class InstallableIso(ImageGenerator):
    configObject = IsoConfig

    def writeProductImage(self):
        # write the product.img cramfs
        productPath = os.path.join(self.baseDir, "product.img")
        tmpPath = tempfile.mkdtemp()
        tmpRoot = tempfile.mkdtemp()

        # write .buildstamp
        bsFile = open(os.path.join(tmpPath, ".buildstamp"), "w")
        print >> bsFile, time.time()
        print >> bsFile, self.project.getName()
        print >> bsFile, upstream(self.release.getTroveVersion())
        print >> bsFile, self.subdir
        print >> bsFile, 'http://bugs.rpath.com/'
        print >> bsFile, "%s %s %s" % (self.release.getTroveName(),
                                       self.release.getTroveVersion().asString(),
                                       self.release.getTroveFlavor().freeze())
        bsFile.close()

        # extract anaconda-images from repository, if exists
        cfg = self.project.getConaryConfig(newUser='anonymous', newPass='anonymous', useSSL = False)
        cfg.root = tmpRoot
        cfg.installLabelPath = [self.version.branch().label()]
        cclient = conaryclient.ConaryClient(cfg)

        print >> sys.stderr, "extracting artwork from anaconda-images=%s" % cfg.installLabelPath[0].asString()
        try:
            self.callback.setChangeSet('anaconda-images')
            itemList = [('anaconda-images', (None, None), (None, None), True)]
            uJob, suggMap = cclient.updateChangeSet(itemList,
                resolveDeps = False,
                callback = self.callback)
        except repository.TroveNotFound:
            print >> sys.stderr, "anaconda-images not found on repository, skipping custom artwork"
        else:
            cclient.applyUpdate(uJob, callback = self.callback)
            print >> sys.stderr, "success."
            sys.stderr.flush()
        
            # copy pixmaps into cramfs root
            cmd = ['cp', '-av', tmpRoot + "/usr/share/anaconda/pixmaps/", tmpPath]
            print >> sys.stderr, " ".join(cmd)
            sys.stderr.flush()
            subprocess.call(cmd)
                
        # write the conaryrc file
        conaryrcFile = open(os.path.join(tmpPath, "conaryrc"), "w")
        print >> conaryrcFile, "installLabelPath " + self.release.getDataValue("installLabelPath")
        print >> conaryrcFile, "pinTroves kernel.*"
        conaryrcFile.close()
            
        # create cramfs
        cmd = ['mkcramfs', tmpPath, productPath]
        print >> sys.stderr, " ".join(cmd)
        sys.stderr.flush()
        subprocess.call(cmd)
        
        # clean up
        util.rmtree(tmpPath)
        util.rmtree(tmpRoot)
        
        assertParentAlive()

    def write(self):
        isocfg = self.getConfig()
        if isocfg.imagesPath != None:
            print >> sys.stderr, "WARNING: The imagesPath configuration entry has moved from installable_iso.conf to iso_gen.conf."
            sys.stderr.flush()
        
        releaseId = self.job.getReleaseId()

        release = self.client.getRelease(releaseId)
        self.release = release
        troveName, versionStr, flavorStr = release.getTrove()
        version = versions.ThawVersion(versionStr)
        flavor = deps.deps.ThawDependencySet(flavorStr)
        project = self.client.getProject(release.getProjectId())
        self.project = project
        self.version = version

        skipMediaCheck = release.getDataValue('skipMediaCheck')
        betaNag = release.getDataValue('betaNag')

        cfg = conarycfg.ConaryConfiguration()
        conarycfgFile = os.path.join(self.cfg.configPath, 'conaryrc')
        if os.path.exists(conarycfgFile):
            cfg.read(conarycfgFile)

        cfg.dbPath = ':memory:'
        cfg.root = ':memory:'
        cfg.initializeFlavors()
        client = conaryclient.ConaryClient(cfg)
        
        revision = version.trailingRevision().asString()
        topdir = os.path.join(self.cfg.imagesPath, project.getHostname(), release.getArch(), revision, "unified") 
        util.mkdirChain(topdir)
        # subdir = string.capwords(project.getHostname())
        subdir = 'rPath'
        self.subdir = subdir
       
        # hardlink template files to topdir
        templateDir = os.path.join(isocfg.templatePath, release.getArch())
        if not os.path.exists(os.path.join(templateDir, 'PRODUCTNAME')):
            raise AnacondaTemplateMissing(release.getArch())

        self.status("Preparing ISO template")
        _linkRecurse(templateDir, topdir)
        productDir = os.path.join(topdir, subdir)
        if os.path.isdir(productDir):
            # reinit template if we're working with an existing image
            util.rmtree(os.path.join(topdir, 'PRODUCTNAME'))
            os.rename(productDir, os.path.join(topdir, 'PRODUCTNAME'))
        os.rename(os.path.join(topdir, 'PRODUCTNAME'), os.path.join(topdir, subdir))
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
        arch = release.getArch()
        assert(arch in ('x86', 'x86_64'))
        if arch == 'x86':
            anacondaArch = 'i386'
        else:
            anacondaArch = arch

        # write the sqldb file
        baseDir = os.path.join(topdir, subdir, 'base')
        self.baseDir = baseDir
        sqldbPath = os.path.join(baseDir, 'sqldb')
        gencslist.writeSqldb(groupcs, sqldbPath)

        # write the cslist
        cslistPath = os.path.join(baseDir, 'cslist')
        cslistFile = file(cslistPath, "w")
        cslistFile.write("\n".join(cslist))
        cslistFile.close()

        infoMap = {
            "isodir":       os.path.normpath(os.path.join(topdir, "..", "iso")),
            "topdir":       topdir,
            "subdir":       subdir,
            "name":         project.getName(),
            "safeName":     project.getHostname(),
            "version":      releaseVer,
            "arch":         anacondaArch,
            "scriptsdir":   isocfg.scriptPath,
        }
        util.mkdirChain(infoMap['isodir'])

        # Abort if parent thread has died
        assertParentAlive()

        # write .discinfo
        discInfoPath = os.path.join(topdir, ".discinfo")
        discInfoFile = open(discInfoPath, "w")
        print >> discInfoFile, time.time()
        print >> discInfoFile, project.getName()
        print >> discInfoFile, anacondaArch
        print >> discInfoFile, "1"
        for x in ["base", "changesets", "pixmaps"]:
            print >> discInfoFile, "%s/%s" % (subdir, x)
        discInfoFile.close()

        self.writeProductImage()

        cmd = [isocfg.scriptPath + "/splitdistro", topdir]
        print >> sys.stderr, " ".join(cmd)
        sys.stderr.flush()
        subprocess.call(cmd)

        # Abort if parent thread has died
        assertParentAlive()

        isoList = []
        isoname = "%(safeName)s-%(version)s-%(arch)s-%%(disc)s.iso" % infoMap
        discdir = os.path.normpath(topdir + "/../")
        self.status("Building ISOs")

        for d in os.listdir(discdir):
            if not d.startswith('disc'):
                continue
            
            discNum = d.split("disc")[-1]
            infoMap['disc'] = d
            discNumStr = "Disk %d" % int(discNum)
            truncatedName = infoMap['name'][:31-len(discNumStr)]
            infoMap['discname'] = "%s %s" % (truncatedName, discNumStr)
            infoMap['iso'] =  isoname % infoMap
            if os.access(os.path.join(discdir, d, "isolinux/isolinux.bin"), os.R_OK):
                os.chdir(os.path.join(discdir, d))
                cmd = ["mkisofs", "-o", "%(isodir)s/%(iso)s" % infoMap,
                                  "-b", "isolinux/isolinux.bin",
                                  "-c", "isolinux/boot.cat",
                                  "-no-emul-boot",
                                  "-boot-load-size", "4",
                                  "-boot-info-table", "-R", "-J",
                                  "-V",  "%(discname)s" % infoMap, "-T", "."]
                print >> sys.stderr, cmd
                sys.stderr.flush()
                subprocess.call(cmd)
                # Abort if parent thread has died
                assertParentAlive()
            else:
                os.chdir(os.path.join(discdir, d))
                cmd = ["mkisofs", "-o", "%(isodir)s/%(iso)s" % infoMap,
                       "-R", "-J", "-V", "\"%(discname)s\"" % infoMap, "-T", "."]
                print >> sys.stderr, cmd
                sys.stderr.flush()
                subprocess.call(cmd)
                # Abort if parent thread has died
                assertParentAlive()

            isoList.append((infoMap['iso'], "%s Disk %s" % (infoMap['name'], discNum)))

        isoList = [ (os.path.join(infoMap['isodir'], iso[0]), iso[1]) for iso in isoList ]
        for iso, name in isoList:
            if not os.access(iso, os.R_OK):
                raise RuntimeError, "ISO generation failed"
            else:
                cmd = [isocfg.implantIsoMd5]
                if skipMediaCheck:
                    cmd.append('--supported-iso')
                cmd.append(iso)
                print >> sys.stderr, cmd
                sys.stderr.flush()
                subprocess.call(cmd)

        # add the netboot images
        isoList += ( (os.path.join(topdir, 'images/boot.iso'), "boot.iso"),
                     (os.path.join(topdir, 'images/diskboot.img'), "diskboot.img"), )

        return isoList
