#
# Copyright (c) 2011 rPath, Inc.
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
RBUILDER_DB_VERSION = sqllib.DBversion(60, 9)

def _createTrigger(db, table, column="changed"):
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
    if not definition.lstrip()[:20].upper().startswith('CREATE TABLE'):
        # Avoid duplication for name; if the statement doesn't start
        # with CREATE TABLE, then assume it's just a straight list of
        # fields
        definition = "CREATE TABLE %s (\n        %s\n) %%(TABLEOPTS)s" % (
            name, definition.strip().rstrip(','))
    cu.execute(definition % db.keywords)
    db.tables[name] = []
    return True


def _createUsers(db):
    cu = db.cursor()

    if 'Users' not in db.tables:
        cu.execute("""
        CREATE TABLE Users (
            userId              %(PRIMARYKEY)s,
            username            varchar(128)    NOT NULL    UNIQUE,
            fullName            varchar(128)    NOT NULL    DEFAULT '',
            salt                text,
            passwd              varchar(254),
            email               varchar(128),
            displayEmail        text,
            timeCreated         numeric(14,3),
            timeAccessed        numeric(14,3),
            active              smallint,
            blurb               text,
            is_admin            boolean         NOT NULL    DEFAULT false,
            timeModified        numeric(14,3),
            created_by          integer
                REFERENCES Users ON DELETE SET NULL,
            modified_by         integer
                REFERENCES Users ON DELETE SET NULL,
            can_create           BOOLEAN       NOT NULL    DEFAULT false,
            deleted              BOOLEAN       NOT NULL    DEFAULT false
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['Users'] = []
    if db.driver != 'sqlite':
        # Create a case-insensitive unique constraint on username
        db.createIndex('Users', 'users_username_casei_uq',
                '( UPPER(username) )', unique=True)
    db.createIndex('Users', 'UsersActiveIdx', 'username, active')

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
    db.createIndex('UserData', 'UserDataIdx', 'userId')

    if 'Confirmations' not in db.tables:
        cu.execute("""
        CREATE TABLE Confirmations (
            userId              integer         NOT NULL
                REFERENCES Users ON DELETE CASCADE,
            timeRequested       integer,
            confirmation        varchar(255)
        ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['Confirmations'] = []


def _createLabels(db):
    cu = db.cursor()

    if 'Labels' not in db.tables:
        cu.execute("""
        CREATE TABLE Labels (
            labelId             %(PRIMARYKEY)s,
            projectId           integer         NOT NULL  UNIQUE
                REFERENCES Projects ON DELETE CASCADE,
            label               varchar(255)              UNIQUE,
            url                 varchar(255),
            authType            varchar(32)     NOT NULL    DEFAULT 'none',
            username            varchar(255),
            password            varchar(255),
            entitlement         varchar(254),
            CONSTRAINT label_not_empty CHECK (label != '')
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Labels'] = []
    db.createIndex('Labels', 'LabelsPackageIdx', 'projectId')


def _createRbac(db):
    '''role based access control tables'''

    cu = db.cursor()

    if 'rbac_permission_type' not in db.tables:
        cu.execute("""
            CREATE TABLE "rbac_permission_type" (
                "permission_type_id" %(PRIMARYKEY)s,
                "name" TEXT NOT NULL UNIQUE,
                "description" TEXT NOT NULL
        )""" % db.keywords)
        db.tables['rbac_permission_type'] = []

    _addTableRows(db, 'rbac_permission_type', 'name', [
        dict(name="ReadMembers", description='Read Member Resources'),
        dict(name="ModMembers", description='Modify Member Resources'),
        dict(name="ReadSet", description='Read Set'),
        dict(name="ModSetDef", description='Modify Set Definition'),
        dict(name="CreateResource", description='Create Resource'), 
    ])

    if 'rbac_role' not in db.tables:
        cu.execute("""
        CREATE TABLE rbac_role (
            role_id      %(PRIMARYKEY)s,
            role_name    TEXT,
            description  TEXT,
            created_date timestamp with time zone NOT NULL,
            modified_date timestamp with time zone NOT NULL,
            created_by   INTEGER
               REFERENCES Users ( userId )
               ON DELETE CASCADE,
            modified_by   INTEGER
               REFERENCES Users ( userId )
               ON DELETE CASCADE,
            is_identity  BOOLEAN NOT NULL DEFAULT FALSE
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['rbac_role'] = []

    if 'rbac_user_role' not in db.tables:
        cu.execute("""
        CREATE TABLE rbac_user_role (
            rbac_user_role_id  %(PRIMARYKEY)s,
            role_id      INTEGER NOT NULL
               REFERENCES rbac_role ( role_id )
               ON DELETE CASCADE
               ON UPDATE CASCADE,
            user_id      INTEGER NOT NULL
               REFERENCES Users ( userId )
               ON DELETE CASCADE,
            created_by   INTEGER
               REFERENCES Users ( userId )
               ON DELETE CASCADE,
            modified_by   INTEGER
               REFERENCES Users ( userId )
               ON DELETE CASCADE,
            created_date timestamp with time zone NOT NULL,
            modified_date timestamp with time zone NOT NULL,
            UNIQUE ( "role_id", "user_id" )
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['rbac_user_role'] = []

    if 'rbac_permission' not in db.tables:
        cu.execute("""
        CREATE TABLE rbac_permission (
            permission_id   %(PRIMARYKEY)s,
            role_id         INTEGER NOT NULL
               REFERENCES rbac_role ( role_id )
               ON DELETE CASCADE
               ON UPDATE CASCADE,
            queryset_id      INTEGER NOT NULL
               REFERENCES querysets_queryset ( query_set_id )
               ON DELETE CASCADE
               ON UPDATE CASCADE,
            permission_type_id  INTEGER NOT NULL
                   REFERENCES rbac_permission_type ( permission_type_id )
                   ON DELETE CASCADE
                   ON UPDATE CASCADE,
            created_date timestamp with time zone NOT NULL,
            modified_date timestamp with time zone NOT NULL,
            created_by   INTEGER
               REFERENCES Users ( userId )
               ON DELETE CASCADE,
            modified_by   INTEGER
               REFERENCES Users ( userId )
               ON DELETE CASCADE,
            UNIQUE ( "role_id", "queryset_id", "permission_type_id" )
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['rbac_permission'] = []

    db.createIndex('rbac_user_role', 'RbacUserRoleSearchIdx',
        'user_id, role_id', unique=True)
    db.createIndex('rbac_permission', 'RbacPermissionLookupIdx',
        'role_id, queryset_id, permission_type_id')

    # rbac query sets
    _createAllRoles(db)
    _createAllGrants(db)

    # target service query set
    _createAllTargets(db)

    # queryset tag tables
    createTable(db, 'querysets_permissiontag', """
        CREATE TABLE "querysets_permissiontag" (
            "permission_tag_id" %(BIGPRIMARYKEY)s,
            "permission_id" INTEGER
                REFERENCES "rbac_permission" ("permission_id")
                ON DELETE CASCADE
                NOT NULL,
            "query_set_id" INTEGER
                REFERENCES "querysets_queryset" ("query_set_id")
                ON DELETE CASCADE,
            "inclusion_method_id" INTEGER
                REFERENCES "querysets_inclusionmethod" ("inclusion_method_id")
                ON DELETE CASCADE
                NOT NULL,
            CONSTRAINT querysets_permissiontag_uq UNIQUE ("permission_id",
                "query_set_id", "inclusion_method_id")
        )""")

    createTable(db, 'querysets_roletag', """
        CREATE TABLE "querysets_roletag" (
            "role_tag_id" %(BIGPRIMARYKEY)s,
            "role_id" INTEGER
                REFERENCES "rbac_role" ("role_id")
                ON DELETE CASCADE
                NOT NULL,
            "query_set_id" INTEGER
                REFERENCES "querysets_queryset" ("query_set_id")
                ON DELETE CASCADE,
            "inclusion_method_id" INTEGER
                REFERENCES "querysets_inclusionmethod" ("inclusion_method_id")
                ON DELETE CASCADE
                NOT NULL,
            CONSTRAINT querysets_roletag_uq UNIQUE ("role_id", "query_set_id",
                "inclusion_method_id")
        )""")
    
    _createNonIdentityRoles(db)

    createTable(db, 'querysets_imagetag', """
        CREATE TABLE "querysets_imagetag" (
            "image_tag_id" %(BIGPRIMARYKEY)s,
            "image_id" INTEGER
                REFERENCES "builds" ("buildid")
                ON DELETE CASCADE
                NOT NULL,
            "query_set_id" INTEGER
                REFERENCES "querysets_queryset" ("query_set_id")
                ON DELETE CASCADE,
            "inclusion_method_id" INTEGER
                REFERENCES "querysets_inclusionmethod" ("inclusion_method_id")
                ON DELETE CASCADE
                NOT NULL,
            CONSTRAINT querysets_imagetag_uq UNIQUE ("image_id", "query_set_id",
                "inclusion_method_id")
        )""")


    _createAllImages(db)


def _createProjects(db):
    cu = db.cursor()

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
            disabled            boolean         NOT NULL    DEFAULT FALSE,
            hidden              boolean         NOT NULL    DEFAULT FALSE,
            external            boolean         NOT NULL    DEFAULT FALSE,
            isAppliance         boolean         NOT NULL    DEFAULT TRUE,
            timeCreated         numeric(14,3),
            timeModified        numeric(14,3),
            commitEmail         varchar(128)                DEFAULT '',
            prodtype            varchar(128)                DEFAULT '',
            version             varchar(128)                DEFAULT '',
            backupExternal      boolean        NOT NULL    DEFAULT FALSE,
            database            varchar(128),
            modified_by         integer
                REFERENCES Users ( userId ) ON DELETE SET NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Projects'] = []
    db.createIndex('Projects', 'ProjectsHostnameIdx', 'hostname')
    db.createIndex('Projects', 'ProjectsShortnameIdx', 'shortname')
    db.createIndex('Projects', 'ProjectsDisabledIdx', 'disabled')
    db.createIndex('Projects', 'ProjectsHiddenIdx', 'hidden')
    if db.driver != 'sqlite':
        # Case-insensitive constraints
        db.createIndex('Projects', 'projects_shortname_casei_uq',
                '( UPPER(shortname) )', unique=True)

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
    db.createIndex('ProjectUsers',
        'ProjectUsersProjectIdx', 'projectId')
    db.createIndex('ProjectUsers', 'ProjectUsersUserIdx', 'userId')

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


def _createBuilds(db):
    cu = db.cursor()

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
    db.createIndex('PublishedReleases', 'PubReleasesProjectIdIdx',
            'projectId')

    if 'Builds' not in db.tables:
        cu.execute("""
        CREATE TABLE Builds (
            buildId             %(PRIMARYKEY)s,
            projectId            integer        NOT NULL
                REFERENCES Projects ON DELETE CASCADE,
            stageid              integer
                 REFERENCES project_branch_stage ON DELETE SET NULL,
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
            output_trove         text,
            base_image           integer
                REFERENCES Builds ON DELETE SET NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Builds'] = []

    db.createIndex('Builds', 'BuildProjectIdIdx', 'projectId')
    db.createIndex('Builds', 'BuildPubReleaseIdIdx', 'pubReleaseId')

    if 'BuildData' not in db.tables:
        cu.execute("""
        CREATE TABLE BuildData (
            buildDataId             %(BIGPRIMARYKEY)s,
            buildId             integer         NOT NULL
                REFERENCES Builds ON DELETE CASCADE,
            name                varchar(32)     NOT NULL,
            value               text            NOT NULL,
            dataType            smallint        NOT NULL,

            CONSTRAINT builddata_uq UNIQUE ( buildId, name )

        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['BuildData'] = []

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

    if 'FilesUrls' not in db.tables:
        cu.execute("""
        CREATE TABLE FilesUrls (
            urlId               %(PRIMARYKEY)s,
            urlType             smallint        NOT NULL,
            url                 varchar(255)    NOT NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['FilesUrls'] = []

    if 'BuildFilesUrlsMap' not in db.tables:
        cu.execute("""
        CREATE TABLE BuildFilesUrlsMap (
            buildFilesUrlsMapId %(PRIMARYKEY)s,
            fileId              integer         NOT NULL
                REFERENCES BuildFiles ON DELETE CASCADE,
            urlId               integer         NOT NULL
                REFERENCES FilesUrls ON DELETE CASCADE,

            CONSTRAINT buildfilesurlsmap_uq UNIQUE ( fileId, urlId )
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['BuildFilesUrlsMap'] = []

    if 'UrlDownloads' not in db.tables:
        cu.execute("""
        CREATE TABLE UrlDownloads (
            urlId               integer         NOT NULL
                REFERENCES FilesUrls ON DELETE CASCADE,
            timeDownloaded      numeric(14,0)   NOT NULL    DEFAULT 0,
            ip                  varchar(64)     NOT NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['UrlDownloads'] = []

    createTable(db, 'auth_tokens', """
        CREATE TABLE auth_tokens (
            token_id            %(BIGPRIMARYKEY)s,
            token               text            NOT NULL UNIQUE,
            expires_date        timestamptz     NOT NULL,
            user_id             integer         NOT NULL
                REFERENCES Users ON UPDATE CASCADE ON DELETE CASCADE,
            image_id            integer
                REFERENCES Builds ON UPDATE CASCADE ON DELETE CASCADE
        )""")


def _createCommits(db):
    cu = db.cursor()

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
    db.createIndex('Commits', 'CommitsProjectIdx', 'projectId')


def _createPackageIndex(db):
    cu = db.cursor()

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
    db.createIndex("PackageIndex", "PackageIndex_Project_Name_idx",
            "projectId, name")
    db.createIndex("PackageIndex", "PackageIndexNameIdx",
        "name, version")
    db.createIndex("PackageIndex", "PackageIndexProjectIdx",
        "projectId")
    db.createIndex("PackageIndex", "PackageIndexServerBranchName",
        "serverName, branchName")

    if 'PackageIndexMark' not in db.tables:
        cu.execute("""
        CREATE TABLE PackageIndexMark (
            mark                integer         NOT NULL
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['PackageIndexMark'] = []
        cu.execute("INSERT INTO PackageIndexMark VALUES(0)")


def _createMirrorInfo(db):
    cu = db.cursor()

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
    db.createIndex('InboundMirrors', 'InboundMirrorsProjectIdIdx',
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
    db.createIndex('OutboundMirrors', 'OutboundMirrorsProjectIdIdx',
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


def _createSessions(db):
    cu = db.cursor()

    if 'Sessions' not in db.tables:
        cu.execute("""
        CREATE TABLE Sessions (
            sessIdx             %(PRIMARYKEY)s,
            sid                 varchar(64)         NOT NULL    UNIQUE,
            data                text
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['Sessions'] = []


def _createProductVersions(db):
    cu = db.cursor()

    # TODO:
    # * Rename table ProductVersions to project_branch
    # * Drop "namespace" column
    # * "name" becomes decorative only, "label" will be sole mechanism for
    #   finding the proddef in the repository.
    if 'ProductVersions' not in db.tables:
        cu.execute("""
            CREATE TABLE ProductVersions (
                productVersionId    %(PRIMARYKEY)s,
                projectId       integer             NOT NULL
                    REFERENCES Projects ON DELETE CASCADE,
                label               text            NOT NULL    UNIQUE,
                cache_key           text,
                source_group        text,
                platform_id         integer
                    REFERENCES Platforms ON DELETE SET NULL,
                platform_label      text,
                namespace           varchar(16),
                name                varchar(16)     NOT NULL,
                description         text,
                timeCreated         numeric(14,3)
        ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['ProductVersions'] = []
    db.createIndex('ProductVersions', 'ProductVersions_uq',
            'projectId,namespace,name', unique=True)

    if 'project_branch_stage' not in db.tables:
        cu.execute("""
            CREATE TABLE "project_branch_stage" (
                "stage_id" %(PRIMARYKEY)s,
                "name" varchar(256) NOT NULL,
                "label" text NOT NULL,
                project_id          integer         NOT NULL
                    REFERENCES Projects (projectId)
                    ON DELETE CASCADE,
                project_branch_id   integer         NOT NULL
                    REFERENCES ProductVersions (productVersionId)
                    ON DELETE CASCADE,
                "promotable" bool,
                "created_date" timestamp with time zone NOT NULL
                    DEFAULT current_timestamp,
                UNIQUE ( project_branch_id, name )
            )""" % db.keywords)
        db.tables['project_branch_stage'] = []


def _createTargets(db):
    from mint import buildtypes
    cu = db.cursor()
    if 'target_types' not in db.tables:
        cu.execute("""
            CREATE TABLE target_types (
            target_type_id     %(PRIMARYKEY)s,
            name              TEXT NOT NULL UNIQUE,
            description       TEXT NOT NULL,
            -- For now, build_type_id is not an FK
            build_type_id     INTEGER NOT NULL,
            created_date      TIMESTAMP WITH TIME ZONE NOT NULL
                DEFAULT current_timestamp,
            modified_date     TIMESTAMP WITH TIME ZONE NOT NULL
                DEFAULT current_timestamp
            ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['target_types'] = []
        _addTableRows(db, 'target_types', 'name',
            [
                dict(name="ec2",
                    description="Amazon Elastic Compute Cloud",
                    build_type_id=buildtypes.AMI),
                dict(name="eucalyptus",
                    description="Eucalyptus",
                    build_type_id=buildtypes.RAW_FS_IMAGE),
                dict(name="openstack",
                    description="OpenStack",
                    build_type_id=buildtypes.RAW_HD_IMAGE),
                dict(name="vcloud",
                    description="VMware vCloud",
                    build_type_id=buildtypes.VMWARE_ESX_IMAGE),
                dict(name="vmware",
                    description="VMware ESX/vSphere",
                    build_type_id=buildtypes.VMWARE_ESX_IMAGE),
                dict(name="xen-enterprise",
                    description="Citrix Xen Server",
                    build_type_id=buildtypes.XEN_OVA),
            ])

    if 'Targets' not in db.tables:
        cu.execute("""
            CREATE TABLE Targets (
                targetId        %(PRIMARYKEY)s,
                target_type_id    integer            NOT NULL
                    REFERENCES target_types (target_type_id)
                    ON DELETE CASCADE,
                name              TEXT NOT NULL,
                description       TEXT NOT NULL,
                zone_id           integer NOT NULL
                    REFERENCES inventory_zone (zone_id)
                    ON DELETE CASCADE,
                created_date      TIMESTAMP WITH TIME ZONE NOT NULL
                    DEFAULT current_timestamp,
                modified_date     TIMESTAMP WITH TIME ZONE NOT NULL
                    DEFAULT current_timestamp
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['Targets'] = []
        db.createIndex('Targets',
            'Targets_Type_Name_Uq', 'target_type_id, name', unique=True)

    if 'TargetData' not in db.tables:
        cu.execute("""
            CREATE TABLE TargetData (
                targetdataId    %(PRIMARYKEY)s,
                targetId        integer             NOT NULL
                    REFERENCES Targets ON DELETE CASCADE,
                name            varchar(255)        NOT NULL,
                value           text
            ) %(TABLEOPTS)s """ % db.keywords)
        db.tables['TargetData'] = []
    db.createIndex('TargetData', 'TargetDataIdx',
            'targetId, name', unique=True)

    createTable(db, 'TargetCredentials', """
            CREATE TABLE TargetCredentials (
                targetCredentialsId     %(PRIMARYKEY)s,
                credentials             text NOT NULL UNIQUE
            ) %(TABLEOPTS)s""")

    createTable(db, 'TargetUserCredentials', """
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

    createTable(db, 'TargetImagesDeployed', """
            CREATE TABLE TargetImagesDeployed (
                id              %(PRIMARYKEY)s,
                targetId        integer             NOT NULL
                    REFERENCES Targets ON DELETE CASCADE,
                fileId          integer             NOT NULL
                    REFERENCES BuildFiles ON DELETE CASCADE,
                targetImageId   varchar(128)        NOT NULL
            ) %(TABLEOPTS)s""")

    createTable(db, 'target_image', """
            CREATE TABLE target_image (
                target_image_id         %(PRIMARYKEY)s,
                name                    TEXT NOT NULL,
                description             TEXT NOT NULL,
                target_id               integer             NOT NULL
                    REFERENCES Targets ON DELETE CASCADE,
                target_internal_id      TEXT             NOT NULL,
                rbuilder_image_id       TEXT,
                created_date            TIMESTAMP WITH TIME ZONE NOT NULL
                    DEFAULT current_timestamp,
                modified_date           TIMESTAMP WITH TIME ZONE NOT NULL
                    DEFAULT current_timestamp,
                UNIQUE ( target_id, target_internal_id )
            ) %(TABLEOPTS)s""")

    createTable(db, 'target_image_credentials', """
            CREATE TABLE target_image_credentials (
                id                      %(PRIMARYKEY)s,
                target_image_id         INTEGER NOT NULL
                    REFERENCES target_image ON DELETE CASCADE,
                target_credentials_id   INTEGER NOT NULL
                    REFERENCES TargetCredentials ON DELETE CASCADE
            ) %(TABLEOPTS)s""")

    createTable(db, 'target_deployable_image', """
                target_deployable_image_id %(PRIMARYKEY)s,
                target_id               integer             NOT NULL
                    REFERENCES Targets ON DELETE CASCADE,
                target_image_id         INTEGER
                    REFERENCES target_image ON DELETE CASCADE,
                file_id                 integer NOT NULL
                    REFERENCES BuildFiles ON DELETE CASCADE,
            """)

def _createPlatforms(db):
    cu = db.cursor()

    if 'Platforms' not in db.tables:
        cu.execute("""
            CREATE TABLE Platforms (
                platformId  %(PRIMARYKEY)s,
                label       varchar(255)    NOT NULL UNIQUE,
                mode varchar(255) NOT NULL DEFAULT 'manual'
                    CHECK (mode in ('auto', 'manual')),
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

    if 'PlatformsContentSourceTypes' not in db.tables:
        cu.execute("""
            CREATE TABLE PlatformsContentSourceTypes (
                contentSourceTypeId %(PRIMARYKEY)s,
                platformId  integer NOT NULL
                    REFERENCES platforms ON DELETE CASCADE,
                contentSourceType  varchar(255) NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['PlatformsContentSourceTypes'] = []
    db.createIndex('PlatformsContentSourceTypes',
            'PlatformsContentSourceTypes_platformId_contentSourceType_uq',
            'platformId,contentSourceType', unique=True)

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
    db.createIndex('PlatformSources',
            'PlatformSources_platformSourceId_defaultSource_uq',
            'platformSourceId,defaultSource', unique=True)
    db.createIndex('PlatformSources',
            'PlatformSources_platformSourceId_orderIndex_uq',
            'platformSourceId,orderIndex', unique=True)

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

    if 'PlatformsPlatformSources' not in db.tables:
        cu.execute("""
            CREATE TABLE PlatformsPlatformSources (
                platforms_platform_sources_id  %(PRIMARYKEY)s,
                platformId          integer         NOT NULL
                    REFERENCES platforms ON DELETE CASCADE,
                platformSourceId    integer         NOT NULL
                    REFERENCES platformSources ON DELETE CASCADE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['PlatformsPlatformSources'] = []


def _createCapsuleIndexerSchema(db):
    # Even though sqlalchemy is perfectly capable of creating the schema, we
    # will create it by hand instead. The main reason is that sqlite will get
    # upset if schema changes underneath an open connection.
    cu = db.cursor()

    tableName = 'ci_rhn_channels'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE ci_rhn_channels (
                channel_id %(PRIMARYKEY)s,
                label VARCHAR(256) NOT NULL,
                last_modified VARCHAR
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
    db.createIndex('ci_rhn_channels',
        'ci_rhn_channels_label_idx_uq', 'label', unique=True)

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
    db.createIndex('ci_rhn_nevra',
        'ci_rhn_nevra_n_e_v_r_a_idx_uq', 'name, epoch, version, release, arch',
        unique=True)

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
    db.createIndex('ci_rhn_packages',
        'ci_rhn_packages_nevra_id_last_modified_idx_uq',
        'nevra_id, last_modified', unique=True)
    db.createIndex('ci_rhn_packages',
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
    db.createIndex('ci_rhn_channel_package',
        'ci_rhn_channel_package_cid_pid_idx_uq', 'channel_id, package_id',
        unique=True)
    db.createIndex('ci_rhn_channel_package',
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
    db.createIndex('ci_rhn_errata_channel',
        'ci_rhn_errata_channel_eid_cid_idx_uq', 'errata_id, channel_id',
        unique=True)
    db.createIndex('ci_rhn_errata_channel',
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


def _createCapsuleIndexerYumSchema(db):
    cu = db.cursor()

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
    db.createIndex('ci_yum_repositories',
        'ci_yum_repositories_label_idx_uq', 'label', unique=True)

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
    db.createIndex('ci_yum_packages',
        'ci_yum_packages_nevra_id_checksum_idx_uq',
        'nevra_id, checksum, checksum_type', unique=True)

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


def _createRepositoryLogSchema(db):
    # Repository Log scraping table and the status table for th scraper
    cu = db.cursor()

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
    db.createIndex('systemupdate',
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


def _createZoneSchema(db):
    cu = db.cursor()

    # XXX this table should no longer be prefixed with inventory_
    if 'inventory_zone' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_zone" (
                "zone_id" %(PRIMARYKEY)s,
                "name" varchar(8092) NOT NULL UNIQUE,
                "description" varchar(8092),
                "created_date" timestamp with time zone NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_zone'] = []


def _createInventorySchema(db, cfg):
    cu = db.cursor()

    if 'inventory_system_state' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_system_state" (
                "system_state_id" %(PRIMARYKEY)s,
                "name" varchar(8092) NOT NULL UNIQUE,
                "description" varchar(8092) NOT NULL,
                "created_date" timestamp with time zone NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_system_state'] = []
        _addSystemStates(db, cfg)

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
        _addManagementInterfaces(db)

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
        _addSystemTypes(db)

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
                "launching_user_id" integer
                    REFERENCES "users" ("userid")
                    ON DELETE SET NULL,
                "current_state_id" integer NOT NULL
                    REFERENCES "inventory_system_state" ("system_state_id"),
                "managing_zone_id" integer NOT NULL
                    REFERENCES "inventory_zone" ("zone_id"),
                "management_interface_id" integer
                    REFERENCES "inventory_management_interface"
                        ("management_interface_id"),
                "system_type_id" integer
                    REFERENCES "inventory_system_type" ("system_type_id"),
                "credentials" text,
                "configuration" text,
                "stage_id" integer
                    REFERENCES "project_branch_stage" ("stage_id")
                    ON DELETE SET NULL,
                "major_version_id" integer
                    REFERENCES ProductVersions (productVersionId)
                    ON DELETE SET NULL,
                "project_id" integer
                    REFERENCES Projects (projectId)
                    ON DELETE SET NULL,
                "should_migrate" BOOLEAN NOT NULL
                    DEFAULT FALSE, 
                "source_image_id" INTEGER 
                    REFERENCES "builds" ("buildid")
                    ON DELETE CASCADE,
                "created_by" integer
                    REFERENCES "users" ("userid")
                    ON DELETE SET NULL,
                "modified_by" integer
                    REFERENCES "users" ("userid")
                    ON DELETE SET NULL,
                "modified_date" TIMESTAMP WITH TIME ZONE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_system'] = []
        db.createIndex("inventory_system",
            "inventory_system_target_id_idx", "target_id")

    if 'inventory_zone_management_node' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_zone_management_node" (
                "system_ptr_id" integer NOT NULL PRIMARY KEY
                    REFERENCES "inventory_system" ("system_id")
                    ON DELETE CASCADE,
                "local" bool,
                "zone_id" integer NOT NULL
                    REFERENCES "inventory_zone" ("zone_id"),
                "node_jid" varchar(64)
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_zone_management_node'] = []

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
        db.createIndex("inventory_system_network",
            "inventory_system_network_system_id_idx", "system_id")
        db.createIndex("inventory_system_network",
            "inventory_system_network_dns_name_idx", "dns_name")

    # add local management zone.  must be done after inventory_system and
    # inventory_system_network are added
    _addManagementZone(db, cfg)

    if 'inventory_system_log' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_system_log" (
                "system_log_id" %(PRIMARYKEY)s,
                "system_id" integer NOT NULL
                    REFERENCES "inventory_system" ("system_id")
                    ON DELETE CASCADE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_system_log'] = []
        db.createIndex("inventory_system_log",
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

    tableName = 'jobs_job_type'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE "jobs_job_type" (
                "job_type_id" %(PRIMARYKEY)s,
                "name" varchar(8092) NOT NULL UNIQUE,
                "description" varchar(8092) NOT NULL,
                "priority" smallint NOT NULL,
                "resource_type" text NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []
        _addTableRows(db, tableName, 'name',
            [dict(name="system registration",
                  description='System registration',
                  # registration events are no longer dispatched immediately
                  # (RBL-8851)
                  priority=70,
                  resource_type='System'),
             dict(name="system poll",
                  description='System synchronization',
                  priority=50,
                  resource_type='System'),
             dict(name="immediate system poll",
                  description='On-demand system synchronization',
                  priority=105,
                  resource_type='System'),
             dict(name="system apply update",
                  description='Scheduled system update',
                  priority=50,
                  resource_type='System'),
             dict(name="immediate system apply update",
                  description='System update',
                  priority=105,
                  resource_type='System'),
             dict(name="system shutdown",
                  description='Scheduled system shutdown',
                  priority=50,
                  resource_type='System'),
             dict(name="immediate system shutdown",
                  description='System shutdown',
                  priority=105,
                  resource_type='System'),
             dict(name='system launch wait',
                  description='Launched system network data discovery',
                  priority=105,
                  resource_type='System'),
             dict(name="system detect management interface",
                  description="System management interface detection",
                  priority=50,
                  resource_type='System'),
             dict(name="immediate system detect management interface",
                  description="On-demand system management "
                        "interface detection",
                  priority=105,
                  resource_type="System"),
             dict(name="immediate system configuration",
                  description="Update system configuration",
                  priority=105,
                  resource_type="System"),
             dict(name="system assimilation",
                  description="System assimilation",
                  priority=105,
                  resource_type="System"),
             dict(name="image builds",
                  description="Image builds",
                  priority=105,
                  resource_type="Image"),
             dict(name="refresh queryset",
                  description="Refresh queryset",
                  priority=105,
                  resource_type="QuerySet"),
             dict(name="refresh target images",
                  description="Refresh target images",
                  priority=105,
                  resource_type="Target"),
             dict(name="refresh target systems",
                  description="Refresh target systems",
                  priority=105,
                  resource_type="Target"),
             dict(name="deploy image on target",
                  description="Deploy image on target",
                  priority=105,
                  resource_type="Target"),
             dict(name="launch system on target",
                  description="Launch system on target",
                  priority=105,
                  resource_type="Target"),
             dict(name="create target",
                  description="Create target",
                  priority=105,
                  resource_type="TargetType"),
             dict(name="configure target credentials",
                  description="Configure target credentials for the current user",
                  priority=105,
                  resource_type="Target"),
             dict(name="system capture",
                  description="Capture a system's image",
                  priority=105,
                  resource_type="System"),
            ])

    if 'inventory_system_event' not in db.tables:
        cu.execute("""
            CREATE TABLE "inventory_system_event" (
                "system_event_id" %(PRIMARYKEY)s,
                "system_id" integer NOT NULL
                    REFERENCES "inventory_system" ("system_id")
                    ON DELETE CASCADE,
                "job_type_id" integer NOT NULL
                    REFERENCES "jobs_job_type",
                "time_created" timestamp with time zone NOT NULL,
                "time_enabled" timestamp with time zone NOT NULL,
                "priority" smallint NOT NULL,
                "event_data" varchar
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['inventory_system_event'] = []
        db.createIndex("inventory_system_event",
            "inventory_system_event_system_id", "system_id")
        db.createIndex("inventory_system_event",
            "inventory_system_event_event_type_id", "job_type_id")
        db.createIndex("inventory_system_event",
            "inventory_system_event_time_enabled", "time_enabled")
        db.createIndex("inventory_system_event",
            "inventory_system_event_priority", "priority")

    if 'jobs_job_state' not in db.tables:
        cu.execute("""
            CREATE TABLE jobs_job_state
            (
                job_state_id %(PRIMARYKEY)s,
                name VARCHAR NOT NULL UNIQUE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['jobs_job_state'] = []
    _addTableRows(db, 'jobs_job_state', 'name',
        [
            dict(name='Queued'), dict(name='Running'),
            dict(name='Completed'), dict(name='Failed'), ])

    tableName = 'jobs_job'
    if tableName not in db.tables:
        cu.execute("""
            CREATE TABLE jobs_job (
                job_id %(PRIMARYKEY)s,
                job_uuid varchar(64) NOT NULL UNIQUE,
                job_token varchar(64) UNIQUE,
                job_state_id integer NOT NULL
                    REFERENCES jobs_job_state,
                job_type_id integer NOT NULL
                    REFERENCES jobs_job_type,
                descriptor VARCHAR,
                descriptor_data VARCHAR,
                status_code INTEGER NOT NULL DEFAULT 100,
                status_text VARCHAR NOT NULL DEFAULT 'Initializing',
                status_detail VARCHAR,
                created_by   INTEGER
                    REFERENCES Users ON DELETE SET NULL,
                time_created timestamp with time zone NOT NULL,
                time_updated timestamp with time zone NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []

    createTable(db, 'jobs_job_result', """
        CREATE TABLE jobs_job_result (
            job_result_id %(PRIMARYKEY)s,
            job_id          INTEGER NOT NULL
                REFERENCES jobs_job ON DELETE CASCADE,
            data            TEXT NOT NULL
        ) %(TABLEOPTS)s""")

    createTable(db, 'jobs_job_history', """
        CREATE TABLE jobs_job_history
        (
            job_history_id  %(PRIMARYKEY)s,
            job_id          INTEGER NOT NULL
                REFERENCES jobs_job ON DELETE CASCADE,
            content         TEXT NOT NULL,
            created_date    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp
        ) %(TABLEOPTS)s""")

    tableName = "inventory_system_job"
    if 'inventory_system_job' not in db.tables:
        # The same job cannot be attached to multiple systems
        # This may change in the future
        cu.execute("""
            CREATE TABLE inventory_system_job (
                system_job_id %(PRIMARYKEY)s,
                job_id integer NOT NULL UNIQUE
                    REFERENCES jobs_job
                    ON DELETE CASCADE,
                system_id integer NOT NULL
                    REFERENCES inventory_system
                    ON DELETE CASCADE,
                event_uuid varchar(64) NOT NULL UNIQUE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables[tableName] = []

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
            )""" % db.keywords)

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

    if 'django_site' not in db.tables:
        cu.execute("""
            CREATE TABLE "django_site" (
                "id" %(PRIMARYKEY)s,
                "domain" VARCHAR(100) NOT NULL UNIQUE,
                "name" VARCHAR(100) NOT NULL UNIQUE
            )""" % db.keywords)
        db.tables['django_site'] = []
        _addTableRows(db, 'django_site', 'name', [
                dict(id=1, domain="rbuilder.inventory",
                    name="rBuilder Inventory"),
                ])

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


def _addSystemStates(db, cfg):
    _addTableRows(db, 'inventory_system_state', 'name', [
        dict(name="unmanaged", description="Unmanaged",
            created_date=str(datetime.datetime.now(tz.tzutc()))),
        dict(name="unmanaged-credentials",
            description="Unmanaged: Invalid credentials",
            created_date=str(datetime.datetime.now(tz.tzutc()))),
        dict(name="registered", description="Initial synchronization pending",
            created_date=str(datetime.datetime.now(tz.tzutc()))),
        dict(name="responsive", description="Online",
            created_date=str(datetime.datetime.now(tz.tzutc()))),
        dict(name="non-responsive-unknown",
            description="Not responding: Unknown",
            created_date=str(datetime.datetime.now(tz.tzutc()))),
        dict(name="non-responsive-net",
            description="Not responding: Network unreachable",
            created_date=str(datetime.datetime.now(tz.tzutc()))),
        dict(name="non-responsive-host",
            description="Not responding: Host unreachable",
            created_date=str(datetime.datetime.now(tz.tzutc()))),
        dict(name="non-responsive-shutdown",
            description="Not responding: Shutdown",
            created_date=str(datetime.datetime.now(tz.tzutc()))),
        dict(name="non-responsive-suspended",
            description="Not responding: Suspended",
            created_date=str(datetime.datetime.now(tz.tzutc()))),
        dict(name="non-responsive-credentials",
            description="Not responding: Invalid credentials",
            created_date=str(datetime.datetime.now(tz.tzutc()))),
        dict(name="dead", description="Stale",
            created_date=str(datetime.datetime.now(tz.tzutc()))),
        dict(name="mothballed", description="Retired",
            created_date=str(datetime.datetime.now(tz.tzutc()))),
        ])


def _addManagementZone(db, cfg):

    # add the zone
    zoneName = "Local rBuilder"
    zoneDescription = 'Local rBuilder management zone'
    _addTableRows(db, 'inventory_zone', 'name',
            [dict(name=zoneName,
                  description=zoneDescription,
                  created_date=str(datetime.datetime.now(tz.tzutc())))])


cim_credentials_descriptor = r"""<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd">
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

wmi_credentials_descriptor = r"""<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd">
  <metadata></metadata>
  <dataFields>
    <field><name>domain</name>
      <descriptions>
        <desc>Windows Domain</desc>
      </descriptions>
      <type>str</type>
      <default></default>
      <required>false</required>
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

ssh_credentials_descriptor = r"""<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd">
  <metadata></metadata>
  <dataFields>
    <field><name>key</name>
      <descriptions>
        <desc>SSH private key</desc>
      </descriptions>
      <type>str</type>
      <default></default>
      <required>false</required>
    </field>
    <field>
      <name>password</name>
      <descriptions>
        <desc>SSH key unlock or root password</desc>
      </descriptions>
      <password>true</password>
      <type>str</type>
      <default></default>
      <required>false</required>
    </field>
  </dataFields>
</descriptor>"""


def _addManagementInterfaces(db):

    _addTableRows(db, 'inventory_management_interface', 'name',
            [dict(name='cim',
                  description='Common Information Model (CIM)',
                  port=5989,
                  created_date=str(datetime.datetime.now(tz.tzutc())),
                  credentials_descriptor=cim_credentials_descriptor,
                  credentials_readonly=True
            )])

    _addTableRows(db, 'inventory_management_interface', 'name',
            [dict(name='wmi',
                  description='Windows Management Instrumentation (WMI)',
                  port=135,
                  created_date=str(datetime.datetime.now(tz.tzutc())),
                  credentials_descriptor=wmi_credentials_descriptor,
                  credentials_readonly=False
            )])

    _addTableRows(db, 'inventory_management_interface', 'name',
            [dict(name='ssh',
                  description='Secure Shell (SSH)',
                  port=22,
                  created_date=str(datetime.datetime.now(tz.tzutc())),
                  credentials_descriptor=ssh_credentials_descriptor,
                  credentials_readonly=False
            )])


inventory_creation_descriptor = r"""<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd"> 
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

management_node_creation_descriptor = r"""<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd"> 
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

windows_build_node_creation_descriptor = r"""<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd"> 
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

    _addTableRows(db, 'inventory_system_type', 'name',
            [dict(name='inventory',
                  description='Inventory',
                  created_date=str(datetime.datetime.now(tz.tzutc())),
                  infrastructure=False,
                  creation_descriptor=inventory_creation_descriptor
            )])

    _addTableRows(db, 'inventory_system_type', 'name',
            [dict(name='infrastructure-management-node',
                  description='rPath Update Service (Infrastructure)',
                  created_date=str(datetime.datetime.now(tz.tzutc())),
                  infrastructure=True,
                  creation_descriptor=management_node_creation_descriptor
            )])

    _addTableRows(db, 'inventory_system_type', 'name',
            [dict(name='infrastructure-windows-build-node',
                  description='rPath Windows Build Service (Infrastructure)',
                  created_date=str(datetime.datetime.now(tz.tzutc())),
                  infrastructure=True,
                  creation_descriptor=windows_build_node_creation_descriptor
            )])


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

    if 'job_types' not in db.tables:
        cu.execute("""
            CREATE TABLE job_types
            (
                job_type_id %(PRIMARYKEY)s,
                name VARCHAR NOT NULL UNIQUE,
                description VARCHAR NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['job_types'] = []
    _addTableRows(db, 'job_types', 'name', [
        dict(name="instance-launch", description='Instance Launch'),
        dict(name="platform-load", description='Platform Load'),
        dict(name="software-version-refresh",
            description='Software Version Refresh'),
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
    _addTableRows(db, 'job_states', 'name', [
        dict(name='Queued'), dict(name='Running'),
        dict(name='Completed'), dict(name='Failed'),
        ])

    if 'rest_methods' not in db.tables:
        cu.execute("""
            CREATE TABLE rest_methods
            (
                rest_method_id %(PRIMARYKEY)s,
                name VARCHAR NOT NULL UNIQUE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['rest_methods'] = []
    _addTableRows(db, 'rest_methods', 'name', [
        dict(name='POST'), dict(name='PUT'), dict(name='DELETE'),
        ])

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


def _createPKI(db):
    """Public key infrastructure tables"""

    createTable(db, 'pki_certificates', """
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


def _addQuerySet(db, name, description, resource_type, can_modify,
        filter_id=None, presentation_type=None, public=False,
        static=False, version=None):
    """Add a new query set"""

    if presentation_type is None:
        presentation_type = resource_type

    # add the query set
    options = dict(name=name, resource_type=resource_type,
            description=description,
            created_date=str(datetime.datetime.now(tz.tzutc())),
            modified_date=str(datetime.datetime.now(tz.tzutc())),
            presentation_type=presentation_type,
            can_modify=can_modify,
    )

    # various prior migrations didn't bother to fork this method
    # so this is how we're handling it to avoid a lot of method
    # cloning.. don't send all options to older migrations because
    # those columns aren't added yet

    if not version or version >= (59, 0):
        options['is_public'] = public
    if not version or version >= (59, 4):
        options['is_static'] = static
 
    _addTableRows(db, "querysets_queryset", "name", [options])    

    # add the query tag
    qsId = _getRowPk(db, "querysets_queryset", "query_set_id",
        name=name)

    if filter_id:
        # link the query set to the filter
        _addTableRows(db, "querysets_queryset_filter_entries", 'id',
            [dict(queryset_id=qsId, filterentry_id=filter_id)],
            ['queryset_id', 'filterentry_id'])

    return qsId


def _addQuerySetFilterEntry(db, field, operator, value):
    """Add a filter entry to be used by query sets"""

    _addTableRows(db, "querysets_filterentry", "filter_entry_id",
        [dict(field=field, operator=operator, value=value)],
        ['field', 'operator', 'value'])

    filterId = _getRowPk(db, "querysets_filterentry", 'filter_entry_id',
        field=field, operator=operator, value=value)

    return filterId


def _addQuerySetChild(db, parent_qs_id, child_qs_id):
    """Add a query set to another as a child"""

    _addTableRows(db, "querysets_queryset_children",
        'id',
        [dict(from_queryset_id=parent_qs_id, to_queryset_id=child_qs_id)],
        uniqueCols=('from_queryset_id', 'to_queryset_id'))


def _addQuerySetChildToInfrastructureSystems(db, child_qs_id):
    """Convenience method to add a child query set to infrastructure systems"""

    qsId = _getRowPk(db, "querysets_queryset", "query_set_id",
        name="Infrastructure Systems")
    return _addQuerySetChild(db, qsId, child_qs_id)


def _createInfrastructureSystemsQuerySetSchema(db, version=None):
    """Add the infrastructure systems query set"""
    filterId = _addQuerySetFilterEntry(db, "system_type.infrastructure",
            "EQUAL", "true")
    _addQuerySet(db, "Infrastructure Systems",
            "Systems that make up the rPath infrastructure", "system",
            False, filterId, version=version)
    return True


def _createWindowsBuildSystemsQuerySet(db, version=None):
    """Add the windows build systems query set"""
    filterId = _addQuerySetFilterEntry(db, "system_type.name", "EQUAL",
            "infrastructure-windows-build-node")
    qsId = _addQuerySet(db, "rPath Windows Build Services",
            "rPath infrastructure services for "
            "building Windows packages/images", "system", False, filterId,
            version=version)
    _addQuerySetChildToInfrastructureSystems(db, qsId)
    return True


def _createUpdateSystemsQuerySet(db, version=None):
    """Add the windows build systems query set"""
    filterId = _addQuerySetFilterEntry(db, "system_type.name", "EQUAL",
            "infrastructure-management-node")
    qsId = _addQuerySet(db, "rPath Update Services",
            "rPath infrastructure services for managing systems",
            "system", False, filterId, version=version)
    _addQuerySetChildToInfrastructureSystems(db, qsId)
    return True


def _createAllProjectBranchStages13(db, version=None):
    """Add the project branch stages query set"""

    # do not change this, froxen to migrate13
    # (NOTE -- this value will NOT be in the final result schema and is wrong!)
    filterId = _addQuerySetFilterEntry(db, "name", "IS_NULL", "False")
    _addQuerySet(db, "All Projects", "All projects",
            "project_branch_stage", False, filterId, "project", public=True,
             version=(58,13))
    return True


def _createAllProjectBranchStages(db, version=None):
    """Add the project branch stages query set"""
    filterId = _addQuerySetFilterEntry(db, "project_branch_stage.name",
            "IS_NULL", "false")
    _addQuerySet(db, "All Project Stages", "All project stages",
            "project_branch_stage", False, filterId, "project", public=True,
            version=version)
    return True


def _createAllProjects(db, version=None):
    """Add the projects query set"""
    # filterId = _getAllFilterId(db)
    filterId = _addQuerySetFilterEntry(db, "project.name", "IS_NULL", "false")
    _addQuerySet(db, "All Projects", "All projects", "project", False,
            filterId, public=True, version=version)
    return True

def _createAllUsers(db, version=None):
    """Add the all users query set"""
    filterId = _addQuerySetFilterEntry(db, "name", "IS_NULL", "false")
    _addQuerySet(db, "All Users", "All users", "user", False,
            filterId, public=True, version=version)
    return True

def _createAllSystems(db, version=None):
    """Add the all systems query set"""
    filterId = _addQuerySetFilterEntry(db, "system.name", "IS_NULL", "false")
    _addQuerySet(db, "All Systems", "All systems", "system", False,
            filterId, public=True, version=version)
    return True

def _createAllTargets(db, version=None):
    """Add the all targets query set"""
    filterId = _addQuerySetFilterEntry(db, "target.name", "IS_NULL", "false")
    _addQuerySet(db, "All Targets", "All targets", "target", False,
            filterId, public=True, version=version)
    return True


def _createAllRoles(db, version=None):
    """Add the all roles query set"""
    filterId = _addQuerySetFilterEntry(db, "rbac_role.role_id", "IS_NULL",
            "false")
    _addQuerySet(db, "All Roles", "All roles", "role", False, filterId,
            'rbac', version=version)
    return True

def _createNonIdentityRoles(db, version=None):
    '''all roles that are intended for multiple users'''
    filterId = _addQuerySetFilterEntry(db, "rbac_role.is_identity", "EQUAL", "false")
    _addQuerySet(db, "All Non-Identity Roles", "All non-identity roles", "role", False, filterId,
            'rbac', version=version)
    return True

def _createAllGrants(db, version=None):
    """Add the all systems query set"""
    filterId = _addQuerySetFilterEntry(db, "rbac_permission.permission_id",
            "IS_NULL", "false")
    _addQuerySet(db, "All Grants", "All grants", "grant", False,
            filterId, 'rbac', version=version)
    return True

def _createAllImages(db, version=None):
    """Add the all images query set"""
    filterId = _addQuerySetFilterEntry(db, "image.image_id",
            "IS_NULL", "false")
    _addQuerySet(db, "All Images", "All images", "image", False,
            filterId, 'image', public=True, version=version)
    return True


def _createQuerySetSchema(db):
    """QuerySet tables"""

    createTable(db, 'querysets_queryset', """
        CREATE TABLE "querysets_queryset" (
            "query_set_id" %(PRIMARYKEY)s,
            "name" TEXT NOT NULL UNIQUE,
            "description" TEXT,
            "created_date" TIMESTAMP WITH TIME ZONE NOT NULL,
            "modified_date" TIMESTAMP WITH TIME ZONE NOT NULL,
            "tagged_date" TIMESTAMP WITH TIME ZONE,
            "resource_type" TEXT NOT NULL,
            "presentation_type" TEXT,
            "can_modify" BOOLEAN NOT NULL DEFAULT TRUE,
            "is_public" BOOLEAN NOT NULL DEFAULT FALSE,
            "is_static" BOOLEAN NOT NULL DEFAULT FALSE,
            "created_by" INTEGER
                REFERENCES Users ON DELETE SET NULL,
            "modified_by" INTEGER
                REFERENCES Users ON DELETE SET NULL,
            "personal_for" INTEGER
                REFERENCES Users ON DELETE SET NULL
        )""")

    createTable(db, 'querysets_filterentry', """
        CREATE TABLE "querysets_filterentry" (
            "filter_entry_id" %(PRIMARYKEY)s,
            "field" TEXT NOT NULL,
            "operator" TEXT NOT NULL,
            "value" TEXT,
            UNIQUE("field", "operator", "value")
        )""")

    createTable(db, "querysets_queryset_filter_entries", """
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

    # unique value was 'name', not queryset_id
    qs_rows=[
         dict(name="Active Systems", resource_type="system",
            description="Active Systems",
            created_date=str(datetime.datetime.now(tz.tzutc())),
            modified_date=str(datetime.datetime.now(tz.tzutc())),
            can_modify=False,
            presentation_type='system',
         ),
         dict(name="Inactive Systems", resource_type="system",
            description="Inactive Systems",
            created_date=str(datetime.datetime.now(tz.tzutc())),
            modified_date=str(datetime.datetime.now(tz.tzutc())),
            can_modify=False,
            presentation_type='system'
         ),
         dict(name="Physical Systems", resource_type="system",
            description="Physical Systems",
            created_date=str(datetime.datetime.now(tz.tzutc())),
            modified_date=str(datetime.datetime.now(tz.tzutc())),
            can_modify=False,
            presentation_type='system'
         ),
    ]
    _addTableRows(db, "querysets_queryset", "name", qs_rows)

    _createAllUsers(db)
    _createAllSystems(db)

    allQSId = _getRowPk(db, "querysets_queryset", "query_set_id",
        name="All Systems")
    activeQSId = _getRowPk(db, "querysets_queryset", "query_set_id",
        name="Active Systems")
    inactiveQSId = _getRowPk(db, "querysets_queryset", "query_set_id",
        name="Inactive Systems")
    physicalQSId = _getRowPk(db, "querysets_queryset", "query_set_id",
        name="Physical Systems")
    allUserQSId = _getRowPk(db, "querysets_queryset", "query_set_id",
        name="All Users")

    _addTableRows(db, "querysets_filterentry",
        'filter_entry_id',
        [dict(field="current_state.name", operator="EQUAL",
            value="responsive"),
         dict(field="current_state.name", operator="IN",
            value='(unmanaged,unmanaged-credentials,registered,'
                'non-responsive-unknown,non-responsive-net,'
                'non-responsive-host,non-responsive-shutdown,'
                'non-responsive-suspended,non-responsive-credentials)'),
         dict(field="target", operator='IS_NULL', value="True"),
         dict(field='user_name', operator='IS_NULL', value="False"),
         ],
        ['field', 'operator', 'value'])

    activeFiltId = _getRowPk(db, "querysets_filterentry", 'filter_entry_id',
        field="current_state.name", operator="EQUAL", value="responsive")

    inactiveFiltId = _getRowPk(db, "querysets_filterentry", 'filter_entry_id',
        field="current_state.name", operator="IN",
        value='(unmanaged,unmanaged-credentials,registered,'
            'non-responsive-unknown,non-responsive-net,non-responsive-host,'
            'non-responsive-shutdown,non-responsive-suspended,'
            'non-responsive-credentials)')

    physicalFiltId = _getRowPk(db, "querysets_filterentry", 'filter_entry_id',
        field="target", operator='IS_NULL', value="True")

    allUserFiltId = _getRowPk(db, "querysets_filterentry", 'filter_entry_id',
        field="user_name", operator='IS_NULL', value="False")

    createTable(db, 'querysets_inclusionmethod', """
        CREATE TABLE "querysets_inclusionmethod" (
            "inclusion_method_id" %(PRIMARYKEY)s,
            "name" TEXT NOT NULL UNIQUE
        )""")
    _addTableRows(db, "querysets_inclusionmethod",
        "name",
        [dict(name="chosen"),
         dict(name="filtered"),
         dict(name="transitive")])

    createTable(db, 'querysets_systemtag', """
        CREATE TABLE "querysets_systemtag" (
            "system_tag_id" %(BIGPRIMARYKEY)s,
            "system_id" INTEGER
                REFERENCES "inventory_system" ("system_id")
                ON DELETE CASCADE
                NOT NULL,
            "query_set_id" INTEGER
                REFERENCES "querysets_queryset" ("query_set_id")
                ON DELETE CASCADE,
            "inclusion_method_id" INTEGER
                REFERENCES "querysets_inclusionmethod" ("inclusion_method_id")
                ON DELETE CASCADE
                NOT NULL,
            CONSTRAINT querysets_systemtag_uq UNIQUE ("system_id",
                "query_set_id", "inclusion_method_id")
        )""")

    createTable(db, 'querysets_usertag', """
        CREATE TABLE "querysets_usertag" (
            "user_tag_id" %(BIGPRIMARYKEY)s,
            "user_id" INTEGER
                REFERENCES "users" ("userid")
                ON DELETE CASCADE
                NOT NULL,
            "query_set_id" INTEGER
                REFERENCES "querysets_queryset" ("query_set_id")
                ON DELETE CASCADE,
            "inclusion_method_id" INTEGER
                REFERENCES "querysets_inclusionmethod" ("inclusion_method_id")
                ON DELETE CASCADE
                NOT NULL,
            CONSTRAINT querysets_usertag_uq UNIQUE ("user_id", "query_set_id",
                "inclusion_method_id")
        )""")

    createTable(db, 'querysets_projecttag', """
        CREATE TABLE "querysets_projecttag" (
            "project_tag_id" %(BIGPRIMARYKEY)s,
            "project_id" INTEGER
                REFERENCES "projects" ("projectid")
                ON DELETE CASCADE
                NOT NULL,
            "query_set_id" INTEGER
                REFERENCES "querysets_queryset" ("query_set_id")
                ON DELETE CASCADE,
            "inclusion_method_id" INTEGER
                REFERENCES "querysets_inclusionmethod" ("inclusion_method_id")
                ON DELETE CASCADE
                NOT NULL,
            CONSTRAINT querysets_projecttag_uq UNIQUE ("project_id",
                "query_set_id", "inclusion_method_id")
        )""")

    createTable(db, 'querysets_stagetag', """
        CREATE TABLE "querysets_stagetag" (
            "stage_tag_id" %(BIGPRIMARYKEY)s,
            "stage_id" INTEGER
                REFERENCES "project_branch_stage" ("stage_id")
                ON DELETE CASCADE
                NOT NULL,
            "query_set_id" INTEGER
                REFERENCES "querysets_queryset" ("query_set_id")
                ON DELETE CASCADE,
            "inclusion_method_id" INTEGER
                REFERENCES "querysets_inclusionmethod" ("inclusion_method_id")
                ON DELETE CASCADE
                NOT NULL,
            CONSTRAINT querysets_stagetag_uq UNIQUE ("stage_id",
                "query_set_id", "inclusion_method_id")
        )""")

    createTable(db, 'querysets_targettag', """
        CREATE TABLE "querysets_targettag" (
            "target_tag_id" %(BIGPRIMARYKEY)s,
            "target_id" INTEGER
                REFERENCES "targets" ("targetid")
                ON DELETE CASCADE
                NOT NULL,
            "query_set_id" INTEGER
                REFERENCES "querysets_queryset" ("query_set_id")
                ON DELETE CASCADE,
            "inclusion_method_id" INTEGER
                REFERENCES "querysets_inclusionmethod" ("inclusion_method_id")
                ON DELETE CASCADE
                NOT NULL,
            CONSTRAINT querysets_targettag_uq UNIQUE ("target_id", "query_set_id",
                "inclusion_method_id")
        )""")

    _addTableRows(db, "querysets_queryset_filter_entries",
        'id',
        [dict(queryset_id=activeQSId, filterentry_id=activeFiltId),
         dict(queryset_id=inactiveQSId, filterentry_id=inactiveFiltId),
         dict(queryset_id=physicalQSId, filterentry_id=physicalFiltId),
         dict(queryset_id=allUserQSId, filterentry_id=allUserFiltId),
         ],
        ['queryset_id', 'filterentry_id'])

    createTable(db, "querysets_queryset_children", """
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


def _createChangeLogSchema(db):
    """ChangeLog tables"""

    createTable(db, 'changelog_change_log', """
        CREATE TABLE "changelog_change_log" (
            "change_log_id" %(PRIMARYKEY)s,
            "resource_type" TEXT NOT NULL,
            "resource_id" INTEGER NOT NULL
        )""")

    createTable(db, 'changelog_change_log_entry', """
        CREATE TABLE "changelog_change_log_entry" (
            "change_log_entry_id" %(PRIMARYKEY)s,
            "change_log_id" INTEGER
                REFERENCES "changelog_change_log" ("change_log_id")
                ON DELETE CASCADE NOT NULL,
            "entry_text" TEXT NOT NULL,
            "entry_date" TIMESTAMP WITH TIME ZONE NOT NULL
        )""")


def _createDjangoSchema(db):
    # before edge, django would just go out by itself to create its
    # tables.
    # we need to do it here. There is no migration needed for old
    # schema versions.
    createTable(db, 'django_content_type', """
        CREATE TABLE django_content_type (
            id          %(PRIMARYKEY)s,
            name        VARCHAR(100) NOT NULL,
            app_label   VARCHAR(100) NOT NULL,
            model       VARCHAR(100) NOT NULL
        )""")
    createTable(db, 'django_site', """
        CREATE TABLE django_site (
            id          %(PRIMARYKEY)s,
            domain      VARCHAR(100) NOT NULL,
            name        VARCHAR(100) NOT NULL
    )""")
    createTable(db, 'django_session', """
        CREATE TABLE django_session (
            session_key VARCHAR(40) NOT NULL PRIMARY KEY,
            session_data    TEXT NOT NULL,
            expire_date TIMESTAMP WITH TIME ZONE NOT NULL
    )""")
    createTable(db, 'django_redirect', """
        CREATE TABLE django_redirect (
            id          %(PRIMARYKEY)s,
            site_id     INTEGER NOT NULL
                        REFERENCES django_site(id),
            old_path    VARCHAR(200) NOT NULL,
            new_path    VARCHAR(200) NOT NULL
    )""")
    createTable(db, 'auth_permission', """
        CREATE TABLE auth_permission (
            id          %(PRIMARYKEY)s,
            name        VARCHAR(50) NOT NULL,
            content_type_id INTEGER NOT NULL
                        REFERENCES django_content_type(id),
            codename    VARCHAR(100) NOT NULL
    )""")
    createTable(db, 'auth_user', """
        CREATE TABLE auth_user (
            id          %(PRIMARYKEY)s,
            username    VARCHAR(30) NOT NULL,
            first_name  VARCHAR(30) NOT NULL,
            last_name   VARCHAR(30) NOT NULL,
            email       VARCHAR(75) NOT NULL,
            password    VARCHAR(128) NOT NULL,
            is_staff    BOOLEAN NOT NULL,
            is_active   BOOLEAN NOT NULL,
            is_superuser    BOOLEAN NOT NULL,
            last_login TIMESTAMP WITH TIME ZONE NOT NULL,
            date_joined TIMESTAMP WITH TIME ZONE NOT NULL
    )""")


def _createPackageSchema(db):
    """Package tables"""

    createTable(db, "packages_package_action_type", """
        CREATE TABLE "packages_package_action_type" (
            "package_action_type_id" %(PRIMARYKEY)s,
            "name" text NOT NULL,
            "description" text NOT NULL,
            "created_date" timestamp with time zone NOT NULL,
            "modified_date" timestamp with time zone NOT NULL
        )""")

    createTable(db, "packages_package", """
        CREATE TABLE "packages_package" (
            "package_id" %(PRIMARYKEY)s,
            "name" TEXT NOT NULL UNIQUE,
            "description" TEXT,
            "created_date" TIMESTAMP WITH TIME ZONE NOT NULL,
            "modified_date" TIMESTAMP WITH TIME ZONE NOT NULL,
            "created_by_id" INTEGER
                REFERENCES "users" ("userid") ON DELETE SET NULL,
            "modified_by_id" INTEGER
                REFERENCES "users" ("userid") ON DELETE SET NULL
        )""")

    createTable(db, "packages_package_version", """
        CREATE TABLE "packages_package_version" (
            "package_version_id" %(PRIMARYKEY)s,
            "package_id" integer NOT NULL
                REFERENCES "packages_package" ("package_id"),
            "name" text NOT NULL,
            "description" text,
            "license" text,
            "consumable" boolean NOT NULL,
            "created_date" timestamp with time zone NOT NULL,
            "modified_date" timestamp with time zone NOT NULL,
            "created_by_id" integer
                REFERENCES "users" ("userid"),
            "modified_by_id" integer
                REFERENCES "users" ("userid"),
            "committed" boolean NOT NULL
        )""")

    createTable(db, "packages_package_version_action", """
        CREATE TABLE "packages_package_version_action" (
            "package_version_action_id" %(PRIMARYKEY)s,
            "package_version_id" integer NOT NULL
                REFERENCES "packages_package_version" ("package_version_id"),
            "package_action_type_id" integer NOT NULL
                REFERENCES "packages_package_action_type"
                    ("package_action_type_id"),
            "visible" boolean NOT NULL,
            "enabled" boolean NOT NULL,
            "descriptor" text,
            "created_date" timestamp with time zone NOT NULL,
            "modified_date" timestamp with time zone NOT NULL
        )""")

    createTable(db, "packages_package_version_job", """
        CREATE TABLE "packages_package_version_job" (
            "package_version_job_id" %(PRIMARYKEY)s,
            "package_version_id" integer NOT NULL
                REFERENCES "packages_package_version" ("package_version_id"),
            "package_action_type_id" integer NOT NULL
                REFERENCES "packages_package_action_type"
                    ("package_action_type_id"),
            "job_id" integer
                REFERENCES "jobs_job" ("job_id"),
            "job_data" text,
            "created_date" timestamp with time zone NOT NULL,
            "modified_date" timestamp with time zone NOT NULL,
            "created_by_id" integer
                REFERENCES "users" ("userid"),
            "modified_by_id" integer
                REFERENCES "users" ("userid")
        )""")

    createTable(db, "packages_package_version_url", """
        CREATE TABLE "packages_package_version_url" (
            "package_version_url_id" %(PRIMARYKEY)s,
            "package_version_id" integer NOT NULL
                REFERENCES "packages_package_version" ("package_version_id"),
            "url" text NOT NULL,
            "file_path" text,
            "downloaded_date" timestamp with time zone,
            "file_size" integer,
            "created_date" timestamp with time zone NOT NULL,
            "modified_date" timestamp with time zone NOT NULL,
            "created_by_id" integer
                REFERENCES "users" ("userid"),
            "modified_by_id" integer
                REFERENCES "users" ("userid")
        )""")

    createTable(db, "packages_package_source", """
        CREATE TABLE "packages_package_source" (
            "package_source_id" %(PRIMARYKEY)s,
            "package_version_id" integer NOT NULL
                REFERENCES "packages_package_version" ("package_version_id"),
            "created_date" timestamp with time zone NOT NULL,
            "modified_date" timestamp with time zone NOT NULL,
            "created_by_id" integer
                REFERENCES "users" ("userid"),
            "modified_by_id" integer
                REFERENCES "users" ("userid"),
            "built" boolean NOT NULL,
            "trove_id" integer
                REFERENCES "inventory_trove" ("trove_id")
        )""")

    createTable(db, "packages_package_source_action", """
        CREATE TABLE "packages_package_source_action" (
            "package_source_action_id" %(PRIMARYKEY)s,
            "package_source_id" integer NOT NULL
                REFERENCES "packages_package_source" ("package_source_id"),
            "package_action_type_id" integer NOT NULL,
            "enabled" boolean NOT NULL,
            "visible" boolean NOT NULL,
            "descriptor" text,
            "created_date" timestamp with time zone NOT NULL,
            "modified_date" timestamp with time zone NOT NULL
        )""")

    createTable(db, "packages_package_source_job", """
        CREATE TABLE "packages_package_source_job" (
            "package_source_job_id" %(PRIMARYKEY)s,
            "package_source_id" integer NOT NULL
                REFERENCES "packages_package_source" ("package_source_id"),
            "package_action_type_id" integer NOT NULL
                REFERENCES "packages_package_action_type"
                    ("package_action_type_id"),
            "job_id" integer
                REFERENCES "jobs_job" ("job_id"),
            "job_data" text,
            "created_date" timestamp with time zone NOT NULL,
            "modified_date" timestamp with time zone NOT NULL,
            "created_by_id" integer
                REFERENCES "users" ("userid"),
            "modified_by_id" integer
                REFERENCES "users" ("userid")
        )""")

    createTable(db, "packages_package_build", """
        CREATE TABLE "packages_package_build" (
            "package_build_id" %(PRIMARYKEY)s,
            "package_source_id" integer NOT NULL
                REFERENCES "packages_package_source" ("package_source_id"),
            "created_date" timestamp with time zone NOT NULL,
            "modified_date" timestamp with time zone NOT NULL,
            "created_by_id" integer
                REFERENCES "users" ("userid"),
            "modified_by_id" integer
                REFERENCES "users" ("userid")
        )""")

    createTable(db, "packages_package_build_troves", """
        CREATE TABLE "packages_package_build_troves" (
            "id" %(PRIMARYKEY)s,
            "packagebuild_id" integer NOT NULL
                REFERENCES "packages_package_build" ("package_build_id"),
            "trove_id" integer NOT NULL
                REFERENCES "inventory_trove" ("trove_id"),
            UNIQUE ("packagebuild_id", "trove_id")
        )""")

    createTable(db, "packages_package_build_action", """
        CREATE TABLE "packages_package_build_action" (
            "package_build_action_id" %(PRIMARYKEY)s,
            "package_build_id" integer NOT NULL
                REFERENCES "packages_package_build" ("package_build_id"),
            "package_action_type_id" integer NOT NULL
                REFERENCES "packages_package_action_type"
                    ("package_action_type_id"),
            "visible" boolean NOT NULL,
            "enabled" boolean NOT NULL,
            "descriptor" text,
            "created_date" timestamp with time zone NOT NULL,
            "modified_date" timestamp with time zone NOT NULL
        )""")

    createTable(db, "packages_package_build_job", """
        CREATE TABLE "packages_package_build_job" (
            "package_build_job_id" %(PRIMARYKEY)s,
            "package_build_id" integer NOT NULL
                REFERENCES "packages_package_build" ("package_build_id"),
            "package_action_type_id" integer NOT NULL,
            "job_id" integer
                REFERENCES "jobs_job" ("job_id"),
            "job_data" text,
            "created_date" timestamp with time zone NOT NULL,
            "modified_date" timestamp with time zone NOT NULL,
            "created_by_id" integer
                REFERENCES "users" ("userid"),
            "modified_by_id" integer
                REFERENCES "users" ("userid")
        )""")

    db.createIndex("packages_package",
        "packages_package_created_by_id", "created_by_id")
    db.createIndex("packages_package",
        "packages_package_modified_by_id", "modified_by_id")
    db.createIndex("packages_package_version",
        "packages_package_version_package_id", "package_id")
    db.createIndex("packages_package_version",
        "packages_package_version_created_by_id", "created_by_id")
    db.createIndex("packages_package_version_action",
        "packages_package_version_action_package_version_id",
        "package_version_id")
    db.createIndex("packages_package_version_action",
        "packages_package_version_action_package_action_type_id",
        "package_action_type_id")
    db.createIndex("packages_package_version_job",
        "packages_package_version_job_package_version_id",
        "package_version_id")
    db.createIndex("packages_package_version_job",
        "packages_package_version_job_package_action_type_id",
        "package_action_type_id")
    db.createIndex("packages_package_version_job",
        "packages_package_version_job_job_id", "job_id")
    db.createIndex("packages_package_version_job",
        "packages_package_version_job_created_by_id", "created_by_id")
    db.createIndex("packages_package_version_job",
        "packages_package_version_job_modified_by_id", "modified_by_id")
    db.createIndex("packages_package_version_url",
        "packages_package_version_url_package_version_id",
        "package_version_id")
    db.createIndex("packages_package_version_url",
        "packages_package_version_url_created_by_id", "created_by_id")
    db.createIndex("packages_package_version_url",
        "packages_package_version_url_modified_by_id", "modified_by_id")
    db.createIndex("packages_package_source",
        "packages_package_source_package_version_id", "package_version_id")
    db.createIndex("packages_package_source",
        "packages_package_source_created_by_id", "created_by_id")
    db.createIndex("packages_package_source",
        "packages_package_source_modified_by_id", "modified_by_id")
    db.createIndex("packages_package_source",
        "packages_package_source_trove_id", "trove_id")
    db.createIndex("packages_package_source_action",
        "packages_package_source_action_package_source_id",
        "package_source_id")
    db.createIndex("packages_package_source_action",
        "packages_package_source_action_package_action_type_id",
        "package_action_type_id")
    db.createIndex("packages_package_source_job",
        "packages_package_source_job_package_source_id", "package_source_id")
    db.createIndex("packages_package_source_job",
        "packages_package_source_job_package_action_type_id",
        "package_action_type_id")
    db.createIndex("packages_package_source_job",
        "packages_package_source_job_job_id", "job_id")
    db.createIndex("packages_package_source_job",
        "packages_package_source_job_created_by_id", "created_by_id")
    db.createIndex("packages_package_source_job",
        "packages_package_source_job_modified_by_id", "modified_by_id")
    db.createIndex("packages_package_build",
        "packages_package_build_package_source_id", "package_source_id")
    db.createIndex("packages_package_build",
        "packages_package_build_created_by_id", "created_by_id")
    db.createIndex("packages_package_build",
        "packages_package_build_modified_by_id", "modified_by_id")
    db.createIndex("packages_package_build_action",
        "packages_package_build_action_package_build_id", "package_build_id")
    db.createIndex("packages_package_build_action",
        "packages_package_build_action_package_action_type_id",
        "package_action_type_id")
    db.createIndex("packages_package_build_job",
        "packages_package_build_job_package_build_id", "package_build_id")
    db.createIndex("packages_package_build_job",
        "packages_package_build_job_package_action_type_id",
        "package_action_type_id")
    db.createIndex("packages_package_build_job",
        "packages_package_build_job_job_id", "job_id")
    db.createIndex("packages_package_build_job",
        "packages_package_build_job_created_by_id", "created_by_id")
    db.createIndex("packages_package_build_job",
        "packages_package_build_job_modified_by_id", "modified_by_id")


def _createTargetJobs(db):
    createTable(db, 'jobs_job_target_type', """
        CREATE TABLE jobs_job_target_type (
            id          %(PRIMARYKEY)s,
            job_id      integer NOT NULL
                        REFERENCES jobs_job(job_id)
                        ON DELETE CASCADE,
            target_type_id integer NOT NULL
                        REFERENCES target_types(target_type_id)
                        ON DELETE CASCADE
    )""")
    createTable(db, 'jobs_job_target', """
        CREATE TABLE jobs_job_target (
            id          %(PRIMARYKEY)s,
            job_id      integer NOT NULL
                        REFERENCES jobs_job(job_id)
                        ON DELETE CASCADE,
            target_id integer NOT NULL
                        REFERENCES Targets(targetid)
                        ON DELETE CASCADE
    )""")

def _createJobThroughTables(db):
    createTable(db, 'jobs_job_image', """
            id          %(PRIMARYKEY)s,
            job_id      integer NOT NULL
                        REFERENCES jobs_job(job_id)
                        ON DELETE CASCADE,
            image_id integer NOT NULL
                        REFERENCES Builds(buildId)
                        ON DELETE CASCADE,
    """)

# create the (permanent) server repository schema
def createSchema(db, doCommit=True, cfg=None):
    if not hasattr(db, "tables"):
        db.loadSchema()

    if doCommit:
        db.transaction()

    _createUsers(db)
    _createProjects(db)
    _createLabels(db)
    _createPlatforms(db)
    _createProductVersions(db)
    _createBuilds(db)
    _createCommits(db)
    _createPackageIndex(db)
    _createMirrorInfo(db)
    _createSessions(db)
    _createZoneSchema(db)
    _createTargets(db)
    _createCapsuleIndexerSchema(db)
    _createRepositoryLogSchema(db)
    _createInventorySchema(db, cfg)
    _createJobsSchema(db)
    _createCapsuleIndexerYumSchema(db)
    _createPKI(db)
    _createQuerySetSchema(db)
    _createInfrastructureSystemsQuerySetSchema(db)
    _createWindowsBuildSystemsQuerySet(db)
    _createUpdateSystemsQuerySet(db)
    _createAllProjectBranchStages(db)
    _createAllProjects(db)
    _createChangeLogSchema(db)
    _createPackageSchema(db)
    _createDjangoSchema(db)
    _createRbac(db)
    _createTargetJobs(db)
    _createJobThroughTables(db)

    if doCommit:
        db.commit()
        db.loadSchema()


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
        version = checkVersion(db)
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
        version are no longer supported. Please contact rPath for help
        converting the rBuilder database to a supported version.""", version)

    # if we reach here, a schema migration is needed/requested
    db.transaction()
    try:
        version = migrate.migrateSchema(db, cfg)
        db.loadSchema()
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
