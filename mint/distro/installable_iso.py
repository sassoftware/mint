#
# Copyright (c) 2004-2005 Specifix, Inc.
#
# All Rights Reserved
#
import errno
import os
import sys
import tempfile
import deps
import flavorcfg
import repository
import versions
from build import use

import distribution 

import conarycfg
from conarycfg import ConfigFile

from imagegen import ImageGenerator

class IsoConfig(ConfigFile):
    defaults = {
        'productPath':       'Specifix',
        'productName':       'Specifix Linux',
        'productPrefix':     'spx',
        'templatePath':      None,
        'nfsPath':           None,
        'tftpbootPath':      None,
        'changesetCache':    None,
    }

class InstallableIso(ImageGenerator):
    def getIsoConfig(self):
        isocfg = IsoConfig()
        isocfg.read("installable_iso.conf")
        return isocfg

    def write(self):
        isocfg = self.getIsoConfig()
    
        profileId = self.job.getProfileId()

        profile = self.client.getProfile(profileId)
        trove, versionStr, frozenFlavor = profile.getTrove()
        flavor = deps.deps.ThawDependencySet(frozenFlavor)

        project = self.client.getProject(profile.getProjectId())

        ccfg = project.getConaryConfig()

        flavorConfig = flavorcfg.FlavorConfig(ccfg.useDirs, ccfg.archDirs)
        ccfg.flavor = flavorConfig.toDependency(override=ccfg.flavor)
        insSet = deps.deps.DependencySet()
        for dep in deps.arch.currentArch:
            insSet.addDep(deps.deps.InstructionSetDependency, dep)
        ccfg.flavor.union(insSet)
        ccfg.buildFlavor = ccfg.flavor.copy()
        flavorConfig.populateBuildFlags()
        use.setBuildFlagsFromFlavor(None, ccfg.buildFlavor, error=None)
       
        repos = repository.netclient.NetworkRepositoryClient(ccfg.repositoryMap)

        jobId = self.job.getId()
        releaseVer = self.job.getData("releaseVer")
        releasePhase = self.job.getData("releasePhase")
        isoSize = self.job.getData("isoSize")

        arch = self.job.getArch()
        assert(arch in ('x86', 'x86_64'))
 
        distroInfo = distribution.DistroInfo(isocfg.productPrefix,
                                       isocfg.productPath,
                                       isocfg.productName,
                                       releaseVer, releasePhase,
                                       arch = arch,
                                       isoSize = isoSize)
        version = versions.VersionFromString(versionStr)
       
        tmpDir = self.cfg.imagesPath + os.path.join(arch, releasePhase)
        dist = distribution.Distribution(arch, repos, ccfg,
                                   distroInfo, (trove, version.asString(), flavor),
                                   buildpath = tmpDir, isopath = tmpDir+"/isos/",
                                   isoTemplatePath = isocfg.templatePath,
                                   nfspath = isocfg.nfsPath,
                                   tftpbootpath = isocfg.tftpbootPath,
                                   fromcspath = isocfg.changesetCache,
                                   statusCb = self.status)
                                   
        logfile = os.path.join(self.cfg.logPath, "instiso-%d.log" % jobId)
        self.grabOutput(logfile)
        try:
            dist.prep()
            filenames = dist.create()
        except:
            self.releaseOutput()
            raise
        self.releaseOutput()
         
        return filenames
