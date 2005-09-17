#
# Copyright (c) 2004-2005 rPath, Inc.
#
# All Rights Reserved
#
import os
import re
import subprocess
import sys

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
        'imagesPath':   '/srv/mint/images/',
        'scriptPath':   '/srv/mint/code/scripts/',
        'cacheDir':     '/srv/mint/changesets/',
    }

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

        cfg = conarycfg.ConaryConfiguration()
        cfg.dbPath = ':memory:'
        cfg.root = ':memory:'
        cfg.initializeFlavors()
        client = conaryclient.ConaryClient(cfg)
        
        revision = version.trailingRevision().asString()
        topdir = os.path.join(isocfg.imagesPath, project.getHostname(), revision, "unified") 
        subdir = 'rPath'
        
        csdir = os.path.join(topdir, subdir, 'changesets')

        util.mkdirChain(csdir)
        self.status("Extracting changesets")
        existingChangesets = {}
        for path in [ "%s/%s" % (csdir, x) for x in os.listdir(csdir) ]:
            existingChangesets[path] = 1

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
        cslist = gencslist.extractChangesets(client, cfg, csdir, groupName,
                                             groupVer, groupFlavor,
                                             oldFiles = existingChangesets,
                                             cacheDir = isocfg.cacheDir)
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

        self.status("Building Anaconda installation")
        cmd = [isocfg.scriptPath + '/buildinstall', '--topdir', topdir,
               '--subdir', subdir, '--name', '%s' % project.getName(),
               '--version', releaseVer, '--arch', anacondaArch]
        print >> sys.stderr, " ".join(cmd)
        sys.stderr.flush()

        subprocess.call(['setarch', anacondaArch] + cmd)

        # Abort if parent thread has died
        assertParentAlive()

        cmd = [isocfg.scriptPath + "/splitdistro", topdir]
        print >> sys.stderr, " ".join(cmd)
        sys.stderr.flush()
        subprocess.call(cmd)

        # Abort if parent thread has died
        assertParentAlive()

        isoList = []
        isoname = "%(safeName)s-%(version)s-%%(disc)s.iso" % infoMap
        discdir = os.path.normpath(topdir + "/../")
        self.status("Building ISOs")

        for d in os.listdir(discdir):
            if not d.startswith('disc'):
                continue
            
            infoMap['disc'] = d
            infoMap['discname'] = ("%(name)s %(disc)s" % infoMap)[32:]
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
            isoList.append(infoMap['iso'])
        
        isoList = [os.path.join(infoMap['isodir'], iso) for iso in isoList]
        for iso in isoList:
            if not os.access(iso, os.R_OK):
                raise RuntimeError, "ISO generation failed"
        return isoList
