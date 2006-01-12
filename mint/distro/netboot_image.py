#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

# python standard library imports
import glob
import os
import tempfile
import subprocess

# mint imports
from imagegen import ImageGenerator

# conary imports
from conary import conaryclient
from conary import deps
from conary import flavorcfg
from conary import versions
from conary.callbacks import UpdateCallback, ChangesetCallback
from conary.conarycfg import ConfigFile
from conary.lib import log, util

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

class NetbootImage(ImageGenerator):
    def write(self):
        rootDir = tempfile.mkdtemp('', 'netboot-root-', self.cfg.imagesPath)
        log.info('generating netboot images, root=%s', rootDir)

        release = self.client.getRelease(self.job.getReleaseId())
        trove, versionStr, flavorStr = release.getTrove()
        flavor = deps.deps.ThawDependencySet(flavorStr)
        version = versions.ThawVersion(versionStr)

        project = self.client.getProject(release.getProjectId())

        # set up configuration
        cfg = project.getConaryConfig()
        # turn off threading
        cfg.threadded = False
        # configure flavor
        flavorConfig = flavorcfg.FlavorConfig(cfg.useDirs, cfg.archDirs)
        cfg.flavor = flavorConfig.toDependency(override=cfg.flavor[0])
        insSet = deps.deps.DependencySet()
        for dep in deps.arch.currentArch:
            insSet.addDep(deps.deps.InstructionSetDependency, dep[0])
        cfg.flavor.union(insSet)
        cfg.buildFlavor = cfg.flavor.copy()
        flavorConfig.populateBuildFlags()
        cfg.setValue('root', rootDir)

        # FIXME: this is a workaround until users/groups work properly
        os.mkdir(rootDir + '/etc')
        f = open(rootDir + '/etc/passwd', 'w')
        f.write("""mail:x:8:12:mail:/var/spool/mail:/sbin/nologin
apache:x:48:48:Apache:/var/www:/sbin/nologin
""")
        f.close()
        f = open(rootDir + '/etc/group', 'w')
        f.write("""tty:x:5:
utmp:x:22:
mail:x:12:mail
apache:x:48:
smmsp:x:51:
""")
        f.close()

        client = conaryclient.ConaryClient(cfg)
        applyList = [(trove, version, flavor)]
        self.status('installing software')
        callback = InstallCallback(self.status)
        (updJob, suggMap) = client.updateChangeSet(applyList, recurse = True,
                                                   resolveDeps = False,
                                                   callback = callback)
        client.applyUpdate(updJob, callback = callback, replaceFiles = True)

        self.status('generating images')
        imgDir = tempfile.mkdtemp('', 'netboot-', self.cfg.imagesPath)

        # figure out the kernel version
        kernelPath = glob.glob(rootDir + '/lib/modules/*')[0]
        kernelVer = kernelPath.split('/')[-1]

        # FIXME - this trusts the script that came from the group
        script = os.path.join(rootDir, 'usr/sbin/diskless-mkinitrd')
        if not os.access(script, os.X_OK):
            raise RuntimeError, 'image missing /usr/sbin/diskless-mkinitrd'

        subprocess.call((script, rootDir, kernelVer, imgDir))
        # make sure everyone can read the images
        os.chmod(imgDir, 0755)

        # get rid of our old root directory
        self.status('cleaning up')
        util.rmtree(rootDir)

        images = [ (os.path.join(imgDir, x), x) for x in
                   ('vmlinuz', 'initrd.img', 'rootfs.tgz') ]
        log.info('images %s', images)
        for image, descr in images:
            log.info('check %s', image)
            if not os.access(image, os.R_OK):
                raise RuntimeError, 'image creations script did not create images properly'

        return images
