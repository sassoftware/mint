#
# Copyright (c) 2005-2006 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.opensource.org/licenses/cpl.php.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

from conary import dbstore
from conary.dbstore import migration, sqlerrors, idtable
from conary.lib.tracelog import logMe

# XXX THIS IS NOT THE SCHEMA FOR RBUILDER -- YET!
# XXX THIS IS A *PROPOSED* SCHEMA FOR RBUILDER!
# XXX THIS IS MERELY BEING CHECKED IN FOR REVIEW!
#
# TODO
# 0. Review changes
# 1. Sync rbuilder code to use new schema.
#    a. new timestamp handling (YYYYMMDDhhmmss)
#    b. update renamed columns
#    c. sessions table is now outside the main schema (new connection)
#    d. anything else I forgot
# 2. Remove old table creation code from existing DatabaseTable objects
# 3. Port migration code from mint/*.py (DatabaseTable objects)

# database schema version
VERSION = 26 # this needs to be +1 from the CURRENT version in mint/database.py

def _createTrigger(db, table, column = "changed", pinned = False):
    retInsert = db.createTrigger(table, column, "INSERT")
    retUpdate = db.createTrigger(table, column, "UPDATE", pinned=pinned)
    return retInsert or retUpdate

def _createUsers(db):
    cu = db.cursor()
    commit = False

    # users
    if 'Users' not in db.tables:
        cu.execute("""
        CREATE TABLE Users (
            userId          %(PRIMARYKEY)s,
            username        VARCHAR(128) NOT NULL,
            password        %(BINARY254)s,
            salt            %(BINARY4)s NOT NULL,
            fullname        VARCHAR(128),
            email           VARCHAR(128) NOT NULL,
            confirmation    VARCHAR(254),
            contactInfo     TEXT,
            additionalInfo  TEXT,
            active          INTEGER NOT NULL DEFAULT 0,
            timeCreated     NUMERIC(14,0) NOT NULL DEFAULT 0,
            timeUpdated     NUMERIC(14,0) NOT NULL DEFAULT 0,
            timeAccessed    NUMERIC(14,0) NOT NULL DEFAULT 0
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['Users'] = []
        commit = True
    db.createIndex('Users', 'Users_uq', 'username', unique = True)
    # need to check to see if we need an index on username, active
    if db.createTrigger('Users', 'timeCreated', 'INSERT'):
        commit = True
    if _createTrigger(db, 'Users', 'timeUpdated'):
        commit = True

    # userData
    if 'UserData' not in db.tables:
        cu.execute("""
        CREATE TABLE UserData (
            userId          INTEGER NOT NULL,
            name            VARCHAR(32) NOT NULL,
            value           TEXT,
            valueType       INTEGER NOT NULL,
            CONSTRAINT UserData_userId_fk
                FOREIGN KEY (userId) REFERENCES Users(userId)
                    ON DELETE CASCADE ON UPDATE CASCADE
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['UserData'] = []
        commit = True
    db.createIndex('UserData', 'UserData_uq', 'userId, name', unique = True)

    # userGroups
    if 'UserGroups' not in db.tables:
        cu.execute("""
        CREATE TABLE UserGroups (
            userGroupId     %(PRIMARYKEY)s,
            userGroup       VARCHAR(128) NOT NULL
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['UserGroups'] = []
        commit = True
    db.createIndex('UserGroups', 'UserGroups_uq', 'userGroup', unique = True)

    # userGroupMembers
    if 'UserGroupMembers' not in db.tables:
        cu.execute("""
        CREATE TABLE UserGroupMembers (
            userGroupId     INTEGER NOT NULL,
            userId          INTEGER NOT NULL,
            CONSTRAINT UserGroupMembers_userGroupId_fk
                FOREIGN KEY (userGroupId) REFERENCES UserGroups(userGroupId)
                ON DELETE RESTRICT ON UPDATE CASCADE,
            CONSTRAINT UserGroupMembers_userId_fk
                FOREIGN KEY (userId) REFERENCES Users(userId)
                ON DELETE CASCADE ON UPDATE CASCADE
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['UserGroupMembers'] = []
        commit = True
    db.createIndex('UserGroupMembers', 'UserGroupMembers_uq',
                   'userGroupId, userId', unique = True)
    db.createIndex('UserGroupMembers', 'UserGroupMembersUserIdx', 'userId')

    if commit:
        db.commit()
        db.loadSchema()


def _createLabels(db):
    cu = db.cursor()
    commit = False

    # labels
    if 'Labels' not in db.tables:
        cu.execute("""
        CREATE TABLE Labels (
            labelId         %(PRIMARYKEY)s,
            label           VARCHAR(767) NOT NULL,
            url             VARCHAR(767) NOT NULL,
            username        VARCHAR(254),
            password        VARCHAR(254)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Labels'] = []
        commit = True

    if commit:
        db.commit()
        db.loadSchema()


def _createProjects(db):
    cu = db.cursor()
    commit = False

    # projects
    if 'Projects' not in db.tables:
        cu.execute("""
        CREATE TABLE Projects (
            projectId       %(PRIMARYKEY)s,
            name            VARCHAR(128) NOT NULL,
            hostname        VARCHAR(128) NOT NULL,
            domainname      VARCHAR(128) NOT NULL,
            projectUrl      VARCHAR(767) NOT NULL DEFAULT '',
            description     TEXT NOT NULL DEFAULT '',
            hidden          INTEGER NOT NULL DEFAULT 0,
            external        INTEGER NOT NULL DEFAULT 0,
            timeCreated     NUMERIC(14,0) NOT NULL DEFAULT 0,
            createdBy       INTEGER,
            timeUpdated     NUMERIC(14,0) NOT NULL DEFAULT 0,
            CONSTRAINT Projects_createdBy_fk
                FOREIGN KEY (createdBy) REFERENCES Users(userId)
                ON DELETE SET NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Projects'] = []
        commit = True
    db.createIndex('Projects', 'ProjectsName_uq', 'name',
            unique = True)
    db.createIndex('Projects', 'ProjectsHostname_uq', 'hostname',
            unique = True)
    db.createIndex('Projects', 'ProjectsNameHiddenExternalIdx',
            'name, hidden, external')
    if db.createTrigger('Projects', 'timeCreated', 'INSERT'):
        commit = True
    if _createTrigger(db,'Projects', 'timeUpdated'):
        commit = True

    # projectLabels
    if 'ProjectLabels' not in db.tables:
        cu.execute("""
        CREATE TABLE ProjectLabels (
            projectId       INTEGER NOT NULL,
            labelId         INTEGER NOT NULL,
            CONSTRAINT ProjectLabels_projectId_fk
                FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                ON DELETE CASCADE,
            CONSTRAINT ProjectLabels_labelId_fk
                FOREIGN KEY (labelId) REFERENCES Labels(labelId)
                ON DELETE RESTRICT ON UPDATE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['ProjectLabels'] = []
    db.createIndex('ProjectLabels', 'ProjectLabels_uq',
            'projectId, labelId', unique = True)

    # projectUsers
    if 'ProjectUsers' not in db.tables:
        cu.execute("""
        CREATE TABLE ProjectUsers (
            projectId       INTEGER NOT NULL,
            userId          INTEGER NOT NULL,
            level           INTEGER,
            CONSTRAINT ProjectUsers_projectId_fk
                FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                ON DELETE CASCADE ON UPDATE CASCADE,
            CONSTRAINT ProjectUsers_userId_fk
                FOREIGN KEY (userId) REFERENCES Users(userId)
                ON DELETE CASCADE ON UPDATE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['ProjectUsers'] = []
        commit = True
    db.createIndex('ProjectUsers', 'ProjectUsers_uq', 'projectId, userId',
            unique = True)

    # membershipRequests
    if 'MembershipRequests' not in db.tables:
        cu.execute("""
        CREATE TABLE MembershipRequests (
            projectId       INTEGER NOT NULL,
            userId          INTEGER NOT NULL,
            comments        TEXT,
            CONSTRAINT MembershipRequests_projectId_fk
                FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                ON DELETE CASCADE ON UPDATE CASCADE,
            CONSTRAINT MembershipRequests_userId_fk
                FOREIGN KEY (userId) REFERENCES Users(userId)
                ON DELETE CASCADE ON UPDATE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['MembershipRequests'] = []
        commit = True
    db.createIndex('MembershipRequests',
            'MembershipRequests_uq',
            'projectId, userId', unique = True)

    if commit:
        db.commit()
        db.loadSchema()


def _createBuilds(db):
    cu = db.cursor()
    commit = False

    # publishedReleases
    if 'PublishedReleases' not in db.tables:
        cu.execute("""
        CREATE TABLE PublishedReleases (
            pubReleaseId    %(PRIMARYKEY)s,
            projectId       INTEGER,
            name            VARCHAR(254),
            version         VARCHAR(254),
            description     TEXT,
            timeCreated     NUMERIC(14,0) NOT NULL DEFAULT 0,
            createdBy       INTEGER,
            timeUpdated     NUMERIC(14,0) NOT NULL DEFAULT 0,
            updatedBy       INTEGER,
            timePublished   NUMERIC(14,0),
            publishedBy     INTEGER,
            CONSTRAINT PublishedReleases_projectId_fk
                FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                ON DELETE RESTRICT,
            CONSTRAINT PublishedReleases_createdBy_fk
                FOREIGN KEY (createdBy) REFERENCES Users(userId)
                ON DELETE SET NULL,
            CONSTRAINT PublishedReleases_updatedBy_fk
                FOREIGN KEY (updatedBy) REFERENCES Users(userId)
                ON DELETE SET NULL,
            CONSTRAINT PublishedReleases_publishedBy_fk
                FOREIGN KEY (publishedBy) REFERENCES Users(userId)
                ON DELETE SET NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['PublishedReleases'] = []
        commit = True
    if db.createTrigger('PublishedReleases', 'timeCreated', 'INSERT'):
        commit = True
    if _createTrigger(db, 'PublishedReleases', 'timeUpdated'):
        commit = True

    # builds
    if 'Builds' not in db.tables:
        cu.execute("""
        CREATE TABLE Builds (
            buildId              %(PRIMARYKEY)s,
            projectId            INTEGER NOT NULL,
            pubReleaseId         INTEGER,
            buildType            INTEGER NOT NULL,
            name                 VARCHAR(254),
            description          TEXT,
            troveName            VARCHAR(767),
            troveVersion         VARCHAR(767),
            troveFlavor          VARCHAR(767),
            troveLastChanged     INTEGER,
            timeCreated          NUMERIC(14,0) NOT NULL DEFAULT 0,
            createdBy            INTEGER,
            timeUpdated          NUMERIC(14,0) NOT NULL DEFAULT 0,
            updatedBy            INTEGER,
            CONSTRAINT Builds_projectId_fk
                FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                ON DELETE CASCADE,
            CONSTRAINT Builds_pubReleaseId_fk
                FOREIGN KEY (pubReleaseId)
                    REFERENCES PublishedReleases(pubReleaseId)
                ON DELETE SET NULL,
            CONSTRAINT Builds_createdBy_fk
                FOREIGN KEY (createdBy) REFERENCES Users(userId)
                ON DELETE SET NULL,
            CONSTRAINT Builds_updatedBy_fk
                FOREIGN KEY (updatedBy) REFERENCES Users(userId)
                ON DELETE SET NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Builds'] = []
        commit = True
    if db.createTrigger('Builds', 'timeCreated', 'INSERT'):
        commit = True
    if _createTrigger(db, 'Builds', 'timeUpdated'):
        commit = True

    # buildData
    if 'BuildData' not in db.tables:
        cu.execute("""
        CREATE TABLE BuildData (
            buildId         INTEGER NOT NULL,
            name            VARCHAR(32),
            value           TEXT,
            valueType       INTEGER NOT NULL,
            CONSTRAINT BuildData_buildId_fk
                FOREIGN KEY (buildId) REFERENCES Builds(buildId)
                ON DELETE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['BuildData'] = []
        commit = True
    db.createIndex('BuildData', 'BuildData_uq', 'buildId, name', unique = True)

    # buildFiles
    if 'BuildFiles' not in db.tables:
        cu.execute("""
        CREATE TABLE BuildFiles (
            fileId          %(PRIMARYKEY)s,
            buildId         INTEGER NOT NULL,
            idx             INTEGER NOT NULL,
            filename        VARCHAR(254) NOT NULL,
            title           VARCHAR(254) DEFAULT '',
            size            BIGINT,
            sha1            CHAR(40),
            CONSTRAINT BuildFiles_buildId_fk
                FOREIGN KEY (buildId) REFERENCES Builds(buildId)
                ON DELETE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['BuildFiles'] = []
        commit = True

    # filesUrls
    if 'FilesUrls' not in db.tables:
        cu.execute("""
        CREATE TABLE FilesUrls (
            urlId           %(PRIMARYKEY)s,
            urlType         INTEGER NOT NULL,
            url             VARCHAR(254) NOT NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['FilesUrls'] = []
        commit = True

    # buildFilesUrlsMap
    if 'BuildFilesUrlsMap' not in db.tables:
        cu.execute("""
        CREATE TABLE BuildFilesUrlsMap (
            fileId  INTEGER NOT NULL,
            urlId   INTEGER NOT NULL,
            CONSTRAINT BuildFilesUrlsMap_fileId_fk FOREIGN KEY(fileId)
                REFERENCES BuildFiles (fileId)
                ON DELETE CASCADE,
            CONSTRAINT BuildFilesUrlsMap_urlId_fk FOREIGN KEY(urlId)
                REFERENCES FilesUrls(urlId)
                ON DELETE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['BuildFilesUrlsMap'] = []
        commit = True
    db.createIndex("BuildFilesUrlsMap", "BuildFilesUrlsMap_f_u_idx",
                   "fileId, urlId", unique = True)

    if 'UrlDownloads' not in db.tables:
        cu.execute("""
            CREATE TABLE UrlDownloads (
                urlId               INTEGER NOT NULL,
                url                 VARCHAR(255),
                timeDownloaded      NUMERIC(14,0) NOT NULL DEFAULT 0,
                ip                  CHAR(15)
            )""" % db.keywords)
        db.tables['UrlDownloads'] = []
        commit = True

    if commit:
        db.commit()
        db.loadSchema()

def _createCommits(db):
    cu = db.cursor()
    commit = False

    # commits
    if 'Commits' not in db.tables:
        cu.execute("""
        CREATE TABLE Commits (
            projectId       INTEGER NOT NULL,
            timestamp       INTEGER,
            troveName       VARCHAR(767),
            version         TEXT,
            userId          INTEGER,
            CONSTRAINT Commits_projectId_fk
                FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                ON DELETE CASCADE,
            CONSTRAINT Commits_userId_fk
                FOREIGN KEY (userId) REFERENCES Users(userId)
                ON DELETE SET NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Commits'] = []
        commit = True
    db.createIndex('Commits', 'CommitsProjectTimestampIdx',
            'projectId, timestamp')
    db.createIndex('Commits', 'CommitsTroveProjectIdx', 'troveName, projectId')
    db.createIndex('Commits', 'CommitsProjectTroveIdx', 'projectId, troveName')
    db.createIndex('Commits', 'CommitsProjectUserIdx', 'projectId, userId')

    if commit:
        db.commit()
        db.loadSchema()

def _createGroupTroves(db):
    cu = db.cursor()
    commit = False

    # groupTroves
    if 'GroupTroves' not in db.tables:
        cu.execute("""
        CREATE TABLE GroupTroves(
            groupTroveId    %(PRIMARYKEY)s,
            projectId       INTEGER NOT NULL,
            recipeName      VARCHAR(200),
            upstreamVersion VARCHAR(128),
            description     TEXT,
            autoResolve     INTEGER,
            timeCreated     INTEGER,
            createdBy       INTEGER,
            timeModified    INTEGER,
            CONSTRAINT GroupTroves_projectId_fk
                FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                ON DELETE CASCADE,
            CONSTRAINT GroupTroves_createdBy_fk
                FOREIGN KEY (createdBy) REFERENCES Users(userId)
                ON DELETE SET NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['GroupTroves'] = []
        commit = True
    if db.createTrigger('GroupTroves', 'timeCreated', 'INSERT'):
        commit = True
    if _createTrigger(db, 'GroupTroves', 'timeModified'):
        commit = True

    # groupTroves
    if 'GroupTroveItems' not in db.tables:
        cu.execute("""
        CREATE TABLE GroupTroveItems(
            groupTroveItemId    %(PRIMARYKEY)s,
            groupTroveId        INTEGER NOT NULL,
            createdBy           INTEGER,
            troveName           VARCHAR(767),
            troveVersion        VARCHAR(767),
            troveFlavor         VARCHAR(767),
            subGroup            VARCHAR(128),
            versionLock         INTEGER NOT NULL DEFAULT 0,
            useLock             INTEGER NOT NULL DEFAULT 0,
            instSetLock         INTEGER NOT NULL DEFAULT 0,
            CONSTRAINT GroupTroveItems_groupTroveId_fk
                FOREIGN KEY (groupTroveId) REFERENCES GroupTroves(groupTroveId)
                ON DELETE CASCADE,
            CONSTRAINT GroupTroveItems_createdBy_fk
                FOREIGN KEY (createdBy) REFERENCES Users(userId)
                ON DELETE SET NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['GroupTroveItems'] = []
        commit = True

    # conaryComponents
    if 'ConaryComponents' not in db.tables:
        cu.execute("""
        CREATE TABLE ConaryComponents(
             componentId    %(PRIMARYKEY)s,
             component      VARCHAR(128)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['ConaryComponents'] = []
        commit = True
    db.createIndex('ConaryComponents', 'ConaryComponents_uq',
            'component', unique = True)

    # groupTroveRemovedComponents
    if 'GroupTroveRemovedComponents' not in db.tables:
        cu.execute("""
        CREATE TABLE GroupTroveRemovedComponents(
             groupTroveId   INTEGER NOT NULL,
             componentId    INTEGER NOT NULL,
             CONSTRAINT GroupTroveRemovedComponents_groupTroveId_fk
                FOREIGN KEY (groupTroveId) REFERENCES GroupTroves(groupTroveId)
                ON DELETE CASCADE ON UPDATE CASCADE,
             CONSTRAINT GroupTroveRemovedComponents_componentId_fk
                FOREIGN KEY (componentId) REFERENCES ConaryComponents(componentId)
                ON DELETE RESTRICT ON UPDATE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['GroupTroveRemovedComponents'] = []
        commit = True

    if commit:
        db.commit()
        db.loadSchema()



def _createJobs(db):
    cu = db.cursor()
    commit = False

    # jobs
    if 'Jobs' not in db.tables:
        cu.execute("""
        CREATE TABLE Jobs (
            jobId           %(PRIMARYKEY)s,
            buildId         INTEGER,
            groupTroveId    INTEGER,
            owner           BIGINT,
            userId          INTEGER,
            status          INTEGER NOT NULL DEFAULT 0,
            statusMessage   TEXT,
            timeSubmitted   NUMERIC(14,0) NOT NULL DEFAULT 0,
            timeStarted     NUMERIC(14,0) NOT NULL DEFAULT 0,
            timeFinished    NUMERIC(14,0) NOT NULL DEFAULT 0,
            CONSTRAINT Jobs_buildId_fk
                FOREIGN KEY (buildId) REFERENCES Builds(buildId),
            CONSTRAINT Jobs_groupTroveId_fk
                FOREIGN KEY (groupTroveId) REFERENCES GroupTroves(groupTroveId),
            CONSTRAINT Jobs_userId_fk
                FOREIGN KEY (userId) REFERENCES Users(userId)
                ON DELETE SET NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Jobs'] = []
        commit = True

    # jobData
    if 'JobData' not in db.tables:
        cu.execute("""
        CREATE TABLE JobData (
            jobId           INTEGER NOT NULL,
            name            VARCHAR(32),
            value           TEXT,
            valueType       INTEGER NOT NULL,
            CONSTRAINT JobData_jobId_fk
                FOREIGN KEY (jobId) REFERENCES Jobs(jobId)
                ON DELETE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['JobData'] = []
        commit = True
    db.createIndex('JobData', 'JobData_uq', 'jobId, name', unique = True)

    if commit:
        db.commit()
        db.loadSchema()


def _createPackageIndex(db):
    cu = db.cursor()
    commit = False

    # packageIndex
    if 'PackageIndex' not in db.tables:
        cu.execute("""
        CREATE TABLE PackageIndex (
            pkgId           %(PRIMARYKEY)s,
            projectId       INTEGER NOT NULL,
            name            VARCHAR(254) NOT NULL,
            version         VARCHAR(254) NOT NULL,
            CONSTRAINT PackageIndex_projectId_fk
                FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                ON DELETE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['PackageIndex'] = []
        commit = True
    db.createIndex("PackageIndex", "PackageIndexNameIdx", "name, projectId")

    # packageIndexMark
    if 'PackageIndexMark' not in db.tables:
        cu.execute("""
        CREATE TABLE PackageIndexMark (
            mark            INTEGER NOT NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['PackageIndexMark'] = []
        commit = True

    if commit:
        db.commit()
        db.loadSchema()

def _createNewsCache(db):
    cu = db.cursor()
    commit = False

    # newsCache
    if 'NewsCache' not in db.tables:
        cu.execute("""
        CREATE TABLE NewsCache (
            itemId          %(PRIMARYKEY)s,
            title           VARCHAR(254) NOT NULL DEFAULT '',
            pubDate         NUMERIC(14,0) NOT NULL DEFAULT 0,
            content         TEXT,
            link            VARCHAR(254),
            category        VARCHAR(254)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['NewsCache'] = []
        commit = True
    db.createIndex('NewsCache', 'NewsCachePubDateIdx', 'pubDate')

    # newsCacheInfo
    if 'NewsCacheInfo' not in db.tables:
        # create table
        cu.execute("""
        CREATE TABLE NewsCacheInfo (
            age             INTEGER NOT NULL,
            feedLink        VARCHAR(254) NOT NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['NewsCacheInfo'] = []
        commit = True

    if commit:
        db.commit()
        db.loadSchema()

def _createRMakeBuilds(db):
    cu = db.cursor()
    commit = False

    # rMakeBuild
    if 'rMakeBuild' not in db.tables:
        cu.execute("""
        CREATE TABLE rMakeBuild(
            rMakeBuildId    %(PRIMARYKEY)s,
            userId          INTEGER NOT NULL,
            title           VARCHAR(128),
            UUID            CHAR(32),
            jobId           INTEGER,
            status          INTEGER NOT NULL DEFAULT 0,
            statusMessage   TEXT,
            CONSTRAINT rMakeBuilds_userId_fk
                FOREIGN KEY (userId) REFERENCES Users(userId)
                ON DELETE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['rMakeBuild'] = []
        commit = True

    # rMakeBuildItems
    if 'rMakeBuildItems' not in db.tables:
        cu.execute("""
        CREATE TABLE rMakeBuildItems(
            rMakeBuildItemId    %(PRIMARYKEY)s,
            rMakeBuildId        INTEGER,
            troveName           VARCHAR(767),
            troveLabel          VARCHAR(767),
            status              INTEGER NOT NULL DEFAULT 0,
            statusMessage       TEXT,
            CONSTRAINT rMakeBuildItems_rMakeBuildId_fk
                FOREIGN KEY (rMakeBuildId) REFERENCES rMakeBuild(rMakeBuildId)
                ON DELETE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['rMakeBuildItems'] = []
        commit = True

    if commit:
        db.commit()
        db.loadSchema()


def _createMirrorInfo(db):
    cu = db.cursor()
    commit = False

    # inboundMirrors
    if 'InboundMirrors' not in db.tables:
        cu.execute("""CREATE TABLE InboundMirrors (
            inboundMirrorId %(PRIMARYKEY)s,
            targetProjectId INT NOT NULL,
            sourceLabels    VARCHAR(767) NOT NULL,
            sourceUrl       VARCHAR(767) NOT NULL,
            sourceUsername  VARCHAR(254),
            sourcePassword  VARCHAR(254),
            CONSTRAINT InboundMirrors_targetProjectId_fk
                FOREIGN KEY (targetProjectId) REFERENCES Projects(projectId)
                ON DELETE CASCADE ON UPDATE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['InboundMirrors'] = []
        commit = True

    # outboundMirrors
    if 'OutboundMirrors' not in db.tables:
        cu.execute("""CREATE TABLE OutboundMirrors (
        outboundMirrorId %(PRIMARYKEY)s,
        sourceProjectId  INT NOT NULL,
        targetLabels     VARCHAR(767) NOT NULL,
        targetUrl        VARCHAR(767) NOT NULL,
        targetUsername   VARCHAR(254),
        targetPassword   VARCHAR(254),
        allLabels        INT NOT NULL DEFAULT 0,
        recurse          INT NOT NULL DEFAULT 0,
        matchStrings     VARCHAR(767) NOT NULL DEFAULT '',
        CONSTRAINT OutboundMirrors_sourceProjectId_fk
            FOREIGN KEY (sourceProjectId) REFERENCES Projects(projectId)
            ON DELETE CASCADE ON UPDATE CASCADE
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['OutboundMirrors'] = []
        commit = True

    if commit:
        db.commit()
        db.loadSchema()


def _createRepNameMap(db):
    cu = db.cursor()
    commit = False

    # repNameMap
    if 'RepNameMap' not in db.tables:
        cu.execute("""
        CREATE TABLE RepNameMap (
            fromName        VARCHAR(254) NOT NULL,
            toName          VARCHAR(254) NOT NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['RepNameMap'] = []
        commit = True

    if commit:
        db.commit()
        db.loadSchema()

def _createApplianceSpotlight(db):
    cu = db.cursor()
    commit = False

    # applianceSpotlight
    if 'ApplianceSpotlight' not in db.tables:
        cu.execute("""
        CREATE TABLE ApplianceSpotlight (
            appSpotlightId  %(PRIMARYKEY)s,
            title           VARCHAR(254) NOT NULL,
            text            VARCHAR(254) NOT NULL,
            link            VARCHAR(254) NOT NULL,
            logo            VARCHAR(254) NOT NULL,
            showArchive     INTEGER NOT NULL DEFAULT 0,
            startDate       NUMERIC(14,0) NOT NULL DEFAULT 0,
            endDate         NUMERIC(14,0) NOT NULL DEFAULT 0
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['ApplianceSpotlight'] = []
        commit = True

    # frontPageSelections
    if 'FrontPageSelections' not in db.tables:
        cu.execute("""
        CREATE TABLE FrontPageSelections (
            frontPageSelId  %(PRIMARYKEY)s,
            name            VARCHAR(254),
            link            VARCHAR(254),
            rank            INTEGER NOT NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['FrontPageSelections'] = []
        commit = True

    # useIt
    if 'UseIt' not in db.tables:
        cu.execute("""
        CREATE TABLE UseIt (
            useItId         %(PRIMARYKEY)s,
            name            VARCHAR(254),
            link            VARCHAR(254)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['UseIt'] = []

    if commit:
        db.commit()
        db.loadSchema()


# create the (permanent) server repository schema
def createSchema(db):
    if not hasattr(db, "tables"):
        db.loadSchema()
    _createUsers(db)
    _createLabels(db)
    _createProjects(db)
    _createBuilds(db)
    _createCommits(db)
    _createGroupTroves(db)
    _createJobs(db)
    _createPackageIndex(db)
    _createNewsCache(db)
    _createRMakeBuilds(db)
    _createMirrorInfo(db)
    _createRepNameMap(db)
    _createApplianceSpotlight(db)

##################### SCHEMA MIGRATION CODE FOLLOWS #########################

class SchemaMigration(migration.SchemaMigration):
    def message(self, msg = None):
        if msg is None:
            msg = self.msg
        if msg == "":
            msg = "Finished migration to schema version %d" % (self.Version,)
        logMe(1, msg)
        self.msg = msg


class MigrateTo_2(SchemaMigration):
    Version = 2
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_3(SchemaMigration):
    Version = 3
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_4(SchemaMigration):
    Version = 4
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_5(SchemaMigration):
    Version = 5
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_6(SchemaMigration):
    Version = 6
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_7(SchemaMigration):
    Version = 7
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_8(SchemaMigration):
    Version = 8
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_9(SchemaMigration):
    Version = 9
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_10(SchemaMigration):
    Version = 10
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_11(SchemaMigration):
    Version = 11
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_12(SchemaMigration):
    Version = 12
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_13(SchemaMigration):
    Version = 13
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_14(SchemaMigration):
    Version = 14
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_15(SchemaMigration):
    Version = 15
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_16(SchemaMigration):
    Version = 16
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_17(SchemaMigration):
    Version = 17
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_18(SchemaMigration):
    Version = 18
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_19(SchemaMigration):
    Version = 19
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_20(SchemaMigration):
    Version = 20
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_21(SchemaMigration):
    Version = 21
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_22(SchemaMigration):
    Version = 22
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_23(SchemaMigration):
    Version = 23
    def migrate(self):
        # TODO port migration code
        pass


class MigrateTo_24(SchemaMigration):
    Version = 24
    def migrate(self):
        # TODO port migration code
        pass

##################### END OF SCHEMA MIGRATION CODE  #########################

# run through the schema creation and migration (if required)
def loadSchema(db):
    global VERSION
    currentVersion = db.getVersion()

    # load the current schema object list
    db.loadSchema()

    # instantiate and call appropriate migration objects in succession.
    while currentVersion and currentVersion < VERSION:
        currentVersion = (lambda x : sys.modules[__name__].__dict__[ \
            'MigrateTo_' + str(x + 1)])(version)(db)()

    if currentVersion:
        db.loadSchema()
    # run through the schema creation to create any missing objects
    createSchema(db)

    if currentVersion > 0 and currentVersion != VERSION:
        # schema creation/conversion failed. SHOULD NOT HAPPEN!
        raise sqlerrors.SchemaVersionError("""
        Schema migration process has failed to bring the database
        schema version up to date. Please report this error at
        http://issues.rpath.com/.

        Current schema version is %s; Required schema version is %s.
        """ % (currentVersion, VERSION))
    db.loadSchema()

    if currentVersion != VERSION:
        return db.setVersion(VERSION)

    return VERSION

# testing 
#if __name__ == '__main__':
#    from conary import dbstore
#    #db = dbstore.connect('/tmp/test', 'sqlite')
#    loadSchema(db)

