#
# Copyright (C) 2006, rPath, Inc.
# All rights reserved.
#

from raa.modules.raasrvplugin import rAASrvPlugin
from mint import loadmirror, config

import os
import statvfs

class Callback(loadmirror.Callback):
    def __init__(self, serverName, totalFiles, statusFile = None, logger = None):
        loadmirror.Callback.__init__(self, serverName, totalFiles)
        self.logger = logger

    def _write(self, msg):
        self.logger.info(msg)


class LoadMirror(rAASrvPlugin):
    def doTask(self, schedId, execId):
        cmd, _ = self.server.getCommand(schedId)

        error = ''
        if cmd == "mount":
            try:
                loadmirror.mountMirrorLoadDrive()
            except loadmirror.NoMirrorLoadDiskFound, e:
                error = str(e)
            srv = os.statvfs('/srv')
            disk = os.statvfs(loadmirror.target)
            available = srv[statvfs.F_BSIZE] * srv[statvfs.F_BAVAIL]
            repoSize = int(disk[statvfs.F_BSIZE] * (disk[statvfs.F_BLOCKS] - disk[statvfs.F_BFREE]) * 1.1)
            if available < repoSize:
                error = '%s MB of disk space needed to preload mirror but only %s MB available' % (repoSize / 0x100000, available / 0x100000)
                log = loadmirror.logger
                log.error(error)
        elif cmd == "preload":
            self._startPreload()

        loadmirror.logger.flush()
        self.server.setError(schedId, cmd, True, error)
        return True

    def _startPreload(self):
        cfg = config.MintConfig()
        cfg.read(config.RBUILDER_CONFIG)

        log = loadmirror.logger
        loader = loadmirror.LoadMirror(loadmirror.target,
            'http://%s:%s@localhost/xmlrpc-private/' % (cfg.authUser, cfg.authPass))
        loadmirror.mountMirrorLoadDrive()

        mirrored = 0
        for serverName in os.listdir(loadmirror.target):
            if not os.path.exists(os.path.join(loadmirror.target, serverName, "MIRROR-INFO")):
                continue
            log.info("Processing %s", serverName)

            numFiles = loader.parseMirrorInfo(serverName)
            cb = Callback(serverName, numFiles, logger = log)

            if os.getuid() == 0:
                import pwd
                apacheUser = pwd.getpwnam('apache')[2:4]
            else:
                apacheUser = None

            try:
                project = loader.findTargetProject(serverName)
                log.info("Found project eligible to load: %s", serverName)
                loader.copyFiles(serverName, project, targetOwner = apacheUser, callback = cb.callback)
                mirrored += 1
            except RuntimeError, e:
                log.warning(e)
            except Exception, e:
                log.error(e)
                raise
        log.info("DONE. Pre-loaded %d repositories." % mirrored)
