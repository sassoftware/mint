#
# Copyright (c) 2004-2005 Specifix, Inc.
#
# All Rights Reserved
#
from imagegen import ImageGenerator

class LiveIso(ImageGenerator):
    def write(self):
        tmpDir = tempfile.mkdtemp("", "imagetool", self.cfg.imagesPath)
        profileId = self.job.getProfileId()

        name, projectId = self.client.server.getProfile(profileId)
        trove, version, frozenFlavor = self.client.server.getTrove(profileId)
        flavor = deps.ThawDependencySet(frozenFlavor)

        project = self.client.getProject(projectId)
        cfg = project.getConaryConfig(self.cfg.imageLabel,
                                      self.cfg.imageRepo)
        cfg.setValue("root", tmpDir)
        client = conaryclient.ConaryClient(cfg)
        applyList = [(trove, version, flavor)]
        (cs, depFailures, suggMap, brokenByErase) = \
            client.updateChangeSet(applyList, recurse = False,
                                   resolveDeps = False)
        journal = Journal()
        client.applyUpdate(cs, journal=journal)

        fd, fn = tempfile.mkstemp('.iso', 'livecd',self.cfg.imagesPath)
        os.close(fd)

        subprocess.call((os.path.join(scriptPath, 'mklivecd'), tmpDir, fn))
        os.chmod(fn, 0644)

        return [fn]
