#
# Copyright (c) 2004-2005 rpath, Inc.
#
# All Rights Reserved
#

# python standard library imports
import os
import tempfile
import subprocess

# mint imports
from imagegen import ImageGenerator

# conary imports
import conary
import conaryclient
import deps
import flavorcfg
import versions
from callbacks import UpdateCallback, ChangesetCallback
from conarycfg import ConfigFile
from lib import log

class LiveIsoConfig(ConfigFile):
    defaults = {
        'scriptPath':        None,
    }

class InstallCallback(UpdateCallback, ChangesetCallback):
    def restoreFiles(self, size, totalSize):
        if totalSize != 0:
            self.restored += size
            self.update('writing files (%d%% of %dK)'
                        %((self.restored * 100) / totalSize, totalSize / 1024))

    def requestingChangeSet(self):
        self.update('requesting changeset')

    def setUpdateHunk(self, num, total):
        self.restored = 0

    def downloadingChangeSet(self, got, need):
        if need != 0:
            self.update('downloading from repository (%d%% of %dk)' %
                        ((got * 100) / need, need / 1024))

    def update(self, msg):
        # only push an update into the database if it differs from the
        # current message
        if self.msg != msg:
            self.msg = msg
            self.status(msg)

    def __init__(self, status):
        self.status = status
        self.restored = 0
        self.msg = ''

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
    def getConfig(self):
        cfg = LiveIsoConfig()
        cfg.read("live_iso.conf")
        return cfg

    def write(self):
        imgcfg = self.getConfig()
        if not imgcfg.scriptPath:
            raise RuntimeError, 'scriptPath must be set in configuration file'

        tmpDir = tempfile.mkdtemp("", "imagetool", self.cfg.imagesPath)
        log.info('generating live iso with tmpdir %s', tmpDir)
        release = self.client.getRelease(self.job.getReleaseId())
        trove, version, flavorStr = release.getTrove()

        project = self.client.getProject(release.getProjectId())

        trove, versionStr, flavorStr = release.getTrove()
        flavor = deps.deps.ThawDependencySet(flavorStr)
        version = versions.ThawVersion(versionStr)

        project = self.client.getProject(release.getProjectId())

        # set up configuration
        cfg = project.getConaryConfig()
        # turn off threading
        cfg.threadded = False
        flavorConfig = flavorcfg.FlavorConfig(cfg.useDirs, cfg.archDirs)
        cfg.flavor = flavorConfig.toDependency(override=cfg.flavor[0])
        insSet = deps.deps.DependencySet()
        for dep in deps.arch.currentArch:
            insSet.addDep(deps.deps.InstructionSetDependency, dep[0])
        cfg.flavor.union(insSet)
        cfg.buildFlavor = cfg.flavor.copy()
        flavorConfig.populateBuildFlags()
        cfg.setValue('root', tmpDir)

        client = conaryclient.ConaryClient(cfg)
        applyList = [(trove, version, flavor)]
        self.status('installing software')
        callback = InstallCallback(self.status)
        (updJob, suggMap) = client.updateChangeSet(applyList, recurse = True,
                                                   resolveDeps = False,
                                                   callback = callback)
        journal = Journal()
        client.applyUpdate(updJob, journal=journal, callback = callback)

        self.status('generating images')
        fd, fn = tempfile.mkstemp('.iso', 'livecd', self.cfg.imagesPath)
        os.close(fd)

        subprocess.call((os.path.join(imgcfg.scriptPath, 'mklivecd'), tmpDir,
                         fn))
        os.chmod(fn, 0644)

        return [fn]
