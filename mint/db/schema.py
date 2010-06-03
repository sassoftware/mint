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

import logging
from conary.dbstore import sqlerrors, sqllib

log = logging.getLogger(__name__)

# database schema major version
RBUILDER_DB_VERSION = sqllib.DBversion(48, 15)


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
            timeCreated         numeric(14,3),
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
            buildType            integer,
            name                 varchar(255),
            description          text,
            troveName            varchar(128),
            troveVersion         varchar(255),
            troveFlavor          varchar(4096),
            troveLastChanged     numeric(14,3),
            timeCreated          numeric(14,3),
            createdBy            integer
                REFERENCES Users ( userId ) ON DELETE SET NULL,
            timeUpdated          numeric(14,3),
            updatedBy            integer
                REFERENCES Users ( userId ) ON DELETE SET NULL,
            buildCount           integer        NOT NULL    DEFAULT 0,
            productVersionId     integer
                REFERENCES ProductVersions ON DELETE SET NULL,
            stageName            varchar(255)               DEFAULT '',
            status               integer                    DEFAULT -1,
            statusMessage        text                       DEFAULT ''
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Builds'] = []
        changed = True

    changed |= db.createIndex('Builds', 'BuildProjectIdIdx', 'projectId')
    changed |= db.createIndex('Builds', 'BuildPubReleaseIdIdx', 'pubReleaseId')

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
    changed |= db.createIndex("PackageIndex", "PackageIndex_Project_Name_idx",
            "projectId, name")
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

    # NB: This table is dead. It is still referenced in a few places, but it
    # was such an awful and tremendously confusing idea that it has been
    # superceded by the "fqdn" column in Projects. Please delete references to
    # it when it is safe to do so.

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

