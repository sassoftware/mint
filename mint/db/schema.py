#
# Copyright (c) 2005-2010 rPath, Inc.
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
import datetime
from dateutil import tz
from conary.dbstore import sqlerrors, sqllib

log = logging.getLogger(__name__)

# database schema major version
RBUILDER_DB_VERSION = sqllib.DBversion(55, 3)


def _createTrigger(db, table, column = "changed"):
    retInsert = db.createTrigger(table, column, "INSERT")
    retUpdate = db.createTrigger(table, column, "UPDATE")
    return retInsert or retUpdate


def createTable(db, name, definition):
    """Helper for creating a table if it doesn't already exist.

    Pass C{None} as C{name} to force creation.
    """
    if name and name in db.tables:
        return False
    cu = db.cursor()
    cu.execute(definition % db.keywords)
    db.tables[name] = []
    return True


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
            job_uuid             uuid,
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
            statusMessage        text                       DEFAULT '',
            output_trove         text
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
                targetName      varchar(255)        NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['Targets'] = []
        db.createIndex('Targets',
            'Targets_Type_Name_Uq', 'targetType, targetName', unique = True)
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

    changed |= createTable(db, 'TargetCredentials', """
            CREATE TABLE TargetCredentials (
                targetCredentialsId     %(PRIMARYKEY)s,
                credentials             text NOT NULL UNIQUE
            ) %(TABLEOPTS)s""")

    changed |= createTable(db, 'TargetUserCredentials', """
            CREATE TABLE TargetUserCredentials (
                id              %(PRIMARYKEY)s,
                targetId        integer             NOT NULL
                    REFERENCES Targets ON DELETE CASCADE,
                userId          integer             NOT NULL
                    REFERENCES Users ON DELETE CASCADE,
                targetCredentialsId integer         NOT NULL
                    REFERENCES TargetCredentials ON DELETE CASCADE,
                UNIQUE ( targetId, userId )
            ) %(TABLEOPTS)s""")

    changed |= createTable(db, 'TargetImagesDeployed', """
            CREATE TABLE TargetImagesDeployed (
                id              %(PRIMARYKEY)s,
                targetId        integer             NOT NULL
                    REFERENCES Targets ON DELETE CASCADE,
                fileId          integer             NOT NULL
                    REFERENCES BuildFiles ON DELETE CASCADE,
                targetImageId   varchar(128)        NOT NULL
            ) %(TABLEOPTS)s""")

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
                    REFERENCES Projects ON DELETE SET NULL,
                platformName    varchar(1024) NOT NULL,
                configurable    boolean NOT NULL DEFAULT false,
                abstract        boolean NOT NULL DEFAULT false,
                isFromDisk      boolean NOT NULL DEFAULT false,
                time_refreshed  timestamp with time zone NOT NULL
                                DEFAULT current_timestamp
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

