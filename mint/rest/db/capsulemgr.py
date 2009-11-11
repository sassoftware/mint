#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from conary.lib import util
from mint.rest.db import manager
from mint.rest.api import models

import rpath_capsule_indexer

class CapsuleManager(manager.Manager):
    def getIndexerConfig(self):
        capsuleDataDir = util.joinPaths(self.cfg.dataPath, 'capsules')
        cfg = rpath_capsule_indexer.IndexerConfig()
        dbDriver = self.db.db.driver
        # pgpool is the same as postgres
        dbConnectString = self.db.db.db.database
        if dbDriver == 'pgpool':
            dbDriver = "postgres"
            # XXX this is temporary
            dbConnectString = 'postgres@localhost:5439/mint'
        elif dbDriver == "sqlite":
            # sqlalchemy requires four slashes for a sqlite backend,
            # because it treats the filename as the database. See comments in
            # sqlalchemy/databases/sqlite.py
            dbConnectString = "/" + dbConnectString
        cfg.configLine("store %s://%s" % (dbDriver, dbConnectString))
        cfg.configLine("indexDir %s/packages" % capsuleDataDir)
        cfg.configLine("systemsPath %s/systems" % capsuleDataDir)
        dataSources = self.db.platformMgr.getSources().instance
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

    def getIndexerErrors(self, platformId = None):
        indexer = self.getIndexer()

        errors = indexer.model.getPackageDownloadFailures()
        ret = models.ResourceErrors()
        for err in errors:
            # For now we only have DownloadError as code
            e = models.ResourceError(id = err.package_failed_id,
                platformId = platformId,
                message = err.failed_msg,
                timestamp = err.failed_timestamp,
                code = 'DownloadError')
            ret.resourceError.append(e)
        return ret
