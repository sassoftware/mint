#
# Copyright (c) 2004-2005 Specifix, Inc.
#
# All Rights Reserved
#
import sys
import tempfile
from deps import deps
import repository

sys.path.insert(0, "/home/tgerla/cvs/darby/client/")
from buildsystem import distro

from imagegen import ImageGenerator

class InstallableIso(ImageGenerator):
    def write(self):
        tmpDir = tempfile.mkdtemp("", "imagetool", self.cfg.imagesPath)
        profileId = self.job.getProfileId()

        name, projectId = self.client.server.getProfile(profileId)
        trove, version, frozenFlavor = self.client.server.getTrove(profileId)
        flavor = deps.ThawDependencySet(frozenFlavor)

        project = self.client.getProject(projectId)

        conaryCfg = project.getConaryConfig(self.cfg.imageLabel,
                                            self.cfg.imageRepo)

        conaryCfg.setValue('buildFlavor', flavor.freeze())
        repos = repository.netclient.NetworkRepositoryClient(conaryCfg.repositoryMap)

        jobId = self.job.getId()
        releaseVer = self.client.getJobData(jobId, "releaseVer")
        releasePhase = self.client.getJobData(jobId, "releasePhase")

        distroInfo = distro.DistroInfo(self.cfg.instIsoPrefix,
                                       self.cfg.instIsoProductPath,
                                       self.cfg.instIsoProductName,
                                       releaseVer, releasePhase)

        dist = distro.Distribution(repos, conaryCfg,
                                   distroInfo,
                                   trove, tmpDir, self.cfg.instIsoTemplatePath, "/", "/", "/", None, False)
        dist.prep()
        dist.create()
        return ['']