def _createInventorySchema(db, cfg):
    cu = db.cursor()
    changed = False
    
    if 'inventory_zone' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_zone" (
                "zone_id" %(PRIMARYKEY)s,
                "name" varchar(8092) NOT NULL UNIQUE,
                "description" varchar(8092),
                "created_date" timestamp with time zone NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_zone'] = []
        changed = True

    if 'inventory_system_state' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_system_state" (
                "system_state_id" %(PRIMARYKEY)s,
                "name" varchar(8092) NOT NULL UNIQUE,
                "description" varchar(8092) NOT NULL,
                "created_date" timestamp with time zone NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_system_state'] = []
        changed = True
        changed |= _addSystemStates(db, cfg)
        
    if 'inventory_management_interface' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_management_interface" (
                "management_interface_id" %(PRIMARYKEY)s,
                "name" varchar(8092) NOT NULL UNIQUE,
                "description" varchar(8092) NOT NULL,
                "created_date" timestamp with time zone NOT NULL,
                "port" integer NOT NULL,
                "credentials_descriptor" text NOT NULL,
                "credentials_readonly" bool
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_management_interface'] = []
        changed |= _addManagementInterfaces(db)
        changed = True
        
    if 'inventory_system_type' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_system_type" (
                "system_type_id" %(PRIMARYKEY)s,
                "name" varchar(8092) NOT NULL UNIQUE,
                "description" varchar(8092) NOT NULL,
                "created_date" timestamp with time zone NOT NULL,
                "infrastructure" bool NOT NULL,
                "creation_descriptor" text NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_system_type'] = []
        changed |= _addSystemTypes(db)
        changed = True

    if 'inventory_stage' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_stage" (
                "stage_id" %(PRIMARYKEY)s,
                "name" varchar(256) NOT NULL,
                "label" text NOT NULL,
                "major_version_id" integer
                    REFERENCES ProductVersions (productVersionId)
                    ON DELETE SET NULL
            )""" % db.keywords)
        db.tables['inventory_stage'] = []
        changed = True

    if 'inventory_system' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_system" (
                "system_id" %(PRIMARYKEY)s,
                "name" varchar(8092) NOT NULL,
                "description" varchar(8092),
                "created_date" timestamp with time zone NOT NULL,
                "hostname" varchar(8092),
                "launch_date" timestamp with time zone,
                "target_id" integer REFERENCES "targets" ("targetid")
                    ON DELETE SET NULL,
                "target_system_id" varchar(255),
                "target_system_name" varchar(255),
                "target_system_description" varchar(1024),
                "target_system_state" varchar(64),
                "registration_date" timestamp with time zone,
                "generated_uuid" varchar(64),
                "local_uuid" varchar(64),
                "ssl_client_certificate" varchar(8092),
                "ssl_client_key" varchar(8092),
                "ssl_server_certificate" varchar(8092),
                "agent_port" integer,
                "state_change_date" timestamp with time zone,
                "launching_user_id" integer REFERENCES "users" ("userid"),
                "current_state_id" integer NOT NULL
                    REFERENCES "inventory_system_state" ("system_state_id"),
                "managing_zone_id" integer NOT NULL
                    REFERENCES "inventory_zone" ("zone_id"),
                "management_interface_id" integer 
                    REFERENCES "inventory_management_interface" ("management_interface_id"),
                "system_type_id" integer 
                    REFERENCES "inventory_system_type" ("system_type_id"),
                "credentials" text,
                "configuration" text,
                "stage_id" integer 
                    REFERENCES "inventory_stage" ("stage_id"),
                "major_version_id" integer 
                    REFERENCES ProductVersions (productVersionId),
                "appliance_id" integer 
                    REFERENCES Projects (projectId)
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_system'] = []
        changed = True
        changed |= db.createIndex("inventory_system",
            "inventory_system_target_id_idx", "target_id")
        
    if 'inventory_zone_management_node' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_zone_management_node" (
                "system_ptr_id" integer NOT NULL PRIMARY KEY 
                    REFERENCES "inventory_system" ("system_id")
                    ON DELETE CASCADE,
                "local" bool,
                "zone_id" integer NOT NULL REFERENCES "inventory_zone" ("zone_id"),
                "node_jid" varchar(64)
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_zone_management_node'] = []
        changed = True

    if 'inventory_system_network' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_system_network" (
                "network_id" %(PRIMARYKEY)s,
                "system_id" integer NOT NULL 
                    REFERENCES "inventory_system" ("system_id")
                    ON DELETE CASCADE,
                "created_date" timestamp with time zone NOT NULL,
                "ip_address" varchar(15),
                "ipv6_address" text,
                "device_name" varchar(255),
                "dns_name" varchar(255) NOT NULL,
                "netmask" varchar(20),
                "port_type" varchar(32),
                "active" bool,
                "required" bool,
                UNIQUE ("system_id", "ip_address"),
                UNIQUE ("system_id", "ipv6_address")
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_system_network'] = []
        changed = True
        changed |= db.createIndex("inventory_system_network",
            "inventory_system_network_system_id_idx", "system_id")
        changed |= db.createIndex("inventory_system_network",
            "inventory_system_network_dns_name_idx", "dns_name")
        
    # add local management zone.  must be done after inventory_system and 
    # inventory_system_network are added
    changed |= _addManagementZone(db, cfg)

    if 'inventory_system_log' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_system_log" (
                "system_log_id" %(PRIMARYKEY)s,
                "system_id" integer NOT NULL 
                    REFERENCES "inventory_system" ("system_id")
                    ON DELETE CASCADE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_system_log'] = []
        changed = True
        changed |= db.createIndex("inventory_system_log",
            "inventory_system_log_system_id_idx", "system_id")

    if 'inventory_system_log_entry' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_system_log_entry" (
                "system_log_entry_id" %(PRIMARYKEY)s,
                "system_log_id" integer NOT NULL
                    REFERENCES "inventory_system_log" ("system_log_id")
                    ON DELETE CASCADE,
                "entry" VARCHAR(8092),
                "entry_date" timestamp with time zone NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_system_log_entry'] = []
        changed = True

    if 'inventory_version' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_version" (
                "version_id" %(PRIMARYKEY)s,
                "full" TEXT NOT NULL,
                "label" TEXT NOT NULL,
                "revision" TEXT NOT NULL,
                "ordering" TEXT NOT NULL,
                "flavor" TEXT NOT NULL,
                UNIQUE("full", "ordering", "flavor")
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_version'] = []
        changed = True

    tableName = 'inventory_event_type'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_event_type" (
                "event_type_id" %(PRIMARYKEY)s,
                "name" varchar(8092) NOT NULL UNIQUE,
                "description" varchar(8092) NOT NULL,
                "priority" smallint NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
        changed = True
        changed |= _addTableRows(db, tableName, 'name',
            [dict(name="system registration",
                  description='System registration',
                  # registration events are no longer dispatched immediately
                  # (RBL-8851)
                  priority=70),
             dict(name="system poll",
                  description='System synchronization',
                  priority=50),
             dict(name="immediate system poll",
                  description='On-demand system synchronization',
                  priority=105),
             dict(name="system apply update",
                  description='Scheduled system update', 
                  priority=50),
             dict(name="immediate system apply update",
                  description='System update',
                  priority=105),
             dict(name="system shutdown",
                  description='Scheduled system shutdown',
                  priority=50),
             dict(name="immediate system shutdown", 
                  description='System shutdown',
                  priority=105),
             dict(name='system launch wait',
                  description='Launched system network data discovery',
                  priority=105),
             dict(name="system detect management interface",
                  description="System management interface detection",
                  priority=50),
             dict(name="immediate system detect management interface",
                  description="On-demand system management interface detection",
                  priority=105),
             dict(name="immediate system configuration",
                  description="Update system configuration",
                  priority=105),
            ])
        
    if 'inventory_system_event' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_system_event" (
                "system_event_id" %(PRIMARYKEY)s,
                "system_id" integer NOT NULL 
                    REFERENCES "inventory_system" ("system_id")
                    ON DELETE CASCADE,
                "event_type_id" integer NOT NULL
                    REFERENCES "inventory_event_type",
                "time_created" timestamp with time zone NOT NULL,
                "time_enabled" timestamp with time zone NOT NULL,
                "priority" smallint NOT NULL,
                "event_data" varchar
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_system_event'] = []
        changed |= db.createIndex("inventory_system_event",
            "inventory_system_event_system_id", "system_id")
        changed |= db.createIndex("inventory_system_event",
            "inventory_system_event_event_type_id", "event_type_id")
        changed |= db.createIndex("inventory_system_event",
            "inventory_system_event_time_enabled", "time_enabled")
        changed |= db.createIndex("inventory_system_event",
            "inventory_system_event_priority", "priority")
        changed = True

    if 'inventory_job_state' not in db.tables:
        cu.execute("""
            CREATE TABLE inventory_job_state
            (
                job_state_id %(PRIMARYKEY)s,
                name VARCHAR NOT NULL UNIQUE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_job_state'] = []
        changed = True
    changed |= _addTableRows(db, 'inventory_job_state', 'name',
        [
            dict(name='Queued'), dict(name='Running'),
            dict(name='Completed'), dict(name='Failed'), ])

    tableName = 'inventory_job'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE inventory_job (
                job_id %(PRIMARYKEY)s,
                job_uuid varchar(64) NOT NULL UNIQUE,
                job_state_id integer NOT NULL
                    REFERENCES inventory_job_state,
                event_type_id integer NOT NULL
                    REFERENCES inventory_event_type,
                status_code INTEGER NOT NULL DEFAULT 100,
                status_text VARCHAR NOT NULL DEFAULT 'Initializing',
                status_detail VARCHAR,
                time_created timestamp with time zone NOT NULL,
                time_updated timestamp with time zone NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
        changed = True

    tableName = "inventory_system_job"
    if 'inventory_system_job' not in db.tables:
        # The same job cannot be attached to multiple systems
        # This may change in the future
        cu.execute("""
            CREATE TABLE inventory_system_job (
                system_job_id %(PRIMARYKEY)s,
                job_id integer NOT NULL UNIQUE
                    REFERENCES inventory_job
                    ON DELETE CASCADE,
                system_id integer NOT NULL
                    REFERENCES inventory_system
                    ON DELETE CASCADE,
                event_uuid varchar(64) NOT NULL UNIQUE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
        changed = True

    if 'inventory_trove_available_updates' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_trove_available_updates" (
                "id" %(PRIMARYKEY)s,
                "trove_id" INTEGER NOT NULL,
                "version_id" INTEGER NOT NULL
                    REFERENCES "inventory_version" ("version_id")
                    ON DELETE CASCADE,
                UNIQUE ("trove_id", "version_id")
            )""" % db.keywords)
        db.tables['inventory_trove_available_updates'] = []
        changed = True

    if 'inventory_trove' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_trove" (
                "trove_id" %(PRIMARYKEY)s,
                "name" TEXT NOT NULL,
                "version_id" INTEGER NOT NULL
                    REFERENCES "inventory_version" ("version_id")
                    ON DELETE CASCADE,
                "flavor" text NOT NULL,
                "is_top_level" BOOL NOT NULL,
                "last_available_update_refresh" timestamp with time zone,
                "out_of_date" BOOL,
                UNIQUE ("name", "version_id", "flavor")
            )""" % db.keywords)

        db.tables['inventory_trove'] = []
        changed = True

    if 'inventory_system_installed_software' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_system_installed_software" (
                "id" %(PRIMARYKEY)s,
                "system_id" INTEGER NOT NULL 
                    REFERENCES "inventory_system" ("system_id")
                    ON DELETE CASCADE,
                "trove_id" INTEGER NOT NULL
                    REFERENCES "inventory_trove" ("trove_id"),
                UNIQUE ("system_id", "trove_id")
            )"""  % db.keywords)

    if 'inventory_system_target_credentials' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_system_target_credentials" (
                "id" %(PRIMARYKEY)s,
                "system_id" INTEGER NOT NULL
                    REFERENCES "inventory_system" ("system_id")
                    ON DELETE CASCADE,
                "credentials_id" INTEGER NOT NULL
                    REFERENCES TargetCredentials (targetCredentialsId)
                    ON DELETE CASCADE,
                UNIQUE ("system_id", "credentials_id")
            )""" % db.keywords)
        db.tables['inventory_system_target_credentials'] = []
        changed = True

    if 'django_site' not in db.tables:
        cu.execute("""
            CREATE TABLE "django_site" (
                "id" %(PRIMARYKEY)s,
                "domain" VARCHAR(100) NOT NULL UNIQUE,
                "name" VARCHAR(100) NOT NULL UNIQUE
            )""" % db.keywords)
        db.tables['django_site'] = []
        changed = True
        changed |= _addTableRows(db, 'django_site', 'name',
            [
                dict(id=1, domain="rbuilder.inventory", name="rBuilder Inventory")])

    if 'django_redirect' not in db.tables:
        cu.execute("""
            CREATE TABLE "django_redirect" (
                "id" %(PRIMARYKEY)s,
                "site_id" INTEGER NOT NULL 
                    REFERENCES "django_site" ("id"),
                "old_path" VARCHAR(200) NOT NULL UNIQUE,
                "new_path" VARCHAR(200) NOT NULL 
            )""" % db.keywords)
        db.tables['django_redirect'] = []
        changed = True

    return changed

def _addSystemStates(db, cfg):
    changed = False
    changed |= _addTableRows(db, 'inventory_system_state', 'name',
            [
                dict(name="unmanaged", description="Unmanaged", created_date=str(datetime.datetime.now(tz.tzutc()))),
                dict(name="unmanaged-credentials", description="Unmanaged: Invalid credentials", created_date=str(datetime.datetime.now(tz.tzutc()))),
                dict(name="registered", description="Initial synchronization pending", created_date=str(datetime.datetime.now(tz.tzutc()))),
                dict(name="responsive", description="Online", created_date=str(datetime.datetime.now(tz.tzutc()))),
                dict(name="non-responsive-unknown", description="Not responding: Unknown", created_date=str(datetime.datetime.now(tz.tzutc()))),
                dict(name="non-responsive-net", description="Not responding: Network unreachable", created_date=str(datetime.datetime.now(tz.tzutc()))),
                dict(name="non-responsive-host", description="Not responding: Host unreachable", created_date=str(datetime.datetime.now(tz.tzutc()))),
                dict(name="non-responsive-shutdown", description="Not responding: Shutdown", created_date=str(datetime.datetime.now(tz.tzutc()))),
                dict(name="non-responsive-suspended", description="Not responding: Suspended", created_date=str(datetime.datetime.now(tz.tzutc()))),
                dict(name="non-responsive-credentials", description="Not responding: Invalid credentials", created_date=str(datetime.datetime.now(tz.tzutc()))),
                dict(name="dead", description="Stale", created_date=str(datetime.datetime.now(tz.tzutc()))),
                dict(name="mothballed", description="Retired", created_date=str(datetime.datetime.now(tz.tzutc())))
            ])
    
    return changed

def _addManagementZone(db, cfg):
    changed = False
    
    # add the zone
    zoneName = "Local rBuilder"
    zoneDescription = 'Local rBuilder management zone'
    changed |= _addTableRows(db, 'inventory_zone', 'name',
            [dict(name=zoneName,
                  description=zoneDescription,
                  created_date=str(datetime.datetime.now(tz.tzutc())))])

    return changed

cim_credentials_descriptor=r"""<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd">
  <metadata></metadata>
  <dataFields>
    <field>
      <name>ssl_client_certificate</name>
      <descriptions>
        <desc>Client Certificate</desc>
      </descriptions>
      <type>str</type>
      <constraints>
        <descriptions>
          <desc>The certificate must start with '-----BEGIN CERTIFICATE-----', end with '-----END CERTIFICATE-----', and have a maximum length of 16384 characters.</desc>
        </descriptions>
        <regexp>^\s*-----BEGIN CERTIFICATE-----.*-----END CERTIFICATE-----\s*$</regexp>
        <length>16384</length>
      </constraints>
      <required>true</required>
      <allowFileContent>true</allowFileContent>
    </field>
    <field>
      <name>ssl_client_key</name>
      <descriptions>
        <desc>Client Private Key</desc>
      </descriptions>
      <type>str</type>
      <constraints>
        <descriptions>
          <desc>The key must start with '-----BEGIN PRIVATE KEY-----', end with '----END PRIVATE KEY-----', and have a maximum length of 16384 characters.</desc>
        </descriptions>
        <regexp>^\s*-----BEGIN (\S+ )?PRIVATE KEY-----.*-----END (\S+ )?PRIVATE KEY-----\s*$</regexp>
        <length>16384</length>
      </constraints>
      <required>true</required>
     <allowFileContent>true</allowFileContent>
    </field>
  </dataFields>
