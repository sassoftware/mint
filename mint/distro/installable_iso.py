#
# Copyright (c) 2004-2005 rPath, Inc.
#
# All Rights Reserved
#
import os
import re
import subprocess
import sys

import callbacks
import conaryclient
import deps
import versions
from build import use
from conarycfg import ConfigFile
from lib import util

import conarycfg
from mint.mint import upstream
from imagegen import ImageGenerator, assertParentAlive
import gencslist

class IsoConfig(ConfigFile):
    defaults = {
        'imagesPath':       '/srv/mint/images/',
        'scriptPath':       '/srv/mint/code/scripts/',
        'cachePath':        '/srv/mint/changesets/',
        'templatePath':     '/srv/mint/templates/',
        'implantIsoMd5':    '/usr/lib/anaconda-runtime/implantisomd5'
    }

class AnacondaTemplateMissing(Exception):
    def __init__(arch = "arch"):
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
    def getIsoConfig(self):
        isocfg = IsoConfig()
        isocfg.read("installable_iso.conf")
        return isocfg

    def write(self):
        isocfg = self.getIsoConfig()
    
        releaseId = self.job.getReleaseId()

        release = self.client.getRelease(releaseId)
        troveName, versionStr, flavorStr = release.getTrove()
        version = versions.ThawVersion(versionStr)
        flavor = deps.deps.ThawDependencySet(flavorStr)
        project = self.client.getProject(release.getProjectId())

        skipMediaCheck = release.getDataValue('skipMediaCheck')
        betaNag = release.getDataValue('betaNag')

        cfg = conarycfg.ConaryConfiguration()
        cfg.dbPath = ':memory:'
        cfg.root = ':memory:'
        cfg.initializeFlavors()
        client = conaryclient.ConaryClient(cfg)
        
        revision = version.trailingRevision().asString()
        topdir = os.path.join(isocfg.imagesPath, project.getHostname(), release.getArch(), revision, "unified") 
        subdir = 'rPath' # XXX parameterize
        csdir = os.path.join(topdir, subdir, 'changesets')
        util.mkdirChain(csdir)
        
        # hardlink template files to topdir
        templateDir = os.path.join(isocfg.templatePath, release.getArch())
        if not os.path.exists(templateDir):
            raise AnacondaTemplateMissing(release.getArch())

        self.status("Preparing ISO template")
        _linkRecurse(templateDir, topdir)
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

        callback = Callback(self.status)
        rc = gencslist.extractChangeSets(client, cfg, csdir, groupName,
                                         groupVer, groupFlavor,
                                         oldFiles = existingChangesets,
                                         cacheDir = isocfg.cachePath,
                                         callback = callback)
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
        sqldbPath = os.path.join(topdir, subdir, 'sqldb')
        gencslist.writeSqldb(groupcs, sqldbPath)

        # write the cslist
        cslistPath = os.path.join(topdir, subdir, 'base')
        util.mkdirChain(cslistPath)
        cslistFile = file(cslistPath + '/cslist', "w")
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
            
            infoMap['disc'] = d
            infoMap['discname'] = ("%(name)s %(disc)s" % infoMap)[:32]
            infoMap['iso'] =  isoname % infoMap
            if os.access(os.path.join(discdir, d, "isolinux/isolinux.bin"), os.R_OK):
                os.chdir(os.path.join(discdir, d))
                cmd = ["mkisofs", "-o", "%(isodir)s/%(iso)s" % infoMap,
                                  "-b", "isolinux/isolinux.bin",
                                  "-c", "isolinux/boot.cat",
                                  "-no-emul-boot",
                                  "-boot-load-size", "4",
                                  "-boot-info-table", "-R", "-J",
                                  "-V",  "\"%(discname)s\"" % infoMap, "-T", "."]
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

            discNum = infoMap['discname'].split("disc")[-1]
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
        isoList += [ (os.path.join(topdir, 'images/boot.iso'), "boot.iso"),
                     (os.path.join(topdir, 'images/diskboot.img'), "diskboot.img"),
                   ]

        return isoList
