#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from conary import versions
from conary.lib import util
from mint.lib import mintutils
from mint.rest.db import manager
from restlib import response
from mint.rest.api import models

import rpath_capsule_indexer

class Indexer(rpath_capsule_indexer.Indexer):
    class SourceChannels(rpath_capsule_indexer.Indexer.SourceChannels):
        LOGFILE_PATH = None
        def getLogger(self):
            consoleLevel = (self.LOGFILE_PATH is None
                and mintutils.logging.WARNING) or mintutils.logging.CRITICAL
            logger = mintutils.setupLogging(logger=__name__,
                consoleLevel=consoleLevel, consoleFormat='apache',
                logPath=self.LOGFILE_PATH)
            return logger

class CapsuleManager(manager.Manager):
    SourcesRHN = set(['RHN', 'satellite', 'proxy'])
    SourcesYum = set(['nu', 'SMT'])

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
        cfg.configLine("registeredSystemPrefix rbuilder %s" %
            self.cfg.siteHost)

        dataSources = self.db.platformMgr.getSources().instance or []
        yumSources = []
        for idx, dataSource in enumerate(dataSources):
            if None in (dataSource.username, dataSource.password):
                if dataSource.contentSourceType in self.SourcesRHN:
                    # Not fully configured yet
                    continue
            if dataSource.contentSourceType == 'RHN':
                dsn = 'RHN'
                sourceHost = None
            elif dataSource.contentSourceType in self.SourcesRHN:
                sourceType = 'source'
                dsn = 'source_%d' % idx
                sourceHost = dataSource.sourceUrl
                if '/' in sourceHost:
                    sourceHost = util.urlSplit(sourceHost)[3]
            elif dataSource.contentSourceType in self.SourcesYum:
                if dataSource.contentSourceType == 'nu':
                    url = 'https://nu.novell.com/repo/$RCE'
                else:
                    url = dataSource.sourceUrl
                arr = list(util.urlSplit(url))
                if dataSource.username is not None:
                    arr[1] = dataSource.username
                if dataSource.password is not None:
                    arr[2] = dataSource.password
                yumSources.append(util.urlUnsplit(arr))
                # We configure yum sources further down
                continue
            cfg.configLine("user %s %s %s" % (dsn, dataSource.username,
                dataSource.password))
            if sourceHost:
                cfg.configLine("%s %s %s" % (sourceType, dsn, sourceHost))
        # List configured platforms
        for platform in self.db.platformMgr.platforms.list().platforms:
            if not platform.enabled:
                continue
            platDef = self.db.platformMgr.platformCache.get(platform.label)
            if platDef is None:
                continue
            contentProvider = platDef.getContentProvider()
            if not contentProvider:
                continue
            if contentProvider.name == 'rhn':
                for ds in contentProvider.dataSources:
                    cfg.configLine("channels %s" % ds.name)
                continue
            for ds in contentProvider.dataSources:
                for ys in yumSources:
                    cfg.configLine("sourceYum %s %s/%s"% (ds.name, ys, ds.name))

        # Copy proxy information
        cfg.proxy = self.db.cfg.proxy.copy()

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
        Indexer.SourceChannels.LOGFILE_PATH = util.joinPaths(self.cfg.logPath,
            'capsule-indexer.log')
        return Indexer(cfg)

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
