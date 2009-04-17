import sys

from conary import dbstore
from conary.dbstore import sqlerrors

from mint import mint_error
from mint.db import schema

from mint.db import builds
from mint.db import communityids
from mint.db import ec2
from mint.db import grouptrove
from mint.db import jobs
from mint.db import news
from mint.db import mirror
from mint.db import pkgindex
from mint.db import projects
from mint.db import pubreleases
from mint.db import requests
from mint.db import sessiondb
from mint.db import selections
from mint.db import stats
from mint.db import targets
from mint.db import users



dbConnection = None
tables = None

class TableCache(object):
    def __init__(self, db, cfg):
        self.labels = projects.LabelsTable(db, cfg)
        self.projects = projects.ProjectsTable(db, cfg)
        self.buildFiles = jobs.BuildFilesTable(db)
        self.filesUrls = jobs.FilesUrlsTable(db)
        self.buildFilesUrlsMap = jobs.BuildFilesUrlsMapTable(db)
        self.urlDownloads = builds.UrlDownloadsTable(db)
        self.users = users.UsersTable(db, cfg)
        self.userGroups = users.UserGroupsTable(db, cfg)
        self.userGroupMembers = users.UserGroupMembersTable(db, cfg)
        self.userData = users.UserDataTable(db)
        self.projectUsers = projects.ProjectUsersTable(db)
        self.builds = builds.BuildsTable(db)
        self.pkgIndex = pkgindex.PackageIndexTable(db)
        self.newsCache = news.NewsCacheTable(db, cfg)
        self.sessions = sessiondb.SessionsTable(db)
        self.membershipRequests = requests.MembershipRequestTable(db)
        self.commits = stats.CommitsTable(db)
        self.buildData = builds.BuildDataTable(db)
        self.groupTroves = grouptrove.GroupTroveTable(db, cfg)
        self.groupTroveItems = grouptrove.GroupTroveItemsTable(db, cfg)
        self.conaryComponents = grouptrove.ConaryComponentsTable(db)
        self.groupTroveRemovedComponents = grouptrove.GroupTroveRemovedComponentsTable(db)
        self.jobData = jobs.JobDataTable(db)
        self.inboundMirrors = mirror.InboundMirrorsTable(db)
        self.outboundMirrors = mirror.OutboundMirrorsTable(db, cfg)
        self.updateServices = mirror.UpdateServicesTable(db, cfg)
        self.outboundMirrorsUpdateServices = mirror.OutboundMirrorsUpdateServicesTable(db)
        self.repNameMap = mirror.RepNameMapTable(db)
        self.selections = selections.FrontPageSelectionsTable(db, cfg)
        self.topProjects = selections.TopProjectsTable(db)
        self.popularProjects = selections.PopularProjectsTable(db)
        self.latestCommit = selections.LatestCommitTable(db)
        self.publishedReleases = pubreleases.PublishedReleasesTable(db)
        self.blessedAMIs = ec2.BlessedAMIsTable(db)
        self.launchedAMIs = ec2.LaunchedAMIsTable(db)
        self.communityIds = communityids.CommunityIdsTable(db)
        self.productVersions = projects.ProductVersionsTable(db, cfg)

        self.targets = targets.TargetsTable(db)
        self.targetData = targets.TargetDataTable(db)

        self.users.confirm_table.db = db
        self.newsCache.ageTable.db = db
        self.projects.reposDB.cfg = cfg
        # make sure we commit after creating all of this, as
        # instantiating some of these tables may perform inserts...
        db.commit()