</descriptor>"""

wmi_credentials_descriptor=r"""<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd">
  <metadata></metadata>
  <dataFields>
    <field><name>domain</name>
      <descriptions>
        <desc>Windows Domain</desc>
      </descriptions>
      <type>str</type>
      <default></default>
      <required>true</required>
    </field>
    <field>
      <name>username</name>
      <descriptions>
        <desc>User</desc>
      </descriptions>
      <type>str</type>
      <default></default>
      <required>true</required>
    </field>
    <field>
      <name>password</name>
      <descriptions>
        <desc>Password</desc>
      </descriptions>
      <password>true</password>
      <type>str</type>
      <default></default>
      <required>true</required>
    </field>
  </dataFields>
</descriptor>"""

def _addManagementInterfaces(db):
    changed = False
    
    changed |= _addTableRows(db, 'inventory_management_interface', 'name',
            [dict(name='cim',
                  description='Common Information Model (CIM)',
                  port=5989,
                  created_date=str(datetime.datetime.now(tz.tzutc())),
                  credentials_descriptor=cim_credentials_descriptor,
                  credentials_readonly=True
            )])
    
    changed |= _addTableRows(db, 'inventory_management_interface', 'name',
            [dict(name='wmi',
                  description='Windows Management Instrumentation (WMI)',
                  port=135,
                  created_date=str(datetime.datetime.now(tz.tzutc())),
                  credentials_descriptor=wmi_credentials_descriptor,
                  credentials_readonly=False
            )])
    
    return changed

inventory_creation_descriptor=r"""<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd"> 
  <metadata>
  </metadata> 
  <dataFields>
    <field> 
      <name>name</name> 
      <help lang="en_US">@System_creation_name@</help>
      <descriptions> 
        <desc>System Name</desc> 
      </descriptions> 
      <type>str</type> 
      <default></default>
      <required>true</required>
      <prompt>
        <desc>Enter the system name</desc>
      </prompt>
    </field>
    <field> 
      <name>description</name> 
      <help lang="en_US">@System_creation_description@</help>
      <descriptions> 
        <desc>Description</desc> 
      </descriptions> 
      <type>str</type> 
      <default></default>
      <required>false</required>
      <prompt>
        <desc>Enter the system description</desc>
      </prompt>
    </field>
    <field> 
      <name>tempIpAddress</name> 
      <help lang="en_US">@System_creation_ip@</help>
      <descriptions> 
        <desc>Network Address</desc> 
      </descriptions> 
      <prompt>
        <desc>Enter the system network address</desc>
      </prompt>
      <type>str</type> 
      <default></default> 
      <required>true</required>
    </field>
    <field>
      <name>requiredNetwork</name>
      <help lang="en_US">@System_creation_required_net@</help>
      <required>false</required>
      <multiple>True</multiple>
      <descriptions>
        <desc>Manage Via this Address Only</desc>
      </descriptions>
      <enumeratedType>
        <describedValue>
          <descriptions>
            <desc></desc>
          </descriptions>
          <key>true</key>
        </describedValue>
      </enumeratedType>
      <default>false</default>
    </field>
  </dataFields> 
