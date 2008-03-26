#
# Copyright (c) 2005-2008 rPath, Inc.
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
from conary.dbstore import migration, sqlerrors, sqllib
from conary.lib.tracelog import logMe

# database schema major version
RBUILDER_DB_VERSION = sqllib.DBversion(45)

def _createTrigger(db, table, column = "changed"):
    retInsert = db.createTrigger(table, column, "INSERT")
    retUpdate = db.createTrigger(table, column, "UPDATE")
    return retInsert or retUpdate

def _createUsers(db):
    cu = db.cursor()
    commit = False

    if 'Users' not in db.tables:
        cu.execute("""
        CREATE TABLE Users (
            userId          %(PRIMARYKEY)s,
            username        CHAR(128) UNIQUE,
            fullName        CHAR(128),
            salt            %(BINARY4)s NOT NULL,
            passwd          %(BINARY254)s NOT NULL,
            email           CHAR(128),
            displayEmail    TEXT,
            timeCreated     DOUBLE,
            timeAccessed    DOUBLE,
            active          INT,
            blurb           TEXT
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['Users'] = []
        commit = True
    # XXX this index seems redundant
    db.createIndex('Users', 'UsersUsernameIdx', 'username', unique=True)
    # XXX need to check to see if we need an index on username, active
    db.createIndex('Users', 'UsersActiveIdx', 'username, active')

    if 'UserData' not in db.tables:
        cu.execute("""
        CREATE TABLE UserData (
            userId          INTEGER,
            name            CHAR(32),
            value           TEXT,
            dataType        INTEGER
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['UserData'] = []
        commit = True
    db.createIndex('UserData', 'UserDataIdx', 'userId')

    if 'UserGroups' not in db.tables:
        cu.execute("""
        CREATE TABLE UserGroups (
            userGroupId     %(PRIMARYKEY)s,
            userGroup       CHAR(128) UNIQUE
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['UserGroups'] = []
        commit = True
    db.createIndex('UserGroups', 'UserGroupsIndex', 'userGroup',
            unique = True)

    if 'UserGroupMembers' not in db.tables:
        cu.execute("""
        CREATE TABLE UserGroupMembers (
            userGroupId     INTEGER,
            userId          INTEGER
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['UserGroupMembers'] = []
        commit = True

    if 'Confirmations' not in db.tables:
        cu.execute("""
        CREATE TABLE Confirmations (
            userId          %(PRIMARYKEY)s,
            timeRequested   INT,
            confirmation    CHAR(255)
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['Confirmations'] = []
        commit = True

    if commit:
        db.commit()
        db.loadSchema()

def _createLabels(db):
    cu = db.cursor()
    commit = False

    if 'Labels' not in db.tables:
        cu.execute("""
        CREATE TABLE Labels (
            labelId         %(PRIMARYKEY)s,
            projectId       INT,
            label           VARCHAR(255),
            url             VARCHAR(255),
            authType        VARCHAR(32),
            username        VARCHAR(255),
            password        VARCHAR(255),
            entitlement     VARCHAR(254)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Labels'] = []
        commit = True
    db.createIndex('Labels', 'LabelsPackageIdx', 'projectId')

    if commit:
        db.commit()
        db.loadSchema()

def _createProjects(db):
    cu = db.cursor()
    commit = False

    if 'Projects' not in db.tables:
        cu.execute("""
        CREATE TABLE Projects (
            projectId       %(PRIMARYKEY)s,
            creatorId       INT,
            name            varchar(128) UNIQUE,
            hostname        varchar(128) UNIQUE,
            shortname       varchar(128),
            domainname      varchar(128) DEFAULT '' NOT NULL,
            projecturl      varchar(128) DEFAULT '' NOT NULL,
            description     text,
            disabled        INT DEFAULT 0,
            hidden          INT DEFAULT 0,
            external        INT DEFAULT 0,
            isAppliance     INT,
            timeCreated     INT,
            timeModified    INT DEFAULT 0,
            commitEmail     varchar(128) DEFAULT '',
            prodtype        varchar(128) DEFAULT '',
            version         varchar(128) DEFAULT '',
            backupExternal  INT DEFAULT 0
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Projects'] = []
        commit = True
    db.createIndex('Projects', 'ProjectsHostnameIdx', 'hostname')
    db.createIndex('Projects', 'ProjectsShortnameIdx', 'shortname')
    db.createIndex('Projects', 'ProjectsDisabledIdx', 'disabled')
    db.createIndex('Projects', 'ProjectsHiddenIdx', 'hidden')

    if 'ProjectUsers' not in db.tables:
        cu.execute("""
        CREATE TABLE ProjectUsers (
            projectId       INT,
            userId          INT,
            level           INT
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['ProjectUsers'] = []
        commit = True
    db.createIndex('ProjectUsers', 'ProjectUsersIdx', 'projectId, userId',
            unique = True)
    db.createIndex('ProjectUsers', 'ProjectUsersProjectIdx', 'projectId')
    db.createIndex('ProjectUsers', 'ProjectUsersUserIdx', 'userId')

    if 'MembershipRequests' not in db.tables:
        cu.execute("""
        CREATE TABLE MembershipRequests (
            projectId       INTEGER,
            userId          INTEGER,
            comments        TEXT,
            PRIMARY KEY(projectId, userId)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['MembershipRequests'] = []
        commit = True

    if 'ReposDatabases' not in db.tables:
        cu.execute("""
        CREATE TABLE ReposDatabases (
            databaseId      %(PRIMARYKEY)s,
            driver          VARCHAR(64),
            path            VARCHAR(255)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['ReposDatabases'] = []
        commit = True

    if 'ReposDatabases' not in db.tables:
        cu.execute("""
        CREATE TABLE ReposDatabases (
            databaseId      %(PRIMARYKEY)s,
            driver          VARCHAR(64),
            path            VARCHAR(255)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['ReposDatabases'] = []
        commit = True

    if 'ProjectDatabase' not in db.tables:
        cu.execute("""
        CREATE TABLE ProjectDatabase (
            projectId       INT NOT NULL,
            databaseId      INT NOT NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['ProjectDatabase'] = []
        commit = True

    if 'CommunityIds' not in db.tables:
        cu.execute("""
        CREATE TABLE CommunityIds (
            projectId           INTEGER,
            communityType       INTEGER,
            communityId         VARCHAR(255)
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['CommunityIds'] = []
        commit = True

    if commit:
        db.commit()
        db.loadSchema()

def _createBuilds(db):
    cu = db.cursor()
    commit = False

    if 'PublishedReleases' not in db.tables:
        cu.execute("""
        CREATE TABLE PublishedReleases (
            pubReleaseId        %(PRIMARYKEY)s,
            projectId           INTEGER,
            name                VARCHAR(255),
            version             VARCHAR(32),
            description         TEXT,
            timeCreated         DOUBLE,
            createdBy           INTEGER,
            timeUpdated         DOUBLE,
            updatedBy           INTEGER,
            timePublished       DOUBLE,
            publishedBy         INTEGER
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['PublishedReleases'] = []
        commit = True
    db.createIndex('PublishedReleases', 'PubReleasesProjectIdIdx',
            'projectId')

    if 'Builds' not in db.tables:
        cu.execute("""
        CREATE TABLE Builds (
            buildId              %(PRIMARYKEY)s,
            projectId            INTEGER NOT NULL,
            pubReleaseId         INTEGER,
            buildType            INTEGER,
            name                 VARCHAR(255),
            description          TEXT,
            troveName            VARCHAR(128),
            troveVersion         VARCHAR(255),
            troveFlavor          VARCHAR(4096),
            troveLastChanged     INTEGER,
            timeCreated          DOUBLE,
            createdBy            INTEGER,
            timeUpdated          DOUBLE,
            updatedBy            INTEGER,
            deleted              INTEGER DEFAULT '0',
            buildCount           INTEGER
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Builds'] = []
        commit = True

    db.createIndex('Builds', 'BuildProjectIdIdx', 'projectId')
    db.createIndex('Builds', 'BuildPubReleaseIdIdx', 'pubReleaseId')

    if 'BuildsView' not in db.views:
        cu.execute("""
        CREATE VIEW BuildsView AS
            SELECT * FROM Builds WHERE deleted = 0
        """)
        commit = True

    if 'BuildData' not in db.tables:
        cu.execute("""
        CREATE TABLE BuildData (
            buildId         INTEGER,
            name            CHAR(32),
            value           TEXT,
            dataType        INTEGER
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['BuildData'] = []
        commit = True
    db.createIndex('BuildData', 'BuildDataIdx', 'buildId, name',
        unique = True)

    # Nota Bummer: the filename column is deprecated, so don't use it.
    # We need to get rid of it once we adopt a migration scheme that 
    # doesn't produce different results from InitialCreation vs. Migration.
    if 'BuildFiles' not in db.tables:
        cu.execute("""
        CREATE TABLE BuildFiles (
            fileId       %(PRIMARYKEY)s,
            buildId      INT,
            idx          INT,
            filename     VARCHAR(255),
            title        CHAR(255) DEFAULT '',
            size         BIGINT,
            sha1         CHAR(40)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['BuildFiles'] = []
        commit = True

    if 'FilesUrls' not in db.tables:
        cu.execute("""
        CREATE TABLE FilesUrls (
            urlId       %(PRIMARYKEY)s,
            urlType     SMALLINT,
            url         VARCHAR(255)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['FilesUrls'] = []
        commit = True

    if 'BuildFilesUrlsMap' not in db.tables:
        cu.execute("""
        CREATE TABLE BuildFilesUrlsMap (
            fileId  INT,
            urlId   INT,
            CONSTRAINT bfum_f_fk FOREIGN KEY(fileId)
                REFERENCES BuildFiles (fileId) ON DELETE CASCADE,
            CONSTRAINT bfum_u_fk FOREIGN KEY(urlId)
                REFERENCES FilesUrls(urlId) ON DELETE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['BuildFilesUrlsMap'] = []
        commit = True
    db.createIndex("BuildFilesUrlsMap", "BuildFilesUrlsMap_f_u_idx",
                   "fileId, urlId", unique = True)

    if 'UrlDownloads' not in db.tables:
        cu.execute("""
        CREATE TABLE UrlDownloads (
            urlId               INTEGER NOT NULL,
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

    if 'Commits' not in db.tables:
        cu.execute("""
        CREATE TABLE Commits (
            projectId       INT,
            timestamp       INT,
            troveName       CHAR(255),
            version         TEXT,
            userId          INT
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Commits'] = []
        commit = True
    db.createIndex('Commits', 'CommitsProjectIdx', 'projectId')

    if commit:
        db.commit()
        db.loadSchema()

def _createGroupTroves(db):
    cu = db.cursor()
    commit = False

    if 'GroupTroves' not in db.tables:
        cu.execute("""
        CREATE TABLE GroupTroves(
            groupTroveId    %(PRIMARYKEY)s,
            projectId       INT,
            creatorId       INT,
            recipeName      CHAR(200),
            upstreamVersion CHAR(128),
            description     TEXT,
            timeCreated     INT,
            timeModified    INT,
            autoResolve     INT,
            cookCount       INT
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['GroupTroves'] = []
        commit = True
    db.createIndex('GroupTroves', 'GroupTrovesProjectIdx', 'projectId')
    db.createIndex('GroupTroves', 'GroupTrovesUserIdx', 'creatorId')

    if 'GroupTroveItems' not in db.tables:
        cu.execute("""
        CREATE TABLE GroupTroveItems(
            groupTroveItemId    %(PRIMARYKEY)s,
            groupTroveId        INT,
            creatorId           INT,
            trvName             CHAR(128),
            trvVersion          TEXT,
            trvFlavor           TEXT,
            subGroup            CHAR(128),
            versionLock         INT,
            useLock             INT,
            instSetLock         INT
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['GroupTroveItems'] = []
        commit = True
    db.createIndex('GroupTroveItems', 'GroupTroveItemsUserIdx', 'creatorId')

    if 'ConaryComponents' not in db.tables:
        cu.execute("""
        CREATE TABLE ConaryComponents(
             componentId    %(PRIMARYKEY)s,
             component      CHAR(128)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['ConaryComponents'] = []
        commit = True
    db.createIndex('ConaryComponents', 'ConaryComponentsIdx',
            'component', unique = True)

    if 'GroupTroveRemovedComponents' not in db.tables:
        cu.execute("""
        CREATE TABLE GroupTroveRemovedComponents(
             groupTroveId   INT,
             componentId    INT
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['GroupTroveRemovedComponents'] = []
        commit = True
    db.createIndex('GroupTroveRemovedComponents',
            'GroupTroveRemovedComponentIdx', 'groupTroveId, componentId',
            unique = True)

    if commit:
        db.commit()
        db.loadSchema()

def _createJobs(db):
    cu = db.cursor()
    commit = False

    if 'Jobs' not in db.tables:
        cu.execute("""
        CREATE TABLE Jobs (
            jobId           %(PRIMARYKEY)s,
            buildId         INT,
            groupTroveId    INT,
            owner           BIGINT,
            userId          INT,
            status          INT,
            statusMessage   TEXT,
            timeSubmitted   DOUBLE,
            timeStarted     DOUBLE,
            timeFinished    DOUBLE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Jobs'] = []
        commit = True
    db.createIndex('Jobs', 'JobsBuildIdx', 'buildId')
    db.createIndex('Jobs', 'JobsGroupTroveIdx', 'groupTroveId')
    db.createIndex('Jobs', 'JobsUserIdx', 'userId')

    if 'JobData' not in db.tables:
        cu.execute("""
        CREATE TABLE JobData (
            jobId           INTEGER,
            name            CHAR(32),
            value           TEXT,
            valueType       INTEGER
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['JobData'] = []
        commit = True
    db.createIndex('JobData', 'JobDataIdx', 'jobId, name', unique = True)

    if commit:
        db.commit()
        db.loadSchema()

def _createPackageIndex(db):
    cu = db.cursor()
    commit = False

    if 'PackageIndex' not in db.tables:
        cu.execute("""
        CREATE TABLE PackageIndex (
            pkgId       %(PRIMARYKEY)s,
            projectId   INT,
            name        CHAR(255),
            version     CHAR(255),
            serverName  VARCHAR(254) NOT NULL,
            branchName  VARCHAR(254) NOT NULL,
            isSource    INT DEFAULT '0'
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['PackageIndex'] = []
        commit = True
    db.createIndex("PackageIndex", "PackageIndexNameIdx", "name, version")
    db.createIndex("PackageIndex", "PackageIndexProjectIdx", "projectId")
    db.createIndex("PackageIndex", "PackageIndexServerBranchName", "serverName, branchName")

    if 'PackageIndexMark' not in db.tables:
        cu.execute("""
        CREATE TABLE PackageIndexMark (
            mark            INTEGER NOT NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['PackageIndexMark'] = []
        cu.execute("INSERT INTO PackageIndexMark VALUES(0)")
        commit = True

    if commit:
        db.commit()
        db.loadSchema()

def _createNewsCache(db):
    cu = db.cursor()
    commit = False

    if 'NewsCache' not in db.tables:
        cu.execute("""
        CREATE TABLE NewsCache (
            itemId          %(PRIMARYKEY)s,
            title           CHAR(255),
            pubDate         INT,
            content         TEXT,
            link            CHAR(255),
            category        CHAR(255)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['NewsCache'] = []
        commit = True

    if 'NewsCacheInfo' not in db.tables:
        cu.execute("""
        CREATE TABLE NewsCacheInfo (
            age             INT,
            feedLink        CHAR(255)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['NewsCacheInfo'] = []
        commit = True

    if commit:
        db.commit()
        db.loadSchema()

def _createMirrorInfo(db):
    cu = db.cursor()
    commit = False

    if 'InboundMirrors' not in db.tables:
        cu.execute("""CREATE TABLE InboundMirrors (
            inboundMirrorId %(PRIMARYKEY)s,
            targetProjectId INT NOT NULL,
            sourceLabels    VARCHAR(767) NOT NULL,
            sourceUrl       VARCHAR(767) NOT NULL,
            sourceAuthType  VARCHAR(32) NOT NULL,
            sourceUsername  VARCHAR(254),
            sourcePassword  VARCHAR(254),
            sourceEntitlement   VARCHAR(254),
            mirrorOrder     INT DEFAULT 0,
            allLabels       INT DEFAULT 0,
            CONSTRAINT InboundMirrors_targetProjectId_fk
                FOREIGN KEY (targetProjectId) REFERENCES Projects(projectId)
                ON DELETE CASCADE ON UPDATE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['InboundMirrors'] = []
        commit = True
    db.createIndex('InboundMirrors', 'InboundMirrorsProjectIdIdx',
            'targetProjectId')

    if 'UpdateServices' not in db.tables:
        cu.execute("""
        CREATE TABLE UpdateServices (
            updateServiceId         %(PRIMARYKEY)s,
            hostname                VARCHAR(767) NOT NULL,
            description             TEXT,
            mirrorUser              VARCHAR(254) NOT NULL,
            mirrorPassword          VARCHAR(254) NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['UpdateServices'] = []
        commit = True
    db.createIndex('UpdateServices', 'UpdateServiceHostnameIdx',
            'hostname', unique = True)

    if 'OutboundMirrors' not in db.tables:
        cu.execute("""CREATE TABLE OutboundMirrors (
            outboundMirrorId %(PRIMARYKEY)s,
            sourceProjectId  INT NOT NULL,
            targetLabels     VARCHAR(767) NOT NULL,
            allLabels        INT NOT NULL DEFAULT 0,
            recurse          INT NOT NULL DEFAULT 0,
            matchStrings     VARCHAR(767) NOT NULL DEFAULT '',
            mirrorOrder      INT DEFAULT 0,
            fullSync         INT NOT NULL DEFAULT 0,
            CONSTRAINT OutboundMirrors_sourceProjectId_fk
                FOREIGN KEY (sourceProjectId) REFERENCES Projects(projectId)
                ON DELETE CASCADE ON UPDATE CASCADE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['OutboundMirrors'] = []
        commit = True
    db.createIndex('OutboundMirrors', 'OutboundMirrorsProjectIdIdx',
            'sourceProjectId')

    if 'OutboundMirrorsUpdateServices' not in db.tables:
        cu.execute("""
        CREATE TABLE OutboundMirrorsUpdateServices (
            outboundMirrorId        INT NOT NULL,
            updateServiceId         INT NOT NULL,
            CONSTRAINT omt_omi_fk
                FOREIGN KEY (outboundMirrorId)
                    REFERENCES OutboundMirrors(outboundMirrorId)
                ON DELETE CASCADE,
            CONSTRAINT omt_usi_fk
                FOREIGN KEY (updateServiceId)
                    REFERENCES UpdateServices(updateServiceId)
                ON DELETE CASCADE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['OutboundMirrorsUpdateServices'] = []
        commit = True
    db.createIndex('OutboundMirrorsUpdateServices', 'omt_omi_usi_uq',
            'outboundMirrorId, updateServiceId', unique = True)

    if commit:
        db.commit()
        db.loadSchema()

def _createRepNameMap(db):
    cu = db.cursor()
    commit = False

    if 'RepNameMap' not in db.tables:
        cu.execute("""
        CREATE TABLE RepNameMap (
            fromName        VARCHAR(254),
            toName          VARCHAR(254),
            PRIMARY KEY(fromName, toName)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['RepNameMap'] = []
        commit = True
    db.createIndex('RepNameMap', 'RepNameMap_fromName_idx', 'fromName')

    if commit:
        db.commit()
        db.loadSchema()

def _createApplianceSpotlight(db):
    cu = db.cursor()
    commit = False

    if 'ApplianceSpotlight' not in db.tables:
        cu.execute("""
        CREATE TABLE ApplianceSpotlight (
            itemId          %(PRIMARYKEY)s,
            title           CHAR(255),
            text            CHAR(255),
            link            CHAR(255),
            logo            CHAR(255),
            showArchive     INT,
            startDate       INT,
            endDate         INT
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['ApplianceSpotlight'] = []
        commit = True

    if 'FrontPageSelections' not in db.tables:
        cu.execute("""
        CREATE TABLE FrontPageSelections (
            itemId          %(PRIMARYKEY)s,
            name            CHAR(255),
            link            CHAR(255),
            rank            INT
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['FrontPageSelections'] = []
        commit = True

    if 'UseIt' not in db.tables:
        cu.execute("""
        CREATE TABLE UseIt (
            itemId         %(PRIMARYKEY)s,
            name            CHAR(255),
            link            CHAR(255)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['UseIt'] = []
        commit = True

    if commit:
        db.commit()
        db.loadSchema()

def _createFrontPageStats(db):
    cu = db.cursor()
    commit = False

    if 'LatestCommit' not in db.tables:
        cu.execute("""
        CREATE TABLE LatestCommit (
            projectId   INTEGER NOT NULL,
            commitTime  INTEGER NOT NULL,
            CONSTRAINT LatestCommit_projectId_fk
                FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                    ON DELETE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['LatestCommit'] = []
        commit = True
    db.createIndex('LatestCommit', 'LatestCommitTimestamp',
            'projectId, commitTime')

    if 'PopularProjects' not in db.tables:
        cu.execute("""
        CREATE TABLE PopularProjects (
            projectId   INTEGER NOT NULL,
            rank        INTEGER NOT NULL,
            CONSTRAINT PopularProjects_projectId_fk
                FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                    ON DELETE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['PopularProjects'] = []
        commit = True

    if 'TopProjects' not in db.tables:
        cu.execute("""
        CREATE TABLE TopProjects (
            projectId   INTEGER NOT NULL,
            rank        INTEGER NOT NULL,
            CONSTRAINT TopProjects_projectId_fk
                FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                    ON DELETE CASCADE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['TopProjects'] = []
        commit = True

    if commit:
        db.commit()
        db.loadSchema()

def _createEC2Data(db):
    cu = db.cursor()
    commit = False

    if 'BlessedAMIs' not in db.tables:
        cu.execute("""
        CREATE TABLE BlessedAMIs (
            blessedAMIId        %(PRIMARYKEY)s,
            ec2AMIId            CHAR(12) NOT NULL,
            buildId             INTEGER,
            shortDescription    VARCHAR(128),
            helptext            TEXT,
            instanceTTL         INTEGER NOT NULL,
            mayExtendTTLBy      INTEGER,
            isAvailable         INTEGER NOT NULL DEFAULT 1,
            userDataTemplate    TEXT,
            CONSTRAINT ba_fk_b FOREIGN KEY (buildId)
                REFERENCES Builds(buildId) ON DELETE SET NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['BlessedAMIs'] = []
        commit = True
    db.createIndex('BlessedAMIs', 'BlessedAMIEc2AMIIdIdx', 'ec2AMIId')

    if 'LaunchedAMIs' not in db.tables:
        cu.execute("""
        CREATE Table LaunchedAMIs (
            launchedAMIId       %(PRIMARYKEY)s,
            blessedAMIId        INTEGER NOT NULL,
            launchedFromIP      CHAR(15) NOT NULL,
            ec2InstanceId       CHAR(10) NOT NULL,
            raaPassword         CHAR(8) NOT NULL,
            launchedAt          NUMERIC(14,0) NOT NULL,
            expiresAfter        NUMERIC(14,0) NOT NULL,
            isActive            INTEGER NOT NULL DEFAULT 1,
            userData            TEXT,
            CONSTRAINT la_bai_fk FOREIGN KEY (blessedAMIId)
                REFERENCES BlessedAMIs(blessedAMIId) ON DELETE RESTRICT
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['LaunchedAMIs'] = []
        commit = True
    db.createIndex('LaunchedAMIs', 'LaunchedAMIsExpiresActive',
            'isActive,expiresAfter')
    db.createIndex('LaunchedAMIs', 'LaunchedAMIsIPsActive',
            'isActive,launchedFromIP')

    if commit:
        db.commit()
        db.loadSchema()

def _createSessions(db):
    cu = db.cursor()
    commit = False

    if 'Sessions' not in db.tables:
        cu.execute("""
        CREATE TABLE Sessions (
            sessIdx     %(PRIMARYKEY)s,
            sid         CHAR(64),
            data        TEXT
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Sessions'] = []
        commit = True
    db.createIndex('Sessions', 'sessionSidIdx', 'sid')

    if commit:
        db.commit()
        db.loadSchema

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
    _createMirrorInfo(db)
    _createRepNameMap(db)
    _createApplianceSpotlight(db)
    _createFrontPageStats(db)
    _createEC2Data(db)
    _createSessions(db)

#############################################################################
# The following code was adapted from Conary's Database Migration schema
# bits (see conary/server/{migrate,schema}.py for updates).

# this should only check for the proper schema version. This function
# is called usually from the multithreaded setup, so schema operations
# should be avoided here

def checkVersion(db):
    global RBUILDER_DB_VERSION
    version = db.getVersion()
    logMe(2, "current =", version, "required =", RBUILDER_DB_VERSION)

    # test for no version
    if version == 0:
        # TODO: Better message
        raise sqlerrors.SchemaVersionError("""
        Your database schema is not initalized or it is too old.  Please
        run the standalone server with the --migrate argument to
        upgrade/initialize the database schema for the Conary Repository.

        Current schema version is %s; Required schema version is %s.
        """ % (version, RBUILDER_DB_VERSION), version)

    # the major versions must match
    if version.major != RBUILDER_DB_VERSION.major:
        # XXX better message
        raise sqlerrors.SchemaVersionError("""
        This code schema version does not match the Conary repository
        database schema that you are running.

        Current schema version is %s; Required schema version is %s.
        """ % (version, RBUILDER_DB_VERSION), version)
    # the minor numbers are considered compatible up and down across a major
    return version

# run through the schema creation and migration (if required)
def loadSchema(db, cfg=None, should_migrate=False):
    global RBUILDER_DB_VERSION
    try:
        version =  checkVersion(db)
    except sqlerrors.SchemaVersionError, e:
        version = e.args[0]
    logMe(1, "current =", version, "required =", RBUILDER_DB_VERSION)
    # load the current schema object list
    db.loadSchema()

    # avoid a recursive import by importing just what we need
    from mint import migrate

    # expedite the initial repo creation
    if version == 0:
        createSchema(db)
        db.loadSchema()
        setVer = migrate.majorMinor(RBUILDER_DB_VERSION)
        return db.setVersion(setVer)
    # test if  the repo schema is newer than what we understand
    # (by major schema number)
    if version.major > RBUILDER_DB_VERSION.major:
        raise sqlerrors.SchemaVersionError("""
        The rBuilder database schema version is newer and incompatible with
        this code base. You need to update rBuilder to a version
        that understands schema %s""" % version, version)
    # now we need to perform a schema migration
    if version.major < RBUILDER_DB_VERSION.major and not should_migrate:
        raise sqlerrors.SchemaVersionError("""
        The rBuilder database schema needs to have a major schema update
        performed.  Please run rbuilder-database with the --migrate option to
        perform this upgrade.
        """, version, RBUILDER_DB_VERSION)
    # now the version.major is smaller than RBUILDER_DB_VERSION.major - but is it too small?
    # we only support migrations from schema 37 on
    if version < 37:
        raise sqlerrors.SchemaVersionError("""
        It appears that this schema is from a version of rBuilder older
        than version 3.1.4. Schema migrations from this database schema
        version are longer supported. Please contact rPath for help 
        converting the rBuilder database to a supported version.""", version)
    # compatible schema versions have the same major
    if version.major == RBUILDER_DB_VERSION.major and not should_migrate:
        return version
    # if we reach here, a schema migration is needed/requested
    version = migrate.migrateSchema(db, cfg)
    db.loadSchema()
    # run through the schema creation to create any missing objects
    logMe(2, "checking for/initializing missing schema elements...")
    createSchema(db)
    if version > 0 and version.major != RBUILDER_DB_VERSION.major:
        # schema creation/conversion failed. SHOULD NOT HAPPEN!
        raise sqlerrors.SchemaVersionError("""
        Schema migration process has failed to bring the database
        schema version up to date. Please report this error at
        http://issues.rpath.com/.

        Current schema version is %s; Required schema version is %s.
        """ % (version, RBUILDER_DB_VERSION))
    db.loadSchema()
    return RBUILDER_DB_VERSION


