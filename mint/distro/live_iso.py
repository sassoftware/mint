#
# Copyright (c) 2004-2005 Specifix, Inc.
#
# All Rights Reserved
#
import os
from imagegen import ImageGenerator

class Journal:
    def lchown(self, root, target, user, group):
        # get rid of the root
        target = target[len(root):]
        dirname = os.path.dirname(target)
        filename = os.path.basename(target)
        f = open(os.sep.join((root, dirname, '.UIDGID')), 'a')
        # XXX e2fsimage does not handle group lookups yet
        f.write('%s %s\n' %(filename, user))
        f.close()

    def mknod(self, root, target, devtype, major, minor, mode,
              uid, gid):
        # get rid of the root
        target = target[len(root):]
        dirname = os.path.dirname(target)
        filename = os.path.basename(target)
        f = open(os.sep.join((root, dirname, '.DEVICES')), 'a')
        # XXX e2fsimage does not handle symbolic users/groups for .DEVICES
        f.write('%s %s %d %d 0%o\n' %(filename, devtype, major, minor, mode))
        f.close()

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
