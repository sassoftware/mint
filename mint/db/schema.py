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

'''
rBuilder database schema

This includes rules to create from scratch all tables and indices used
by rBuilder. For migration from previous versions, see the
L{migrate<mint.migrate>} module.
'''

from conary.dbstore import sqlerrors, sqllib
from conary.lib.tracelog import logMe

# database schema major version
RBUILDER_DB_VERSION = sqllib.DBversion(47, 1)


def _createTrigger(db, table, column = "changed"):
    retInsert = db.createTrigger(table, column, "INSERT")
    retUpdate = db.createTrigger(table, column, "UPDATE")
    return retInsert or retUpdate


def _createUsers(db):
    cu = db.cursor()
    changed = False

    if 'Users' not in db.tables:
        cu.execute("""
        CREATE TABLE Users (
            userId              %(PRIMARYKEY)s,
            username            varchar(128)    NOT NULL    UNIQUE,
            fullName            varchar(128)    NOT NULL    DEFAULT '',
            salt                %(BINARY4)s,
            passwd              varchar(254),
            email               varchar(128),
            displayEmail        text,
            timeCreated         numeric(14,3),
            timeAccessed        numeric(14,3),
            active              smallint,
            blurb               text
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['Users'] = []
        changed = True
    changed |= db.createIndex('Users', 'UsersActiveIdx', 'username, active')

    if 'UserData' not in db.tables:
        cu.execute("""
        CREATE TABLE UserData (
            userId              integer         NOT NULL
                REFERENCES Users ON DELETE CASCADE,
            name                varchar(32)     NOT NULL,
            value               text,
            dataType            integer,

            PRIMARY KEY ( userId, name )
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['UserData'] = []
        changed = True
    changed |= db.createIndex('UserData', 'UserDataIdx', 'userId')

    if 'UserGroups' not in db.tables:
        cu.execute("""
        CREATE TABLE UserGroups (
            userGroupId         %(PRIMARYKEY)s,
            userGroup           varchar(128)    NOT NULL    UNIQUE
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['UserGroups'] = []
        changed = True

    if 'UserGroupMembers' not in db.tables:
        cu.execute("""
        CREATE TABLE UserGroupMembers (
            userGroupId         integer         NOT NULL
                REFERENCES UserGroups ON DELETE CASCADE,
            userId              integer         NOT NULL
                REFERENCES Users ON DELETE CASCADE,

            PRIMARY KEY ( userGroupId, userId )
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['UserGroupMembers'] = []
        changed = True

    if 'Confirmations' not in db.tables:
        cu.execute("""
        CREATE TABLE Confirmations (
            userId              integer         NOT NULL
                REFERENCES Users ON DELETE CASCADE,
            timeRequested       integer,
            confirmation        varchar(255)
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['Confirmations'] = []
        changed = True

    return changed


def _createLabels(db):
    cu = db.cursor()
    changed = False

    if 'Labels' not in db.tables:
        cu.execute("""
        CREATE TABLE Labels (
            labelId             %(PRIMARYKEY)s,
            projectId           integer         NOT NULL
                REFERENCES Projects ON DELETE CASCADE,
            label               varchar(255)    NOT NULL,
            url                 varchar(255)    NOT NULL,
            authType            varchar(32)     NOT NULL    DEFAULT 'none',
            username            varchar(255),
            password            varchar(255),
            entitlement         varchar(254)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Labels'] = []
        changed = True
    changed |= db.createIndex('Labels', 'LabelsPackageIdx', 'projectId')

    return changed


def _createProjects(db):
    cu = db.cursor()
    changed = False

    if 'Projects' not in db.tables:
        cu.execute("""
        CREATE TABLE Projects (
            projectId           %(PRIMARYKEY)s,
            creatorId           integer
                REFERENCES Users ( userId ) ON DELETE SET NULL,
            name                varchar(128)    NOT NULL,
            hostname            varchar(63)     NOT NULL    UNIQUE,
            shortname           varchar(63)     NOT NULL    UNIQUE,
            domainname          varchar(128)    NOT NULL    DEFAULT '',
            fqdn                varchar(255)    NOT NULL,
            namespace           varchar(16),
            projecturl          varchar(128)    DEFAULT ''  NOT NULL,
            description         text,
            disabled            smallint        NOT NULL    DEFAULT 0,
            hidden              smallint        NOT NULL    DEFAULT 0,
            external            smallint        NOT NULL    DEFAULT 0,
            isAppliance         smallint        NOT NULL    DEFAULT 1,
            timeCreated         numeric(14,3),
            timeModified        numeric(14,3),
            commitEmail         varchar(128)                DEFAULT '',
            prodtype            varchar(128)                DEFAULT '',
            version             varchar(128)                DEFAULT '',
            backupExternal      smallint        NOT NULL    DEFAULT 0,
            database            varchar(128)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Projects'] = []
        changed = True
    changed |= db.createIndex('Projects', 'ProjectsHostnameIdx', 'hostname')
    changed |= db.createIndex('Projects', 'ProjectsShortnameIdx', 'shortname')
    changed |= db.createIndex('Projects', 'ProjectsDisabledIdx', 'disabled')
    changed |= db.createIndex('Projects', 'ProjectsHiddenIdx', 'hidden')

    if 'ProjectUsers' not in db.tables:
        cu.execute("""
        CREATE TABLE ProjectUsers (
            projectId           integer         NOT NULL
                REFERENCES Projects ON DELETE CASCADE,
            userId              integer         NOT NULL
                REFERENCES Users ON DELETE CASCADE,
            level               smallint        NOT NULL,

            PRIMARY KEY ( projectId, userId )
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['ProjectUsers'] = []
        changed = True
    changed |= db.createIndex('ProjectUsers',
        'ProjectUsersProjectIdx', 'projectId')
    changed |= db.createIndex('ProjectUsers', 'ProjectUsersUserIdx', 'userId')

    if 'MembershipRequests' not in db.tables:
        cu.execute("""
        CREATE TABLE MembershipRequests (
            projectId           integer         NOT NULL
                REFERENCES Projects ON DELETE CASCADE,
            userId              integer         NOT NULL
                REFERENCES Users ON DELETE CASCADE,
            comments            text,

            PRIMARY KEY ( projectId, userId )
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['MembershipRequests'] = []
        changed = True

    if 'CommunityIds' not in db.tables:
        cu.execute("""
        CREATE TABLE CommunityIds (
            projectId           integer         NOT NULL
                REFERENCES Projects ON DELETE CASCADE,
            communityType       integer,
            communityId         varchar(255)
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['CommunityIds'] = []
        changed = True

    return changed


def _createBuilds(db):
    cu = db.cursor()
    changed = False

    if 'PublishedReleases' not in db.tables:
        cu.execute("""
        CREATE TABLE PublishedReleases (
            pubReleaseId        %(PRIMARYKEY)s,
            projectId           integer         NOT NULL
                REFERENCES Projects ON DELETE CASCADE,
            name                varchar(255)    NOT NULL    DEFAULT '',
            version             varchar(32)     NOT NULL    DEFAULT '',
            description         text,
            timeCreated         numeric(14,3)   NOT NULL,
            createdBy           integer
                REFERENCES Users ( userId ) ON DELETE SET NULL,
            timeUpdated         numeric(14,3),
            updatedBy           integer
                REFERENCES Users ( userId ) ON DELETE SET NULL,
            timePublished       numeric(14,3),
            publishedBy         integer
                REFERENCES Users ( userId ) ON DELETE SET NULL,
            shouldMirror        smallint        NOT NULL    DEFAULT 0,
            timeMirrored        numeric(14,3)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['PublishedReleases'] = []
        changed = True
    changed |= db.createIndex('PublishedReleases', 'PubReleasesProjectIdIdx',
            'projectId')

    if 'Builds' not in db.tables:
        cu.execute("""
        CREATE TABLE Builds (
            buildId             %(PRIMARYKEY)s,
            projectId            integer        NOT NULL
                REFERENCES Projects ON DELETE CASCADE,
            pubReleaseId         integer
                REFERENCES PublishedReleases ON DELETE SET NULL,
            buildType            integer        NOT NULL,
            name                 varchar(255)   NOT NULL,
            description          text,
            troveName            varchar(128)   NOT NULL,
            troveVersion         varchar(255)   NOT NULL,
            troveFlavor          varchar(4096)  NOT NULL,
            troveLastChanged     numeric(14,3),
            timeCreated          numeric(14,3),
            createdBy            integer
                REFERENCES Users ( userId ) ON DELETE SET NULL,
            timeUpdated          numeric(14,3),
            updatedBy            integer
                REFERENCES Users ( userId ) ON DELETE SET NULL,
            deleted              smallint       NOT NULL    DEFAULT 0,
            buildCount           integer        NOT NULL    DEFAULT 0,
            productVersionId     integer
                REFERENCES ProductVersions ON DELETE SET NULL,
            stageName            varchar(255),
            status               integer                    DEFAULT -1,
            statusMessage        varchar(255)               DEFAULT ''
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Builds'] = []
        changed = True

    changed |= db.createIndex('Builds', 'BuildProjectIdIdx', 'projectId')
    changed |= db.createIndex('Builds', 'BuildPubReleaseIdIdx', 'pubReleaseId')

    if 'BuildsView' not in db.views:
        cu.execute("""
        CREATE VIEW BuildsView AS
            SELECT * FROM Builds WHERE deleted = 0
        """)
        changed = True

    if 'BuildData' not in db.tables:
        cu.execute("""
        CREATE TABLE BuildData (
            buildId             integer         NOT NULL
                REFERENCES Builds ON DELETE CASCADE,
            name                varchar(32)     NOT NULL,
            value               text            NOT NULL,
            dataType            smallint        NOT NULL,

            PRIMARY KEY ( buildId, name )
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['BuildData'] = []
        changed = True

    if 'BuildFiles' not in db.tables:
        cu.execute("""
        CREATE TABLE BuildFiles (
            fileId              %(PRIMARYKEY)s,
            buildId             integer         NOT NULL
                REFERENCES Builds ON DELETE CASCADE,
            idx                 smallint        NOT NULL    DEFAULT 0,
            title               varchar(255)    NOT NULL    DEFAULT '',
            size                bigint,
            sha1                char(40)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['BuildFiles'] = []
        changed = True

    if 'FilesUrls' not in db.tables:
        cu.execute("""
        CREATE TABLE FilesUrls (
            urlId               %(PRIMARYKEY)s,
            urlType             smallint        NOT NULL,
            url                 varchar(255)    NOT NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['FilesUrls'] = []
        changed = True

    if 'BuildFilesUrlsMap' not in db.tables:
        cu.execute("""
        CREATE TABLE BuildFilesUrlsMap (
            fileId              integer         NOT NULL
                REFERENCES BuildFiles ON DELETE CASCADE,
            urlId               integer         NOT NULL
                REFERENCES FilesUrls ON DELETE CASCADE,

            PRIMARY KEY ( fileId, urlId )
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['BuildFilesUrlsMap'] = []
        changed = True

    if 'UrlDownloads' not in db.tables:
        cu.execute("""
        CREATE TABLE UrlDownloads (
            urlId               integer         NOT NULL
                REFERENCES FilesUrls ON DELETE CASCADE,
            timeDownloaded      numeric(14,0)   NOT NULL    DEFAULT 0,
            ip                  varchar(64)     NOT NULL
        )""" % db.keywords)
        db.tables['UrlDownloads'] = []
        changed = True

    return changed


def _createCommits(db):
    cu = db.cursor()
    changed = False

    if 'Commits' not in db.tables:
        cu.execute("""
        CREATE TABLE Commits (
            projectId           integer         NOT NULL
                REFERENCES Projects ON DELETE CASCADE,
            timestamp           numeric(14,3),
            troveName           varchar(255),
            version             varchar(255),
            userId              integer
                REFERENCES Users ON DELETE SET NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Commits'] = []
        changed = True
    changed |= db.createIndex('Commits', 'CommitsProjectIdx', 'projectId')

    return changed


def _createJobs(db):
    cu = db.cursor()
    changed = False

    if 'Jobs' not in db.tables:
        cu.execute("""
        CREATE TABLE Jobs (
            jobId           %(PRIMARYKEY)s,
            buildId         integer,
            groupTroveId    integer,
            owner           bigint,
            userId          integer,
            status          integer,
            statusMessage   text,
            timeSubmitted   numeric(14,3),
            timeStarted     numeric(14,3),
            timeFinished    numeric(14,3)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Jobs'] = []
        changed = True
    changed |= db.createIndex('Jobs', 'JobsBuildIdx', 'buildId')
    changed |= db.createIndex('Jobs', 'JobsGroupTroveIdx', 'groupTroveId')
    changed |= db.createIndex('Jobs', 'JobsUserIdx', 'userId')

    if 'JobData' not in db.tables:
        cu.execute("""
        CREATE TABLE JobData (
            jobId           integer,
            name            varchar(32),
            value           text,
            valueType       integer
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['JobData'] = []
        changed = True
    changed |= db.createIndex('JobData', 'JobDataIdx', 'jobId, name',
        unique = True)

    return changed


def _createPackageIndex(db):
    cu = db.cursor()
    changed = False

    if 'PackageIndex' not in db.tables:
        cu.execute("""
        CREATE TABLE PackageIndex (
            pkgId               %(PRIMARYKEY)s,
            projectId           integer         NOT NULL
                REFERENCES Projects ON DELETE CASCADE,
            name                varchar(255)    NOT NULL,
            version             varchar(255)    NOT NULL,
            serverName          varchar(254)    NOT NULL,
            branchName          varchar(254)    NOT NULL,
            isSource            integer         NOT NULL    DEFAULT '0'
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['PackageIndex'] = []
        changed = True
    changed |= db.createIndex("PackageIndex", "PackageIndexNameIdx",
        "name, version")
    changed |= db.createIndex("PackageIndex", "PackageIndexProjectIdx",
        "projectId")
    changed |= db.createIndex("PackageIndex", "PackageIndexServerBranchName",
        "serverName, branchName")

    if 'PackageIndexMark' not in db.tables:
        cu.execute("""
        CREATE TABLE PackageIndexMark (
            mark                integer         NOT NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['PackageIndexMark'] = []
        cu.execute("INSERT INTO PackageIndexMark VALUES(0)")
        changed = True

    return changed


def _createNewsCache(db):
    cu = db.cursor()
    changed = False

    if 'NewsCache' not in db.tables:
        cu.execute("""
        CREATE TABLE NewsCache (
            itemId              %(PRIMARYKEY)s,
            title               varchar(255),
            pubDate             numeric(14,3),
            content             text,
            link                varchar(255),
            category            varchar(255)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['NewsCache'] = []
        changed = True

    if 'NewsCacheInfo' not in db.tables:
        cu.execute("""
        CREATE TABLE NewsCacheInfo (
            age                 numeric(14,3),
            feedLink            varchar(255)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['NewsCacheInfo'] = []
        changed = True

    return changed


def _createMirrorInfo(db):
    cu = db.cursor()
    changed = False

    if 'InboundMirrors' not in db.tables:
        cu.execute("""CREATE TABLE InboundMirrors (
            inboundMirrorId     %(PRIMARYKEY)s,
            targetProjectId     integer         NOT NULL
                REFERENCES Projects ( projectId ) ON DELETE CASCADE,
            sourceLabels        varchar(767)    NOT NULL,
            sourceUrl           varchar(767)    NOT NULL,
            sourceAuthType      varchar(32)     NOT NULL,
            sourceUsername      varchar(254),
            sourcePassword      varchar(254),
            sourceEntitlement   varchar(254),
            mirrorOrder         integer                     DEFAULT 0,
            allLabels           integer                     DEFAULT 0
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['InboundMirrors'] = []
        changed = True
    changed |= db.createIndex('InboundMirrors', 'InboundMirrorsProjectIdIdx',
            'targetProjectId')

    if 'UpdateServices' not in db.tables:
        cu.execute("""
        CREATE TABLE UpdateServices (
            updateServiceId     %(PRIMARYKEY)s,
            hostname            varchar(767)    NOT NULL    UNIQUE,
            description         text,
            mirrorUser          varchar(254)    NOT NULL,
            mirrorPassword      varchar(254)    NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['UpdateServices'] = []
        changed = True

    if 'OutboundMirrors' not in db.tables:
        cu.execute("""CREATE TABLE OutboundMirrors (
            outboundMirrorId    %(PRIMARYKEY)s,
            sourceProjectId     integer         NOT NULL
                REFERENCES Projects ( projectId ) ON DELETE CASCADE,
            targetLabels        varchar(767)    NOT NULL,
            allLabels           smallint        NOT NULL    DEFAULT 0,
            recurse             smallint        NOT NULL    DEFAULT 0,
            matchStrings        varchar(767)    NOT NULL    DEFAULT '',
            mirrorOrder         integer                     DEFAULT 0,
            fullSync            smallint        NOT NULL    DEFAULT 0,
            useReleases         integer         NOT NULL    DEFAULT 0
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['OutboundMirrors'] = []
        changed = True
    changed |= db.createIndex('OutboundMirrors', 'OutboundMirrorsProjectIdIdx',
            'sourceProjectId')

    if 'OutboundMirrorsUpdateServices' not in db.tables:
        cu.execute("""
        CREATE TABLE OutboundMirrorsUpdateServices (
            outboundMirrorId    integer         NOT NULL
                REFERENCES OutboundMirrors ON DELETE CASCADE,
            updateServiceId     integer         NOT NULL
                REFERENCES UpdateServices ON DELETE CASCADE,

            PRIMARY KEY ( outboundMirrorId, updateServiceId )
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['OutboundMirrorsUpdateServices'] = []
        changed = True

    return changed


def _createRepNameMap(db):
    cu = db.cursor()
    changed = False

    if 'RepNameMap' not in db.tables:
        cu.execute("""
        CREATE TABLE RepNameMap (
            fromName            varchar(254)    NOT NULL,
            toName              varchar(254)    NOT NULL,

            PRIMARY KEY ( fromName, toName )
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['RepNameMap'] = []
        changed = True
    changed |= db.createIndex('RepNameMap', 'RepNameMap_fromName_idx',
        'fromName')
    changed |= db.createIndex('RepNameMap', 'RepNameMap_toName_idx',
        'toName')

    return changed


def _createApplianceSpotlight(db):
    cu = db.cursor()
    changed = False

    # XXX: delete this in a future schema upgrade; leaving dormant for now
    if 'ApplianceSpotlight' not in db.tables:
        cu.execute("""
        CREATE TABLE ApplianceSpotlight (
            itemId          %(PRIMARYKEY)s,
            title           varchar(255),
            text            varchar(255),
            link            varchar(255),
            logo            varchar(255),
            showArchive     integer,
            startDate       integer,
            endDate         INT
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['ApplianceSpotlight'] = []
        changed = True

    if 'FrontPageSelections' not in db.tables:
        cu.execute("""
        CREATE TABLE FrontPageSelections (
            itemId          %(PRIMARYKEY)s,
            name            varchar(255),
            link            varchar(255),
            rank            INT
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['FrontPageSelections'] = []
        changed = True

    # XXX: delete this in a future schema upgrade; leaving dormant for now
    if 'UseIt' not in db.tables:
        cu.execute("""
        CREATE TABLE UseIt (
            itemId         %(PRIMARYKEY)s,
            name            varchar(255),
            link            varchar(255)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['UseIt'] = []
        changed = True

    return changed


def _createFrontPageStats(db):
    cu = db.cursor()
    changed = False

    if 'LatestCommit' not in db.tables:
        cu.execute("""
        CREATE TABLE LatestCommit (
            projectId           integer         NOT NULL
                REFERENCES Projects ON DELETE CASCADE,
            commitTime          numeric(14,3)   NOT NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['LatestCommit'] = []
        changed = True
    changed |= db.createIndex('LatestCommit', 'LatestCommitTimestamp',
            'projectId, commitTime')

    if 'PopularProjects' not in db.tables:
        cu.execute("""
        CREATE TABLE PopularProjects (
            projectId           integer         NOT NULL
                REFERENCES Projects ON DELETE CASCADE,
            rank                integer         NOT NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['PopularProjects'] = []
        changed = True

    if 'TopProjects' not in db.tables:
        cu.execute("""
        CREATE TABLE TopProjects (
            projectId           integer         NOT NULL
                REFERENCES Projects ON DELETE CASCADE,
            rank                integer         NOT NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['TopProjects'] = []
        changed = True

    return changed


def _createEC2Data(db):
    cu = db.cursor()
    changed = False

    if 'BlessedAMIs' not in db.tables:
        cu.execute("""
        CREATE TABLE BlessedAMIs (
            blessedAMIId        %(PRIMARYKEY)s,
            ec2AMIId            varchar(12) NOT NULL,
            buildId             integer,
            shortDescription    varchar(128),
            helptext            text,
            instanceTTL         integer NOT NULL,
            mayExtendTTLBy      integer,
            isAvailable         integer NOT NULL DEFAULT 1,
            userDataTemplate    text,
            CONSTRAINT ba_fk_b FOREIGN KEY (buildId)
                REFERENCES Builds(buildId) ON DELETE SET NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['BlessedAMIs'] = []
        changed = True
    changed |= db.createIndex('BlessedAMIs', 'BlessedAMIEc2AMIIdIdx', 'ec2AMIId')

    if 'LaunchedAMIs' not in db.tables:
        cu.execute("""
        CREATE Table LaunchedAMIs (
            launchedAMIId       %(PRIMARYKEY)s,
            blessedAMIId        integer NOT NULL,
            launchedFromIP      varchar(15) NOT NULL,
            ec2InstanceId       varchar(10) NOT NULL,
            raaPassword         varchar(8) NOT NULL,
            launchedAt          numeric(14,0) NOT NULL,
            expiresAfter        numeric(14,0) NOT NULL,
            isActive            integer NOT NULL DEFAULT 1,
            userData            text,
            CONSTRAINT la_bai_fk FOREIGN KEY (blessedAMIId)
                REFERENCES BlessedAMIs(blessedAMIId) ON DELETE RESTRICT
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['LaunchedAMIs'] = []
        changed = True
    changed |= db.createIndex('LaunchedAMIs', 'LaunchedAMIsExpiresActive',
            'isActive,expiresAfter')
    changed |= db.createIndex('LaunchedAMIs', 'LaunchedAMIsIPsActive',
            'isActive,launchedFromIP')

    return changed


def _createSessions(db):
    cu = db.cursor()
    changed = False

    if 'Sessions' not in db.tables:
        cu.execute("""
        CREATE TABLE Sessions (
            sessIdx             %(PRIMARYKEY)s,
            sid                 varchar(64)         NOT NULL    UNIQUE,
            data                text
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Sessions'] = []
        changed = True

    return changed


def _createProductVersions(db):
    cu = db.cursor()
    changed = False

    if 'ProductVersions' not in db.tables:
        cu.execute("""
            CREATE TABLE ProductVersions (
                productVersionId    %(PRIMARYKEY)s,
                projectId       integer             NOT NULL
                    REFERENCES Projects ON DELETE CASCADE,
                namespace           varchar(16)     NOT NULL,
                name                varchar(16)     NOT NULL,
                description         text,
                timeCreated         numeric(14,3)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['ProductVersions'] = []
        changed = True
    changed |= db.createIndex('ProductVersions', 'ProductVersions_uq',
            'projectId,namespace,name', unique = True)

    return changed

def _createTargets(db):
    cu = db.cursor()
    changed = False
    if 'Targets' not in db.tables:
        cu.execute("""
            CREATE TABLE Targets (
                targetId        %(PRIMARYKEY)s,
                targetType      varchar(255)        NOT NULL,
                targetName      varchar(255)        NOT NULL    UNIQUE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['Targets'] = []
        changed = True

    if 'TargetData' not in db.tables:
        cu.execute("""
            CREATE TABLE TargetData (
                targetId        integer             NOT NULL
                    REFERENCES Targets ON DELETE CASCADE,
                name            varchar(255)        NOT NULL,
                value           text,

                PRIMARY KEY ( targetId, name )
            ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['TargetData'] = []
        changed = True

    return changed

# create the (permanent) server repository schema
def createSchema(db, doCommit=True):
    if not hasattr(db, "tables"):
        db.loadSchema()

    if doCommit:
        db.transaction()

    changed = False
    changed |= _createUsers(db)
    changed |= _createProjects(db)
    changed |= _createLabels(db)
    changed |= _createProductVersions(db)
    changed |= _createBuilds(db)
    changed |= _createCommits(db)
    changed |= _createJobs(db)
    changed |= _createPackageIndex(db)
    changed |= _createNewsCache(db)
    changed |= _createMirrorInfo(db)
    changed |= _createRepNameMap(db)
    changed |= _createApplianceSpotlight(db)
    changed |= _createFrontPageStats(db)
    changed |= _createEC2Data(db)
    changed |= _createSessions(db)
    changed |= _createTargets(db)

    if doCommit:
        if changed:
            db.commit()
            db.loadSchema()
        else:
            db.rollback()

    return changed


#############################################################################
# The following code was adapted from Conary's Database Migration schema
# bits (see conary/server/{migrate,schema}.py for updates).

# this should only check for the proper schema version. This function
# is called usually from the multithreaded setup, so schema operations
# should be avoided here

def checkVersion(db):
    version = db.getVersion()
    logMe(2, "current =", version, "required =", RBUILDER_DB_VERSION)

    # test for no version
    if version == 0:
        raise sqlerrors.SchemaVersionError('Uninitialized database', version)

    # the major and minor versions must match
    if version != RBUILDER_DB_VERSION:
        raise sqlerrors.SchemaVersionError('Schema version mismatch', version)

    return version


# run through the schema creation and migration (if required)
def loadSchema(db, cfg=None, should_migrate=False):
    try:
        version =  checkVersion(db)
    except sqlerrors.SchemaVersionError, e_value:
        version = e_value.args[0]
    logMe(1, "current =", version, "required =", RBUILDER_DB_VERSION)
    # load the current schema object list
    db.loadSchema()

    # avoid a recursive import by importing just what we need
    from mint.scripts import migrate

    # expedite the initial repo creation
    if version == 0:
        createSchema(db)
        setVer = migrate.majorMinor(RBUILDER_DB_VERSION.major)
        return db.setVersion(setVer)

    # test if  the repo schema is newer than what we understand
    # (by major schema number)
    if version > RBUILDER_DB_VERSION:
        raise sqlerrors.SchemaVersionError("""
        The rBuilder database schema version is newer and incompatible with
        this code base. You need to update rBuilder to a version
        that understands schema %s""" % version, version)

    # now we need to perform a schema migration
    if version < RBUILDER_DB_VERSION and not should_migrate:
        raise sqlerrors.SchemaVersionError("""
        The rBuilder database schema needs to have a schema update
        performed.  Please run rbuilder-database with the --migrate
        option to perform this upgrade.
        """, version, RBUILDER_DB_VERSION)

    # now the version.major is smaller than RBUILDER_DB_VERSION.major
    # -- but is it too small?
    # we only support migrations from schema 37 on
    if version < 37:
        raise sqlerrors.SchemaVersionError("""
        It appears that this schema is from a version of rBuilder older
        than version 3.1.4. Schema migrations from this database schema
        version are longer supported. Please contact rPath for help 
        converting the rBuilder database to a supported version.""", version)

    # if we reach here, a schema migration is needed/requested
    version = migrate.migrateSchema(db, cfg)
    db.loadSchema()

    # run through the schema creation to create any missing objects
    logMe(2, "checking for/initializing missing schema elements...")
    createSchema(db)
    if version > 0 and version != RBUILDER_DB_VERSION:
        # schema creation/conversion failed. SHOULD NOT HAPPEN!
        raise sqlerrors.SchemaVersionError("""
        Schema migration process has failed to bring the database
        schema version up to date. Please report this error at
        http://issues.rpath.com/.

        Current schema version is %s; Required schema version is %s.
        """ % (version, RBUILDER_DB_VERSION))

    db.loadSchema()
    return RBUILDER_DB_VERSION
