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
from conarycfg import ConfigFile, BOOLEAN

import distribution 
import conarycfg
from mint.mint import upstream
from imagegen import ImageGenerator

class IsoConfig(ConfigFile):
    defaults = {
        'productPath':       'rpath',
        'productName':       'rpath Linux',
        'productPrefix':     'rpl',
        'templatePath':      None,
        'nfsPath':           None,
        'tftpbootPath':      None,
        'changesetCache':    None,
        'instRootCache':     None,
        'cachedAnaconda':    [ BOOLEAN, False ],
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

        ccfg = project.getConaryConfig()

        flavorConfig = flavorcfg.FlavorConfig(ccfg.useDirs, ccfg.archDirs)
        ccfg.flavor = flavorConfig.toDependency(override=ccfg.flavor[0])
        insSet = deps.deps.DependencySet()
        for dep in deps.arch.currentArch:
            insSet.addDep(deps.deps.InstructionSetDependency, dep[0])
        ccfg.flavor.union(insSet)
        ccfg.buildFlavor = ccfg.flavor.copy()
        flavorConfig.populateBuildFlags()
       
        repos = repository.netclient.NetworkRepositoryClient(ccfg.repositoryMap)

        jobId = self.job.getId()
        releaseVer = upstream(version)
        releasePhase = "ALPHA"

        arch = release.getArch()
        assert(arch in ('x86', 'x86_64'))
 
        distroInfo = distribution.DistroInfo(isocfg.productPrefix, isocfg.productPath, release.getName(),
                                             releaseVer, releasePhase,
                                             arch = arch,
                                             isoSize = isoSize)
       
        tmpDir = self.cfg.imagesPath + os.path.join(arch, releasePhase)
        dist = distribution.Distribution(arch, repos, ccfg,
                                   distroInfo, (troveName, version.asString(), flavor),
                                   buildpath = tmpDir, isopath = tmpDir+"/isos/",
                                   isoTemplatePath = isocfg.templatePath,
                                   nfspath = isocfg.nfsPath,
                                   tftpbootpath = isocfg.tftpbootPath,
                                   cachepath = isocfg.changesetCache,
                                   instCachePath = isocfg.instRootCache,
                                   cachedAnaconda = isocfg.cachedAnaconda,
                                   statusCb = self.status,
                                   clean = True)
                                   
        dist.prep()
        filenames = dist.create()
        
        return filenames
