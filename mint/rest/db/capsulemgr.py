#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from conary.lib import util
from mint.rest.db import manager

import rpath_capsule_indexer

class CapsuleManager(manager.Manager):
    def getIndexerConfig(self):
        capsuleDataDir = util.joinPaths(self.cfg.dataPath, 'capsules')
        cfg = rpath_capsule_indexer.IndexerConfig()
        cfg.configLine("store sqlite:///%s/database.sqlite" %
            capsuleDataDir)
        cfg.configLine("indexDir %s/packages" % capsuleDataDir)
        cfg.configLine("systemsPath %s/systems" % capsuleDataDir)
        dataSources = self.db.platformMgr.listPlatformSources().platformSource
        # XXX we only deal with RHN for now
        if dataSources:
            cfg.configLine("user RHN %s %s" % (dataSources[0].username,
                dataSources[0].password))
        # XXX channels are hardcoded for now
        cfg.configLine("channels rhel-i386-as-4")
        cfg.configLine("channels rhel-x86_64-as-4")
        cfg.configLine("channels rhel-i386-server-5")
        cfg.configLine("channels rhel-x86_64-server-5")

        util.mkdirChain(capsuleDataDir)
        return cfg

    def getIndexer(self):
        cfg = self.getIndexerConfig()
        return rpath_capsule_indexer.Indexer(cfg)
