#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

from conary import dbstore
from conary.dbstore import sqlerrors
from conary.lib.util import rethrow

from mint import mint_error
from mint.db import schema

from mint.db import builds
from mint.db import jobs
from mint.db import mirror
from mint.db import pkgindex
from mint.db import platforms
from mint.db import projects
from mint.db import pubreleases
from mint.db import requests
from mint.db import sessiondb
from mint.db import stats
from mint.db import targets
from mint.db import users

from mint.lib import database as dblib

class TableCache(object):
    def __init__(self, db, cfg):
        self.auth_tokens = builds.AuthTokensTable(db)
        self.labels = projects.LabelsTable(db, cfg)
        self.projects = projects.ProjectsTable(db, cfg)
        self.buildFiles = jobs.BuildFilesTable(db)
        self.filesUrls = jobs.FilesUrlsTable(db)
        self.buildFilesUrlsMap = jobs.BuildFilesUrlsMapTable(db)
        self.urlDownloads = builds.UrlDownloadsTable(db)
        self.users = users.UsersTable(db, cfg)
        self.userData = users.UserDataTable(db)
        self.projectUsers = projects.ProjectUsersTable(db)
        self.builds = builds.BuildsTable(db)
        self.pkgIndex = pkgindex.PackageIndexTable(db)
        self.sessions = sessiondb.SessionsTable(db)
        self.membershipRequests = requests.MembershipRequestTable(db)
        self.commits = stats.CommitsTable(db)
        self.buildData = builds.BuildDataTable(db)
        self.inboundMirrors = mirror.InboundMirrorsTable(db)
        self.outboundMirrors = mirror.OutboundMirrorsTable(db, cfg)
        self.updateServices = mirror.UpdateServicesTable(db, cfg)
        self.outboundMirrorsUpdateServices = mirror.OutboundMirrorsUpdateServicesTable(db)
        self.publishedReleases = pubreleases.PublishedReleasesTable(db)
        self.productVersions = projects.ProductVersionsTable(db, cfg)

        self.targets = targets.TargetsTable(db)
        self.targetData = targets.TargetDataTable(db)

        self.platforms = platforms.PlatformsTable(db, cfg)
        self.platformSources = platforms.PlatformSourcesTable(db, cfg)
        self.platformSourceData = platforms.PlatformSourceDataTable(db)
        self.platformsPlatformSources = platforms.PlatformsPlatformSourcesTable(db)
        self.platformsContentSourceTypes = platforms.PlatformsContentSourceTypesTable(db)

        self.users.confirm_table.db = db
        self.projects.reposDB.cfg = cfg

class Database(object):
    # Not the ideal place to put these, but I wanted to easily find them later
    # --misa
    EC2TargetType = 'ec2'
    EC2TargetName = 'aws'

    def __init__(self, cfg, db=None):
        self._cfg = cfg
        self._db = db
        self._autoDb = False

        self._openDb()

    def _copyTables(self, tables):
        self.auth_tokens = tables.auth_tokens
        self.labels = tables.labels
        self.projects = tables.projects
        self.buildFiles = tables.buildFiles
        self.filesUrls = tables.filesUrls
        self.buildFilesUrlsMap = tables.buildFilesUrlsMap
        self.urlDownloads = tables.urlDownloads
        self.users = tables.users
        self.userData = tables.userData
        self.projectUsers = tables.projectUsers
        self.builds = tables.builds
        self.pkgIndex = tables.pkgIndex
        self.sessions = tables.sessions
        self.membershipRequests = tables.membershipRequests
        self.commits = tables.commits
        self.buildData = tables.buildData
        self.inboundMirrors = tables.inboundMirrors
        self.outboundMirrors = tables.outboundMirrors
        self.updateServices = tables.updateServices
        self.outboundMirrorsUpdateServices = tables.outboundMirrorsUpdateServices
        self.publishedReleases = tables.publishedReleases
        self.productVersions = tables.productVersions
        self.platforms = tables.platforms
        self.platformSources = tables.platformSources
        self.platformSourceData = tables.platformSourceData
        self.platformsPlatformSources = tables.platformsPlatformSources
        self.platformsContentSourceTypes = tables.platformsContentSourceTypes

        self.targets = tables.targets
        self.targetData = tables.targetData

    @property
    def db(self):
        return self._db

    @property
    def driver(self):
        return self._db.driver

    def _openDb(self):
        if not self._db:
            self._db = dbstore.connect(self._cfg.dbPath, self._cfg.dbDriver)
            self._autoDb = True

        # check to make sure the schema version is correct
        try:
            schema.checkVersion(self._db)
        except sqlerrors.SchemaVersionError:
            rethrow(mint_error.DatabaseVersionMismatch, False)

        tables = TableCache(self._db, self._cfg)
        self._copyTables(tables)
        if self._db.inTransaction(True):
            self._db.commit()

    def close(self):
        if self._autoDb:
            self._db.close()
            self._db = None

    def reopen_fork(self, forked=False):
        """Re-open the database connection after a fork()."""
        self._db.close_fork()
        self._db = None
        self._openDb()

    def cursor(self):
        return self._db.cursor()

    def reopen(self):
        return self._db.reopen()

    def rollback(self):
        return self._db.rollback()

    def commit(self):
        return self._db.commit()

    def transaction(self):
        return self._db.transaction()

    def inTransaction(self, default=None):
        return self._db.inTransaction(default)

    def _getOne(self, cu, exception, key):
        try:
            cu = iter(cu)
            res = cu.next()
            assert (not(list(cu))), key # make sure that we really only
                                        # got one entry
            return res
        except:
            raise exception(key)