def _createPlatforms(db):
    cu = db.cursor()
    changed = False

    if 'Platforms' not in db.tables:
        cu.execute("""
            CREATE TABLE Platforms (
                platformId  %(PRIMARYKEY)s,
                label       varchar(255)    NOT NULL UNIQUE,
                mode varchar(255) NOT NULL DEFAULT 'manual' check (mode in ('auto', 'manual')),
                enabled     smallint NOT NULL DEFAULT 1,
                projectId   smallint 
                    REFERENCES Projects ON DELETE SET NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['Platforms'] = []
        changed = True

    if 'PlatformsContentSourceTypes' not in db.tables:
        cu.execute("""
            CREATE TABLE PlatformsContentSourceTypes (
                platformId  integer NOT NULL
                    REFERENCES platforms ON DELETE CASCADE,
                contentSourceType  varchar(255) NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['PlatformsContentSourceTypes'] = []
        changed = True
    changed |= db.createIndex('PlatformsContentSourceTypes',
            'PlatformsContentSourceTypes_platformId_contentSourceType_uq',
            'platformId,contentSourceType', unique = True)

    if 'PlatformSources' not in db.tables:
        cu.execute("""
            CREATE TABLE PlatformSources (
                platformSourceId  %(PRIMARYKEY)s,
                name       varchar(255)    NOT NULL,
                shortName  varchar(255)    NOT NULL UNIQUE,
                defaultSource    smallint  NOT NULL DEFAULT 0,
                contentSourceType  varchar(255) NOT NULL,
                orderIndex  smallint NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['PlatformSources'] = []
        changed = True
    changed |= db.createIndex('PlatformSources',
            'PlatformSources_platformSourceId_defaultSource_uq',
            'platformSourceId,defaultSource', unique = True)
    changed |= db.createIndex('PlatformSources',
            'PlatformSources_platformSourceId_orderIndex_uq',
            'platformSourceId,orderIndex', unique = True)

    if 'PlatformSourceData' not in db.tables:
        cu.execute("""
            CREATE TABLE PlatformSourceData (
                platformSourceId    integer         NOT NULL
                    REFERENCES PlatformSources ON DELETE CASCADE,
                name                varchar(32)     NOT NULL,
                value               text            NOT NULL,
                dataType            smallint        NOT NULL,
                PRIMARY KEY ( platformSourceId, name )
            ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['PlatformSourceData'] = []
        changed = True

    if 'PlatformsPlatformSources' not in db.tables:
        cu.execute("""
            CREATE TABLE PlatformsPlatformSources (
                platformId          integer         NOT NULL
                    REFERENCES platforms ON DELETE CASCADE,
                platformSourceId    integer         NOT NULL
                    REFERENCES platformSources ON DELETE CASCADE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['PlatformsPlatformSources'] = []
        changed = True

    if 'PlatformLoadJobs' not in db.tables:
        cu.execute("""
            CREATE TABLE PlatformLoadJobs (
                jobId %(PRIMARYKEY)s,
                platformId          integer         NOT NULL
                    REFERENCES platforms ON DELETE CASCADE,
                message             varchar(255) NOT NULL,
                done                smallint NOT NULL DEFAULT 0,
                error               smallint NOT NULL DEFAULT 0
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['PlatformLoadJobs'] = []
        changed = True

    return changed

def _createCapsuleIndexerSchema(db):
    # Even though sqlalchemy is perfectly capable of creating the schema, we
    # will create it by hand instead. The main reason is that sqlite will get
    # upset if schema changes underneath an open connection.
    cu = db.cursor()
    changed = False

    tableName = 'ci_rhn_channels'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE ci_rhn_channels (
                channel_id %(PRIMARYKEY)s,
                label VARCHAR(256) NOT NULL,
                last_modified VARCHAR
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
        changed = True
    changed |= db.createIndex('ci_rhn_channels',
        'ci_rhn_channels_label_idx_uq', 'label', unique = True)

    tableName = 'ci_rhn_errata'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE ci_rhn_errata (
                errata_id %(PRIMARYKEY)s,
                advisory VARCHAR NOT NULL,
                advisory_type VARCHAR NOT NULL,
                issue_date VARCHAR NOT NULL,
                last_modified_date VARCHAR NOT NULL,
                synopsis VARCHAR NOT NULL,
                update_date VARCHAR NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
        changed = True

    tableName = 'ci_rhn_nevra'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE ci_rhn_nevra (
                nevra_id %(PRIMARYKEY)s,
                name VARCHAR NOT NULL,
                epoch INTEGER NOT NULL,
                version VARCHAR NOT NULL,
                release VARCHAR NOT NULL,
                arch VARCHAR NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
        changed = True
    changed |= db.createIndex('ci_rhn_nevra',
        'ci_rhn_nevra_n_e_v_r_a_idx_uq', 'name, epoch, version, release, arch',
        unique = True)

    tableName = 'ci_rhn_packages'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE ci_rhn_packages (
                package_id %(PRIMARYKEY)s,
                nevra_id INTEGER NOT NULL
                    REFERENCES ci_rhn_nevra ON DELETE CASCADE,
                md5sum VARCHAR,
                sha1sum VARCHAR,
                last_modified VARCHAR NOT NULL,
                path VARCHAR
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
        changed = True
    changed |= db.createIndex('ci_rhn_packages',
        'ci_rhn_packages_nevra_id_last_modified_idx_uq',
        'nevra_id, last_modified', unique = True)
    changed |= db.createIndex('ci_rhn_packages',
        'ci_rhn_packages_nevra_id_sha1sum_idx', 'nevra_id, sha1sum')

    tableName = 'ci_rhn_package_failed'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE ci_rhn_package_failed (
                package_failed_id %(PRIMARYKEY)s,
                package_id INTEGER NOT NULL
                    REFERENCES ci_rhn_packages ON DELETE CASCADE,
                failed_timestamp INTEGER NOT NULL,
                failed_msg VARCHAR NOT NULL,
                resolved VARCHAR
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
        changed = True

    tableName = 'ci_rhn_channel_package'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE ci_rhn_channel_package (
                channel_id  INTEGER NOT NULL
                    REFERENCES ci_rhn_channels ON DELETE CASCADE,
                package_id INTEGER NOT NULL
                    REFERENCES ci_rhn_packages ON DELETE CASCADE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
        changed = True
    changed |= db.createIndex('ci_rhn_channel_package',
        'ci_rhn_channel_package_cid_pid_idx_uq', 'channel_id, package_id',
        unique = True)
    changed |= db.createIndex('ci_rhn_channel_package',
        'ci_rhn_channel_package_pid_cid_idx', 'package_id, channel_id')

    tableName = 'ci_rhn_errata_channel'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE ci_rhn_errata_channel (
                errata_id INTEGER NOT NULL
                    REFERENCES ci_rhn_errata ON DELETE CASCADE,
                channel_id  INTEGER NOT NULL
                    REFERENCES ci_rhn_channels ON DELETE CASCADE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
        changed = True
    changed |= db.createIndex('ci_rhn_errata_channel',
        'ci_rhn_errata_channel_eid_cid_idx_uq', 'errata_id, channel_id',
        unique = True)
    changed |= db.createIndex('ci_rhn_errata_channel',
        'ci_rhn_errata_channel_cid_eid_idx', 'channel_id, errata_id')

    tableName = 'ci_rhn_errata_nevra_channel'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE ci_rhn_errata_nevra_channel (
                errata_id INTEGER NOT NULL
                    REFERENCES ci_rhn_errata ON DELETE CASCADE,
                nevra_id INTEGER NOT NULL
                    REFERENCES ci_rhn_nevra ON DELETE CASCADE,
                channel_id INTEGER NOT NULL
                    REFERENCES ci_rhn_channels ON DELETE CASCADE,
                PRIMARY KEY (errata_id, nevra_id, channel_id)
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
        changed = True

    return changed

def _createCapsuleIndexerYumSchema(db):
    cu = db.cursor()
    changed = False

    tableName = 'ci_yum_repositories'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE ci_yum_repositories (
                yum_repository_id %(PRIMARYKEY)s,
                label VARCHAR(256) NOT NULL,
                timestamp VARCHAR,
                checksum VARCHAR,
                checksum_type VARCHAR
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
        changed = True
    changed |= db.createIndex('ci_yum_repositories',
        'ci_yum_repositories_label_idx_uq', 'label', unique = True)

    tableName = 'ci_yum_packages'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE ci_yum_packages (
                package_id %(PRIMARYKEY)s,
                nevra_id INTEGER NOT NULL
                    REFERENCES ci_rhn_nevra ON DELETE CASCADE,
                sha1sum VARCHAR,
                checksum VARCHAR NOT NULL,
                checksum_type VARCHAR NOT NULL,
                path VARCHAR
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
        changed = True
    changed |= db.createIndex('ci_yum_packages',
        'ci_yum_packages_nevra_id_checksum_idx_uq',
        'nevra_id, checksum, checksum_type', unique = True)

    tableName = 'ci_yum_repository_package'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE ci_yum_repository_package (
                yum_repository_id INTEGER NOT NULL
                    REFERENCES ci_yum_repositories ON DELETE CASCADE,
                package_id INTEGER NOT NULL
                    REFERENCES ci_yum_packages ON DELETE CASCADE,
                location VARCHAR NOT NULL,
                PRIMARY KEY (yum_repository_id, package_id)
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
        changed = True
    return changed

def _createRepositoryLogSchema(db):
    # Repository Log scraping table and the status table for th scraper 
    cu = db.cursor()
    changed = False

    if 'systemupdate' not in db.tables:
        cu.execute("""
            CREATE TABLE systemupdate
            (
                systemupdateid %(PRIMARYKEY)s, 
                servername character varying(128) NOT NULL,
                repositoryname character varying(128) NOT NULL,
                updatetime numeric(14,3) NOT NULL,
                updateuser character varying(128) NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['systemupdate'] = []
        changed = True
    changed |= db.createIndex('systemupdate',
        'systemupdate_repo_idx', 'repositoryname')

    if 'repositorylogstatus' not in db.tables:
        cu.execute("""
            CREATE TABLE repositorylogstatus
            (
                logname varchar(128) PRIMARY KEY,
                inode integer NOT NULL,
                logoffset integer NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['repositorylogstatus'] = []
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
    changed |= _createPackageIndex(db)
    changed |= _createNewsCache(db)
    changed |= _createMirrorInfo(db)
    changed |= _createRepNameMap(db)
    changed |= _createApplianceSpotlight(db)
    changed |= _createFrontPageStats(db)
    changed |= _createEC2Data(db)
    changed |= _createSessions(db)
    changed |= _createTargets(db)
    changed |= _createPlatforms(db)
    changed |= _createCapsuleIndexerSchema(db)
    changed |= _createRepositoryLogSchema(db)
    changed |= _createCapsuleIndexerYumSchema(db)

    if doCommit:
        db.commit()
        db.loadSchema()

    return changed


#############################################################################
# The following code was adapted from Conary's Database Migration schema
# bits (see conary/server/{migrate,schema}.py for updates).

# this should only check for the proper schema version. This function
# is called usually from the multithreaded setup, so schema operations
# should be avoided here

def checkVersion(db):
    version = db.getVersion()

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
    log.debug("Current schema version is %s", version)
    log.debug("Latest schema verson is %s", RBUILDER_DB_VERSION)

    if version == RBUILDER_DB_VERSION:
        # Nothing to do
        return version

    # load the current schema object list
    db.loadSchema()

    # avoid a recursive import by importing just what we need
    from mint.scripts import migrate

    # expedite the initial repo creation
    if version == 0:
        log.info("Creating new mint database schema with version %s",
                RBUILDER_DB_VERSION)
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
    db.transaction()
    try:
        version = migrate.migrateSchema(db, cfg)
        db.loadSchema()

        # run through the schema creation to create any missing objects
        log.debug("Checking for and creating missing schema elements")
        createSchema(db, doCommit=False)
    except:
        db.rollback()
        raise
    else:
        db.commit()
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
