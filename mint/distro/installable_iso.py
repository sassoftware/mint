#
# Copyright (c) 2004-2005 Specifix, Inc.
#
# All Rights Reserved
#
import os
import sys
import tempfile
import deps
import flavorcfg
import repository
import versions
from build import use

sys.path.insert(0, "/home/tgerla/cvs/darby/client/")
from buildsystem import distro

from imagegen import ImageGenerator

class InstallableIso(ImageGenerator):
    def write(self):
        profileId = self.job.getProfileId()

        name, projectId = self.client.server.getProfile(profileId)
        trove, versionStr, frozenFlavor = self.client.server.getTrove(profileId)
        flavor = deps.deps.ThawDependencySet(frozenFlavor)

        project = self.client.getProject(projectId)

        ccfg = project.getConaryConfig()

        flavorConfig = flavorcfg.FlavorConfig(ccfg.useDir, ccfg.archDir)
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
        releaseVer = self.client.getJobData(jobId, "releaseVer")
        releasePhase = self.client.getJobData(jobId, "releasePhase")

        distroInfo = distro.DistroInfo(self.cfg.instIsoPrefix,
                                       self.cfg.instIsoProductPath,
                                       self.cfg.instIsoProductName,
                                       releaseVer, releasePhase)
        version = versions.VersionFromString(versionStr)
       
        # XXX remove this and pass version as soon as darby can handle a full ver
        label = version.branch().label()
        
        # XXX this may be a hack--not sure
        arch = flavor.members[deps.deps.DEP_CLASS_IS].members.keys()[0]
        assert(arch in ('x86', 'x86_64'))
       
        tmpDir = self.cfg.imagesPath + os.path.join(arch, releasePhase)
        dist = distro.Distribution(arch, repos, ccfg,
                                   distroInfo, (trove, label, flavor),
                                   tmpDir, tmpDir+"/isos/", self.cfg.instIsoTemplatePath,
                                   self.cfg.nfsPath, self.cfg.tftpbootPath, None,
                                   "/data/imagetool/data/logs/", False)
                                   
        dist.prep()
        filenames = dist.create()
        return filenames