class Database(object):

    def __init__(self, cfg, db=None, alwaysReload=False):
        db, reloadTables = self._openDb(cfg.dbDriver, cfg.dbPath, db, 
                                        alwaysReload)
        self._cfg = cfg

        # check to make sure the schema version is correct
        try:
            schema.checkVersion(db)
        except sqlerrors.SchemaVersionError, e:
            raise mint_error.DatabaseVersionMismatch(e.args[0])
        self._db = db
        global tables
        if not tables or reloadTables:
            tables = TableCache(db, cfg)
            self.tablesReloaded = True
        else:
            self.tablesReloaded = False

        self.labels = tables.labels
        self.projects = tables.projects
        self.buildFiles = tables.buildFiles
        self.filesUrls = tables.filesUrls
        self.buildFilesUrlsMap = tables.buildFilesUrlsMap
        self.urlDownloads = tables.urlDownloads
        self.users = tables.users
        self.userGroups = tables.userGroups
        self.userGroupMembers = tables.userGroupMembers
        self.userData = tables.userData
        self.projectUsers = tables.projectUsers
        self.builds = tables.builds
        self.pkgIndex = tables.pkgIndex
        self.newsCache = tables.newsCache
        self.sessions = tables.sessions
        self.membershipRequests = tables.membershipRequests
        self.commits = tables.commits
        self.buildData = tables.buildData
        self.groupTroves = tables.groupTroves
        self.groupTroveItems = tables.groupTroveItems
        self.conaryComponents = tables.conaryComponents
        self.groupTroveRemovedComponents = tables.groupTroveRemovedComponents
        self.jobData = tables.jobData
        self.inboundMirrors = tables.inboundMirrors
        self.outboundMirrors = tables.outboundMirrors
        self.updateServices = tables.updateServices
        self.outboundMirrorsUpdateServices = tables.outboundMirrorsUpdateServices
        self.repNameMap = tables.repNameMap
        self.selections = tables.selections
        self.topProjects = tables.topProjects
        self.popularProjects = tables.popularProjects
        self.latestCommit = tables.latestCommit
        self.publishedReleases = tables.publishedReleases
        self.blessedAMIs = tables.blessedAMIs
        self.launchedAMIs = tables.launchedAMIs
        self.communityIds = tables.communityIds
        self.productVersions = tables.productVersions

        self.targets = tables.targets
        self.targetData = tables.targetData

        if self.tablesReloaded:
            self.normalizeMirrorOrder()

    def _getDb(self):
        return self._db
    db = property(_getDb)

    def _openDb(self, dbDriver, dbPath, db, alwaysReload):
        global dbConnection
        if db and not db.poolmode:
            dbConnection = db

        # Flag to indicate if we created a new self.db and need to force a
        # call to getTables
        reloadTables = False

        if dbConnection and not alwaysReload:
            db = dbConnection

            # reopen a dead database
            if db.reopen():
                print >> sys.stderr, "reopened dead database connection in mint server"
                sys.stderr.flush()
        else:
            db = dbstore.connect(dbPath, driver=dbDriver)
            if not db.poolmode:
                dbConnection = db
            reloadTables = True

        return db, reloadTables

    def close(self):
        return self._db.close()

    def getDriver(self):
        return self._db.driver
    driver = property(getDriver)

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

    def normalizeMirrorOrder(self):
        self._normalizeMirrorOrder("OutboundMirrors", "outboundMirrorId")
        self._normalizeMirrorOrder("InboundMirrors", "inboundMirrorId")

    def _normalizeMirrorOrder(self, table, idField):
        # normalize mirror order, in case of deletions
        updates = []
        cu = self.db.cursor()
        cu.execute("SELECT mirrorOrder, %s FROM %s ORDER BY mirrorOrder ASC"
                % (idField, table))
        for newIndex, (oldIndex, rowId) in enumerate(cu.fetchall()):
            if newIndex != oldIndex:
                updates.append((newIndex, rowId))

        if updates:
            cu.executemany("UPDATE %s SET mirrorOrder=? WHERE %s=?"
                    % (table, idField), updates)
            self.db.commit()

    def _getOne(self, cu, exception, key):
        try:
            cu = iter(cu)
            res = cu.next()
            assert (not(list(cu))), key # make sure that we really only
                                        # got one entry
            return res
        except:
            raise exception(key)
