#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from conary import versions
from conary.lib import util
from mint.rest.db import manager
from restlib import response
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

    def getContentInjectionServers(self):
        # Grab labels for enabled platforms that have capsule content
        labels = self.db.platformMgr.getContentEnabledPlatformLabels()
        ret = []
        for label in labels:
            try:
                label = versions.Label(label).getHost()
            except versions.ParseError:
                # Oh well, try to use it as is
                pass
            ret.append(label)
        return ret

    def getIndexer(self):
        cfg = self.getIndexerConfig()
        return rpath_capsule_indexer.Indexer(cfg)

    def getIndexerErrors(self, contentSourceName, instanceName):
        indexer = self.getIndexer()

        errors = indexer.model.getPackageDownloadFailures()
        ret = models.ResourceErrors()
        for err in errors:
            # For now we only have DownloadError as code
            e = self._oneFailure(err, contentSourceName, instanceName)
            ret.resourceError.append(e)
        return ret

    def getIndexerError(self, contentSourceName, instanceName, errorId):
        indexer = self.getIndexer()

        err = indexer.model.getPackageDownloadFailure(errorId)
        if not err:
            return response.Response(status = 404)
        return self._oneFailure(err, contentSourceName, instanceName)

    def updateIndexerError(self, contentSourceName, instanceName, errorId,
            resourceError):
        indexer = self.getIndexer()

        err = indexer.model.getPackageDownloadFailure(errorId)
        if not err:
            return response.Response(status = 404)

        # sqlalchemy doesn't like unicode passed to psycopg2, but it seems to
        # only be a problem when run from apache
        resolvedMessage = resourceError.resolvedMessage
        if resolvedMessage is not None:
            resolvedMessage = str(resolvedMessage)
        err.resolved = resolvedMessage

        indexer.model.commit()

        err = indexer.model.getPackageDownloadFailure(errorId)
        return self._oneFailure(err, contentSourceName, instanceName)

    @classmethod
    def _oneFailure(cls, err, contentSourceName, instanceName):
        ret = models.ResourceError(id = err.package_failed_id,
                contentSourceName = contentSourceName,
                instanceName = instanceName,
                message = err.failed_msg,
                timestamp = err.failed_timestamp,
                resolved = bool(err.resolved),
                resolvedMessage = err.resolved,
                code = 'DownloadError')
        return ret