</descriptor>"""

management_node_creation_descriptor=r"""<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd"> 
  <metadata>
  </metadata> 
  <dataFields>
    <field> 
      <name>name</name> 
      <help lang="en_US">@Management_node_creation_name@</help>
      <descriptions> 
        <desc>System Name</desc> 
      </descriptions> 
      <type>str</type> 
      <default></default>
      <required>true</required>
      <prompt>
        <desc>Enter the system name</desc>
      </prompt>
    </field>
    <field> 
      <name>description</name> 
      <help lang="en_US">@Management_node_creation_description@</help>
      <descriptions> 
        <desc>Description</desc> 
      </descriptions> 
      <type>str</type> 
      <default></default>
      <required>false</required>
      <prompt>
        <desc>Enter the system description</desc>
      </prompt>
    </field>
    <field> 
      <name>tempIpAddress</name> 
      <help lang="en_US">@Management_node_creation_ip@</help>
      <descriptions> 
        <desc>Network Address</desc> 
      </descriptions> 
      <prompt>
        <desc>Enter the system network address</desc>
      </prompt>
      <type>str</type> 
      <default></default> 
      <required>true</required>
    </field>
    <field> 
      <name>zoneName</name> 
      <help lang="en_US">@Management_node_zone_creation_name@</help>
      <descriptions> 
        <desc>Zone Name</desc> 
      </descriptions> 
      <type>str</type> 
      <default></default>
      <required>true</required>
      <prompt>
        <desc>Enter the name of the zone</desc>
      </prompt>
    </field>
    <field> 
      <name>zoneDescription</name> 
      <help lang="en_US">@Management_node_zone_creation_description@</help>
      <descriptions> 
        <desc>Zone Description</desc> 
      </descriptions> 
      <type>str</type> 
      <default></default>
      <required>false</required>
      <prompt>
        <desc>Enter a description of the zone</desc>
      </prompt>
    </field>
  </dataFields> 
