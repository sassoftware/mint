#
# Copyright (c) 2004-2005 Specifix, Inc.
#
# All Rights Reserved
#
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

        conaryCfg.set('buildFlavor', flavor)

        releaseVer = self.client.getProfileData(self.job.getProfileId(), "releaseVer")
        releasePhase = self.client.getProfileDat(self.job.getProfileId(), "releasePhase")

        distroInfo = distro.DistroInfo(self.cfg.instIsoPrefix,
                                       self.cfg.instIsoProductPath,
                                       self.cfg.instIsoProductName,
                                       releaseVer, releasePhase)

        dist = distro.Distribution(repos, cfg, distroInfo, trove, tmpDir, self.cfg.instIsoTemplate, "/", "/", "/", None, False)
        dist.prep()
        dist.create()
        return ['']