</descriptor>"""

windows_build_node_creation_descriptor=r"""<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd"> 
  <metadata>
  </metadata> 
  <dataFields>
    <field> 
      <name>name</name> 
      <help lang="en_US">@Windows_build_node_creation_name@</help>
      <descriptions> 
        <desc>System Name</desc> 
      </descriptions> 
      <type>str</type> 
      <default></default>
      <required>true</required>
      <prompt>
        <desc>Enter the system name.</desc>
      </prompt>
    </field>
    <field> 
      <name>description</name> 
      <help lang="en_US">@Windows_build_node_creation_description@</help>
      <descriptions> 
        <desc>Description</desc> 
      </descriptions> 
      <type>str</type> 
      <default></default>
      <required>false</required>
      <prompt>
        <desc>Enter the system description</desc>
      </prompt>
    </field>
    <field> 
      <name>tempIpAddress</name> 
      <help lang="en_US">@Windows_build_node_creation_ip@</help>
      <descriptions> 
        <desc>Network Address</desc> 
      </descriptions> 
      <prompt>
        <desc>Enter the system network address</desc>
      </prompt>
      <type>str</type> 
      <default></default> 
      <required>true</required>
    </field>
  </dataFields> 
</descriptor>"""

def _addSystemTypes(db):
    changed = False
    
    changed |= _addTableRows(db, 'inventory_system_type', 'name',
            [dict(name='inventory',
                  description='Inventory',
                  created_date=str(datetime.datetime.now(tz.tzutc())),
                  infrastructure=False,
                  creation_descriptor=inventory_creation_descriptor
            )])
    
    changed |= _addTableRows(db, 'inventory_system_type', 'name',
            [dict(name='infrastructure-management-node',
                  description='rPath Update Service (Infrastructure)',
                  created_date=str(datetime.datetime.now(tz.tzutc())),
                  infrastructure=True,
                  creation_descriptor=management_node_creation_descriptor
            )])
    
    changed |= _addTableRows(db, 'inventory_system_type', 'name',
            [dict(name='infrastructure-windows-build-node',
                  description='rPath Windows Build Service (Infrastructure)',
                  created_date=str(datetime.datetime.now(tz.tzutc())),
                  infrastructure=True,
                  creation_descriptor=windows_build_node_creation_descriptor
            )])
    
    return changed

def _addTableRows(db, table, uniqueKey, rows, uniqueCols=[]):
    """
    Adds rows to the table, if they do not exist already
    The rows argument is a list of dictionaries
    """
    if not rows:
        return
    cu = db.cursor()
    inserts = []
    sql = "SELECT 1 FROM %s WHERE %s = ?" % (table, uniqueKey)
    tableCols = rows[0].keys()
    if not uniqueCols:
        uniqueCols = [uniqueKey]
    for row in rows:
        valList = [{c:row[c]} for c in uniqueCols]
        uniqueValues = {}
        [uniqueValues.update(v) for v in valList]
        pk = _getRowPk(db, table, uniqueKey, **uniqueValues)
        if pk:
            continue
        inserts.append(tuple(row[c] for c in tableCols))
    if not inserts:
        return False
    sql = "INSERT INTO %s (%s) VALUES (%s)" % (table,
        ','.join(tableCols), ','.join('?' for c in tableCols))
    cu.executemany(sql, inserts)
    return True

def _getRowPk(db, table, pkColumn, **uniqueVals):
    """
    Get the primary key value for a table row based on the value of a
    different uniqueColumn.
    """
    cu = db.cursor()
    sql = """
        SELECT %s
        FROM %s
        WHERE %s
    """
    whereClause = ["%s='%s'" % (k, v) for k, v in uniqueVals.items()]
    whereClause = 'AND '.join(whereClause)
    cu.execute(sql % (pkColumn, table, whereClause))
    row = cu.fetchone()
    if row:
        return row[0]
    else:
        return None

def _createJobsSchema(db):
    cu = db.cursor()
    changed = False

    if 'job_types' not in db.tables:
        cu.execute("""
            CREATE TABLE job_types
            (
                job_type_id %(PRIMARYKEY)s,
                name VARCHAR NOT NULL UNIQUE,
                description VARCHAR NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['job_types'] = []
        changed = True
    changed |= _addTableRows(db, 'job_types', 'name',
        [ dict(name="instance-launch", description='Instance Launch'),
          dict(name="platform-load", description='Platform Load'),
          dict(name="software-version-refresh", description='Software Version Refresh'),
          dict(name="instance-update", description='Update Instance'),
          dict(name="image-deployment", description="Image Deployment"),
        ])
    if 'job_states' not in db.tables:
        cu.execute("""
            CREATE TABLE job_states
            (
                job_state_id %(PRIMARYKEY)s,
                name VARCHAR NOT NULL UNIQUE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['job_states'] = []
        changed = True
    changed |= _addTableRows(db, 'job_states', 'name', [ dict(name='Queued'),
        dict(name='Running'), dict(name='Completed'), dict(name='Failed') ])

    if 'rest_methods' not in db.tables:
        cu.execute("""
            CREATE TABLE rest_methods
            (
                rest_method_id %(PRIMARYKEY)s,
                name VARCHAR NOT NULL UNIQUE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['rest_methods'] = []
        changed = True
    changed |= _addTableRows(db, 'rest_methods', 'name', [ dict(name='POST'),
        dict(name='PUT'), dict(name='DELETE') ])

    if 'jobs' not in db.tables:
        cu.execute("""
            CREATE TABLE jobs
            (
                job_id      %(PRIMARYKEY)s,
                job_type_id INTEGER NOT NULL
                    REFERENCES job_types ON DELETE CASCADE,
                job_state_id INTEGER NOT NULL
                    REFERENCES job_states ON DELETE CASCADE,
                job_uuid    VARCHAR(64) NOT NULL UNIQUE,
                created_by   INTEGER NOT NULL
                    REFERENCES Users ON DELETE CASCADE,
                created     NUMERIC(14,4) NOT NULL,
                modified    NUMERIC(14,4) NOT NULL,
                expiration  NUMERIC(14,4),
                ttl         INTEGER,
                pid         INTEGER,
                message     VARCHAR,
                error_response VARCHAR,
                rest_uri    VARCHAR,
                rest_method_id INTEGER
                    REFERENCES rest_methods ON DELETE CASCADE,
                rest_args   VARCHAR
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['jobs'] = []
        changed = True

    if 'job_history' not in db.tables:
        cu.execute("""
            CREATE TABLE job_history
            (
                job_history_id  %(PRIMARYKEY)s,
                -- job_history_type needed
                job_id          INTEGER NOT NULL
                    REFERENCES jobs ON DELETE CASCADE,
                timestamp   NUMERIC(14,3) NOT NULL,
                content     VARCHAR NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['job_history'] = []
        changed = True

    if 'job_results' not in db.tables:
        cu.execute("""
            CREATE TABLE job_results
            (
                job_result_id   %(PRIMARYKEY)s,
                job_id          INTEGER NOT NULL
                    REFERENCES jobs ON DELETE CASCADE,
                data    VARCHAR NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['job_results'] = []
        changed = True

    if 'job_target' not in db.tables:
        cu.execute("""
            CREATE TABLE job_target
            (
                job_id      INTEGER NOT NULL
                    REFERENCES jobs ON DELETE CASCADE,
                targetId    INTEGER NOT NULL
                    REFERENCES Targets ON DELETE CASCADE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['job_target'] = []
        changed = True

    if 'job_system' not in db.tables:
        cu.execute("""
            CREATE TABLE job_system
            (
                job_id      INTEGER NOT NULL
                    REFERENCES jobs ON DELETE CASCADE,
                system_id    INTEGER NOT NULL
                    REFERENCES inventory_system ON DELETE CASCADE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['job_system'] = []
        changed = True

    return changed

def _createPKI(db):
    """Public key infrastructure tables"""
    changed = False

    changed |= createTable(db, 'pki_certificates', """
        CREATE TABLE pki_certificates (
            fingerprint             text PRIMARY KEY,
            purpose                 text NOT NULL,
            is_ca                   boolean NOT NULL DEFAULT false,
            x509_pem                text NOT NULL,
            pkey_pem                text NOT NULL,
            issuer_fingerprint      text
                REFERENCES pki_certificates ( fingerprint )
                ON DELETE SET NULL,
            ca_serial_index         integer,
            time_issued             timestamptz NOT NULL,
            time_expired            timestamptz NOT NULL
        )""")

    return changed

def _createQuerySetSchema(db):
    """QuerySet tables"""
    changed = False

    changed |= createTable(db, 'querysets_queryset', """
        CREATE TABLE "querysets_queryset" (
            "query_set_id" %(PRIMARYKEY)s,
            "name" TEXT NOT NULL UNIQUE,
            "description" TEXT,
            "created_date" TIMESTAMP WITH TIME ZONE NOT NULL,
            "modified_date" TIMESTAMP WITH TIME ZONE NOT NULL,
            "resource_type" TEXT NOT NULL,
            "can_modify" BOOLEAN NOT NULL DEFAULT TRUE
        )""")
    changed |= _addTableRows(db, "querysets_queryset", "name",
        [dict(name="All Systems", resource_type="system",
            description="All Systems",
            created_date=str(datetime.datetime.now(tz.tzutc())),
            modified_date=str(datetime.datetime.now(tz.tzutc())),
            can_modify=False),
         dict(name="Active Systems", resource_type="system",
            description="Active Systems",
            created_date=str(datetime.datetime.now(tz.tzutc())),
            modified_date=str(datetime.datetime.now(tz.tzutc())),
            can_modify=False),
         dict(name="Inactive Systems", resource_type="system",
            description="Inactive Systems",
            created_date=str(datetime.datetime.now(tz.tzutc())),
            modified_date=str(datetime.datetime.now(tz.tzutc())),
            can_modify=False),
         dict(name="Physical Systems", resource_type="system",
            description="Physical Systems",
            created_date=str(datetime.datetime.now(tz.tzutc())),
            modified_date=str(datetime.datetime.now(tz.tzutc())),
            can_modify=False),
        ])
    allQSId = _getRowPk(db, "querysets_queryset", "query_set_id", 
        name="All Systems")
    activeQSId = _getRowPk(db, "querysets_queryset", "query_set_id", 
        name="Active Systems")
    inactiveQSId = _getRowPk(db, "querysets_queryset", "query_set_id", 
        name="Inactive Systems")
    physicalQSId = _getRowPk(db, "querysets_queryset", "query_set_id", 
        name="Physical Systems")

    changed |= createTable(db, 'querysets_filterentry', """
        CREATE TABLE "querysets_filterentry" (
            "filter_entry_id" %(PRIMARYKEY)s,
            "field" TEXT NOT NULL,
            "operator" TEXT NOT NULL,
            "value" TEXT,
            UNIQUE("field", "operator", "value")
        )""")
    changed |= _addTableRows(db, "querysets_filterentry",
        'filter_entry_id',
        [dict(field="current_state.name", operator="EQUAL", value="responsive"),
         dict(field="current_state.name", operator="IN", 
            value="(unmanaged,unmanaged-credentials,registered,non-responsive-unknown,non-responsive-net,non-responsive-host,non-responsive-shutdown,non-responsive-suspended,non-responsive-credentials)"),
         dict(field="target", operator='IS_NULL', value="True")],
        ['field', 'operator', 'value'])
    activeFiltId = _getRowPk(db, "querysets_filterentry", 'filter_entry_id',
        field="current_state.name", operator="EQUAL", value="responsive")
    inactiveFiltId = _getRowPk(db, "querysets_filterentry", 'filter_entry_id',
        field="current_state.name", operator="IN", 
                    value="(unmanaged,unmanaged-credentials,registered,non-responsive-unknown,non-responsive-net,non-responsive-host,non-responsive-shutdown,non-responsive-suspended,non-responsive-credentials)")
    physicalFiltId = _getRowPk(db, "querysets_filterentry", 'filter_entry_id',
        field="target", operator='IS_NULL', value="True")

    changed |= createTable(db, 'querysets_querytag', """
        CREATE TABLE "querysets_querytag" (
            "query_tag_id" %(PRIMARYKEY)s,
            "query_set_id" INTEGER UNIQUE
                REFERENCES "querysets_queryset" ("query_set_id")
                ON DELETE CASCADE
                NOT NULL,
            "name" TEXT NOT NULL UNIQUE
        )""")
    changed |= _addTableRows(db, "querysets_querytag", "name",
        [dict(query_set_id=allQSId, name="query-tag-All_Systems-1"),
         dict(query_set_id=activeQSId, name="query-tag-Active_Systems-2"),
         dict(query_set_id=inactiveQSId, name="query-tag-Inactive_Systems-3"),
         dict(query_set_id=physicalQSId, name="query-tag-Physical_Systems-4"),
        ])

    changed |= createTable(db, 'querysets_inclusionmethod', """
        CREATE TABLE "querysets_inclusionmethod" (
            "inclusion_method_id" %(PRIMARYKEY)s,
            "name" TEXT NOT NULL UNIQUE
        )""")
    changed |= _addTableRows(db, "querysets_inclusionmethod",
        "name",
        [dict(name="chosen"),
         dict(name="filtered")])

    changed |= createTable(db, 'querysets_systemtag', """
        CREATE TABLE "querysets_systemtag" (
            "system_tag_id" %(PRIMARYKEY)s,
            "system_id" INTEGER
                REFERENCES "inventory_system" ("system_id")
                ON DELETE CASCADE
                NOT NULL,
            "query_tag_id" INTEGER
                REFERENCES "querysets_querytag" ("query_tag_id")
                ON DELETE CASCADE
                NOT NULL,
            "inclusion_method_id" INTEGER
                REFERENCES "querysets_inclusionmethod" ("inclusion_method_id")
                ON DELETE CASCADE
                NOT NULL,
            UNIQUE ("system_id", "query_tag_id", "inclusion_method_id")
        )""")

    changed |= createTable(db, "querysets_queryset_filter_entries", """
        CREATE TABLE "querysets_queryset_filter_entries" (
            "id" %(PRIMARYKEY)s,
            "queryset_id" INTEGER
                REFERENCES "querysets_queryset" ("query_set_id")
                ON DELETE CASCADE
                NOT NULL,
            "filterentry_id" INTEGER
                REFERENCES "querysets_filterentry" ("filter_entry_id")
                ON DELETE CASCADE
                NOT NULL,
            UNIQUE ("queryset_id", "filterentry_id")
        )""")

    changed |= _addTableRows(db, "querysets_queryset_filter_entries",
        'id',
        [dict(queryset_id=activeQSId, filterentry_id=activeFiltId),
         dict(queryset_id=inactiveQSId, filterentry_id=inactiveFiltId),
         dict(queryset_id=physicalQSId, filterentry_id=physicalFiltId)],
        ['queryset_id', 'filterentry_id'])

    changed |= createTable(db, "querysets_queryset_children", """
        CREATE TABLE "querysets_queryset_children" (
            "id" %(PRIMARYKEY)s,
            "from_queryset_id" INTEGER
                REFERENCES "querysets_queryset" ("query_set_id")
                ON DELETE CASCADE
                NOT NULL,
            "to_queryset_id" INTEGER
                REFERENCES "querysets_queryset" ("query_set_id")
                ON DELETE CASCADE
                NOT NULL,
            UNIQUE ("from_queryset_id", "to_queryset_id")
        )""")
    changed |= _addTableRows(db, "querysets_queryset_children",
        'id',
        [dict(from_queryset_id=allQSId, to_queryset_id=activeQSId),
         dict(from_queryset_id=allQSId, to_queryset_id=inactiveQSId)],
        uniqueCols=('from_queryset_id', 'to_queryset_id'))

    return changed

def _createChangeLogSchema(db):
    """ChangeLog tables"""
    changed = False

    changed |= createTable(db, 'changelog_change_log', """
        CREATE TABLE "changelog_change_log" (
            "change_log_id" %(PRIMARYKEY)s,
            "resource_type" TEXT NOT NULL,
            "resource_id" INTEGER NOT NULL
        )""")

    changed |= createTable(db, 'changelog_change_log_entry', """
        CREATE TABLE "changelog_change_log_entry" (
            "change_log_entry_id" %(PRIMARYKEY)s,
            "change_log_id" INTEGER
                REFERENCES "changelog_change_log" ("change_log_id")
                ON DELETE CASCADE NOT NULL,
            "entry_text" TEXT NOT NULL,
            "entry_date" TIMESTAMP WITH TIME ZONE NOT NULL
        )""")

    return changed

# create the (permanent) server repository schema
def createSchema(db, doCommit=True, cfg=None):
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
    changed |= _createSessions(db)
    changed |= _createTargets(db)
    changed |= _createPlatforms(db)
    changed |= _createCapsuleIndexerSchema(db)
    changed |= _createRepositoryLogSchema(db)
    changed |= _createInventorySchema(db, cfg)
    changed |= _createJobsSchema(db)
    changed |= _createCapsuleIndexerYumSchema(db)
    changed |= _createPKI(db)
    changed |= _createQuerySetSchema(db)
    changed |= _createChangeLogSchema(db)

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
        createSchema(db, cfg=cfg)
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
