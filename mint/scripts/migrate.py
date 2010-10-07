#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

import logging
import os
import sys
import time

from conary.conarycfg import loadEntitlement, EntitlementList
from conary.dbstore import migration, sqlerrors
from mint import userlevels
from mint.db import repository
from mint.db import schema

log = logging.getLogger(__name__)


# SCHEMA Migration
class SchemaMigration(migration.SchemaMigration):
    db = None
    cfg = None
    msg = None

    def __init__(self, db, cfg=None):
        migration.SchemaMigration.__init__(self, db)
        self.cfg = cfg

    def message(self, msg = None):
        if msg is None:
            msg = self.msg
        if msg == "":
            msg = "Finished migration to schema version %s" % (self.Version,)
        log.info(msg)
        self.msg = msg


# Helper functions
def add_columns(db, table, *columns):
    '''
    Add each column while ignoring existing columns.

    >>> add_columns(db, 'Table', 'something INTEGER',
    ...     'somethingelse STRING')
    '''
    cu = db.cursor()
    changed = False

    for column in columns:
        try:
            cu.execute('ALTER TABLE %s ADD COLUMN %s' % (table, column))
            changed = True
        except sqlerrors.DuplicateColumnName:
            pass
    return changed


def drop_tables(db, *tables):
    '''
    Drop each table, ignoring any missing tables.

    >>> drop_tables(db, 'sometable', 'anothertable')
    '''
    cu = db.cursor()

    for table in tables:
        if table in db.tables:
            cu.execute('DROP TABLE %s' % (table,))
            del db.tables[table]

    db.loadSchema()


def rebuild_table(db, table, fieldsOut, fieldsIn=None):
    """
    SQLite offers no way to alter, drop, or change constraints on columns.
    So instead we have to rename it out of the way, build a new table, and
    drop the old one.
    """
    cu = db.cursor()

    tmpTable = None
    if table in db.tables:
        for index in list(db.tables[table]):
            db.dropIndex(table, index)

        tmpTable = table + '_tmp'
        cu.execute("ALTER TABLE %s RENAME TO %s" % (table, tmpTable))
        del db.tables[table]

    assert schema.createSchema(db, doCommit=False)

    if fieldsIn is None:
        fieldsIn = fieldsOut
    assert len(fieldsIn) == len(fieldsOut)

    if tmpTable:
        fieldsOut = ', '.join(fieldsOut)
        placeHolders = ' ,'.join('?' for x in fieldsOut)

        hasChoices = max(isinstance(x, (tuple, list)) for x in fieldsIn)
        if hasChoices:
            # This block is something resembling a portable way to pick
            # which of a list of possible field names is actually in the
            # table. All of the items in fieldsIn that are a list or tuple
            # of choices will be replaced with a single item that was found
            # in the table.
            cu.execute("SELECT * FROM %s LIMIT 1" % tmpTable)
            allFields = set(x.lower() for x in cu.fields())
            for n, field in enumerate(fieldsIn):
                if isinstance(field, (tuple, list)):
                    for choice in field:
                        if choice.lower() in allFields:
                            fieldsIn[n] = choice
                            break
                    else:
                        raise RuntimeError("None of the fields %r are in "
                                "table %s %r" % (tuple(field), table,
                                    tuple(allFields)))

        fieldsIn = ', '.join(fieldsIn)
        cu.execute("INSERT INTO %s ( %s ) SELECT %s FROM %s"
                % (table, fieldsOut, fieldsIn, tmpTable))
        cu.execute("DROP TABLE %s" % tmpTable)

    db.loadSchema()


def createTable(db, definition):
    return schema.createTable(db, None, definition)


#### SCHEMA MIGRATIONS BEGIN HERE ###########################################

# SCHEMA VERSION 37.0 - DUMMY MIGRATION
# Note that schemas older than 37 are not supported by this migration
class MigrateTo_37(SchemaMigration):
    Version = (37, 0)

    def migrate(self):
        return self.Version

# SCHEMA VERSION 38
class MigrateTo_38(SchemaMigration):
    Version = (38, 0)

    # 38.0
    # - Add cookCount to GroupTroves
    def migrate(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE GroupTroves ADD COLUMN cookCount INT""")
        cu.execute("UPDATE GroupTroves SET cookCount=0")
        cu.execute("DROP TABLE DatabaseVersion")
        return True

# SCHEMA VERSION 39
class MigrateTo_39(SchemaMigration):
    Version = (39, 0)

    # 39.0
    # - Move to Conary-style database versions
    def migrate(self):
        cu = self.db.cursor()
        cu.execute("DROP TABLE DatabaseVersion")
        return True


# SCHEMA VERSION 40
class MigrateTo_40(SchemaMigration):
    Version = (40, 0)

    # 40.0
    # - Add explicit auth type columns to Labels, InboundMirrors tables
    # - Move entitlements into Labels/InboundMirrors
    def migrate(self):
        cu = self.db.cursor()

        # Add columns
        cu.execute("ALTER TABLE Labels ADD COLUMN authType VARCHAR(254)")
        cu.execute("ALTER TABLE Labels ADD COLUMN entitlement VARCHAR(254)")
        cu.execute("ALTER TABLE InboundMirrors ADD COLUMN sourceAuthType VARCHAR(254)")
        cu.execute("ALTER TABLE InboundMirrors ADD COLUMN sourceEntitlement VARCHAR(254)")

        # Fix existing data - anonymous
        cu.execute("""UPDATE Labels
            SET authType = 'none', username = '', password = ''
            WHERE username = 'anonymous'
                OR username = '' OR username IS NULL
                OR password = '' OR password IS NULL""")
        cu.execute("""UPDATE InboundMirrors
            SET sourceAuthType = 'none', sourceUsername = '',
                sourcePassword=''
            WHERE sourceUsername = 'anonymous'
                OR sourceUsername = '' OR sourceUsername IS NULL
                OR sourcePassword = '' OR sourcePassword IS NULL""")

        # Fix existing data - username & password
        cu.execute("""UPDATE Labels SET authType = 'userpass'
            WHERE authType IS NULL""")
        cu.execute("""UPDATE InboundMirrors SET sourceAuthType = 'userpass'
            WHERE sourceAuthType IS NULL""")

        # Import entitlements
        entDir = os.path.join(self.cfg.dataPath, 'entitlements')
        entList = EntitlementList()
        if os.path.isdir(entDir):
            for basename in os.listdir(entDir):
                if os.path.isfile(os.path.join(entDir, basename)):
                    ent = loadEntitlement(entDir, basename)
                    if not ent:
                        continue
                    entList.addEntitlement(ent[0], ent[2])

        for host, ent in entList:
            ent = ent[1]
            cu.execute("""SELECT projectId, 
                    EXISTS(SELECT * FROM InboundMirrors WHERE
                        projectId=targetProjectId) AS localMirror
                FROM Projects LEFT JOIN Labels USING(projectId)
                WHERE external = 1 AND label LIKE ?""", '%s@%%' % host)

            for projectId, localMirror in cu.fetchall():
                if localMirror:
                    cu.execute("""UPDATE InboundMirrors
                        SET sourceAuthType = 'entitlement',
                            sourceEntitlement = ?
                        WHERE targetProjectId = ?""",
                            ent, projectId)
                else:
                    cu.execute("""UPDATE Labels
                        SET authType = 'entitlement', entitlement = ?
                        WHERE projectId = ?""",
                            ent, projectId)

        return True

# SCHEMA VERSION 41
class MigrateTo_41(SchemaMigration):
    Version = (41, 1)

    # 41.0
    # - buildCount
    def migrate(self):
        cu = self.db.cursor()
        cu.execute("ALTER TABLE Builds ADD COLUMN buildCount INTEGER")
        return True

    # 41.1
    # - buildCount should be set to 1 for older builds that were created
    #   pre-migration
    def migrate1(self):
        cu = self.db.cursor()
        cu.execute("UPDATE Builds SET buildCount = 1 WHERE buildCount IS NULL")
        return True

# SCHEMA VERSION 42
class MigrateTo_42(SchemaMigration):
    Version = (42, 0)

    # 42.0
    # - We were missing fullSync on OutboundMirrors in some 4.0.0 rBuilder
    #   schemas. This will rectify it without breaking databases which have
    #   it already.
    def migrate(self):
        cu = self.db.cursor()
        try:
            cu.execute("""ALTER TABLE OutboundMirrors
                ADD COLUMN fullSync INT NOT NULL DEFAULT 0""")
        except sqlerrors.DuplicateColumnName:
            pass # this is OK, as databases migrated from 3.1.x will have this
        return True

# SCHEMA VERSION 43
class MigrateTo_43(SchemaMigration):
    Version = (43, 0)

    # 43.0
    # - Add userDataTemplate to BlessedAMIs table
    # - Add userData to LaunchedAMIs table
    def migrate(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE BlessedAMIs
            ADD COLUMN userDataTemplate TEXT""")
        cu.execute("""ALTER TABLE LaunchedAMIs
            ADD COLUMN userData TEXT""")
        return True

# SCHEMA VERSION 44
class MigrateTo_44(SchemaMigration):
    Version = (44, 1)

    # 44.0
    # - Drop rMake related tables
    def migrate(self):
        drop_tables(self.db, 'rMakeBuild', 'rMakeBuildItems')
        return True

    # 44.1
    # - Add backupExternal column to Projects table
    def migrate1(self):
        add_columns(self.db, 'Projects', 'backupExternal INT DEFAULT 0')
        return True

# SCHEMA VERSION 45
class MigrateTo_45(SchemaMigration):
    Version = (45, 7)

    # 45.0
    # - Create UpdateServices table
    # - Create OutboundMirrorsUpdateServices table
    # - Distill the OutboundMirrorTargets table into a set unique by URL;
    #     fill in UpdateServices table
    # - Remap current outbound mirrors to new update services
    # - Drop no longer needed rAPAPasswords, OutboundMirrorTargets tables
    # - Add versions table
    def migrate(self):
        from urlparse import urlparse
        cu = self.db.cursor()

        # Make sure UpdateServices table and OutboundMirrorsUpdateServices
        # tables are created. We copy this code from mint/schema.py because
        # this is a snapshot of how these tables looked at the time this schema
        # version was created; calling schema._createMirrorInfo would create
        # the latest version of that table (and foul up future migrations,
        # perhaps).
        if 'UpdateServices' not in self.db.tables:
            cu.execute("""
            CREATE TABLE UpdateServices (
                updateServiceId         %(PRIMARYKEY)s,
                hostname                VARCHAR(767) NOT NULL,
                description             TEXT,
                mirrorUser              VARCHAR(254) NOT NULL,
                mirrorPassword          VARCHAR(254) NOT NULL
                ) %(TABLEOPTS)s""" % self.db.keywords)
            self.db.tables['UpdateServices'] = []
        self.db.createIndex('UpdateServices', 'UpdateServiceHostnameIdx',
                'hostname', unique = True)

        if 'OutboundMirrorsUpdateServices' not in self.db.tables:
            cu.execute("""
            CREATE TABLE OutboundMirrorsUpdateServices (
                outboundMirrorId        INT NOT NULL,
                updateServiceId         INT NOT NULL,
                CONSTRAINT ous_omi_fk
                    FOREIGN KEY (outboundMirrorId)
                        REFERENCES OutboundMirrors(outboundMirrorId)
                    ON DELETE CASCADE,
                CONSTRAINT ous_usi_fk
                    FOREIGN KEY (updateServiceId)
                        REFERENCES UpdateServices(updateServiceId)
                    ON DELETE CASCADE
                ) %(TABLEOPTS)s""" % self.db.keywords)
            self.db.tables['OutboundMirrorsUpdateServices'] = []
        self.db.createIndex('OutboundMirrorsUpdateServices', 'ous_omi_usi_uq',
                'outboundMirrorId, updateServiceId', unique = True)

        # Collapse all the OutboundMirrorTargets into the
        # UpdateServices table. Take the ones with the highestId
        # as they were the most recently-added, and have the best
        # possiblity of working against the Update Service.
        # Also collect the OutboundMirrorIds from the duplicate
        # entries and reassign them to an UpdateService
        cu.execute("""SELECT outboundMirrorTargetsId, outboundMirrorId,
                          url, username, password
                      FROM outboundMirrorTargets
                      ORDER BY outboundMirrorTargetsId DESC""")
        updateServices = dict()
        outboundMirrorsUpdateServices = dict()
        for targetId, mirrorId, url, username, password in cu.fetchall():
            updateServiceHostname = urlparse(url)[1]
            if updateServiceHostname not in updateServices.keys():
                updateServiceId = targetId
                updateServices[updateServiceHostname] = \
                        (updateServiceId, username, password)
                outboundMirrorsUpdateServices[updateServiceId] = []
            else:
                updateServiceId = updateServices[updateServiceHostname][0]
            outboundMirrorsUpdateServices[updateServiceId].append(mirrorId)

        for usHostname, usData in updateServices.items():
            cu.execute("""INSERT INTO UpdateServices (hostname,
                              updateServiceId, mirrorUser,
                              mirrorPassword)
                          VALUES(?,?,?,?)""", usHostname, *usData)

        for updateServiceId, outboundMirrorIds in \
                outboundMirrorsUpdateServices.items():
            for outboundMirrorId in outboundMirrorIds:
                cu.execute("""INSERT INTO OutboundMirrorsUpdateServices
                          VALUES(?,?)""", outboundMirrorId,
                          updateServiceId)

        # Kill old vestigial tables
        drop_tables(self.db, 'rAPAPasswords', 'OutboundMirrorTargets')

        # Create versions table if needed
        if 'ProductVersions' not in self.db.tables:
            cu.execute("""
                CREATE TABLE ProductVersions (
                    productVersionId    %(PRIMARYKEY)s,
                    projectId           INT NOT NULL,
                    name                VARCHAR(16),
                    description         TEXT,
                CONSTRAINT pv_pid_fk FOREIGN KEY (projectId)
                    REFERENCES Projects(projectId) ON DELETE CASCADE
            ) %(TABLEOPTS)s """ % self.db.keywords)
            self.db.tables['ProductVersions'] = []

        return True

    # 45.1
    # - Add columns that got dropped from the migration in a merge
    def migrate1(self):
        add_columns(self.db, 'Projects', "shortname VARCHAR(128)",
                                    "prodtype VARCHAR(128) DEFAULT ''",
                                    "version VARCHAR(128) DEFAULT ''")

        return True

    # 45.2
    # - Add columns to support mirroring of published releases
    def migrate2(self):
        add_columns(self.db, 'PublishedReleases',
                "shouldMirror INTEGER NOT NULL DEFAULT 0",
                "timeMirrored INTEGER")
        add_columns(self.db, 'OutboundMirrors',
            "useReleases INTEGER NOT NULL DEFAULT 0")
        return True
    
    # 45.3
    # - Set shortname to hostname if it isn't set to anything
    def migrate3(self):
        cu = self.db.cursor()
        cu.execute("""UPDATE Projects SET shortname=hostname
                    WHERE shortname is NULL""")
        return True

    # 45.4
    # - Store the namespace with the Product Version
    def migrate4(self):
        add_columns(self.db, 'ProductVersions',
                'namespace VARCHAR(16) DEFAULT %r' % self.cfg.namespace)
        #Drop and readd the unique index
        self.db.dropIndex('ProductVersions', 'ProductVersionsProjects')
        self.db.createIndex('ProductVersions', 'ProductVersionsNamespacesProjects',
            'projectId,namespace,name', unique = True)
        return True

    # 45.5
    # - Add namespace column to Project
    def migrate5(self):
        add_columns(self.db, 'Projects',
                'namespace VARCHAR(16) DEFAULT %r' % self.cfg.namespace)
        return True

    # 45.6
    # - create Target tables
    def migrate6(self):
        cu = self.db.cursor()
        if 'Targets' not in self.db.tables:
            cu.execute("""
                CREATE TABLE Targets (
                    targetId   %(PRIMARYKEY)s,
                    targetType VARCHAR(255),
                    targetName VARCHAR(255)
                ) %(TABLEOPTS)s""" % self.db.keywords)
            self.db.tables['Targets'] = []

        if 'TargetData' not in self.db.tables:
            cu.execute("""
                CREATE TABLE TargetData (
                    targetId  INT NOT NULL,
                    name      VARCHAR(255),
                    value     TEXT
                ) %(TABLEOPTS)s """ % self.db.keywords)
            self.db.tables['TargetData'] = []

        # this isn't ideal but the idea is to farm any ec2 settings data
        # from the rBuilder config values, so that they can be ignored from
        # now on. the alternative is to have data in two places, one of which
        # rBuilder can't necessarily control properly. (rbuilder-custom.conf)
        if self.cfg is not None:
            amiData = {}
            for k in ('ec2PublicKey', 'ec2PrivateKey', 'ec2AccountId',
                      'ec2S3Bucket', 'ec2LaunchUsers', 'ec2LaunchGroups',
                      'ec2ExposeTryItLink', 'ec2MaxInstancesPerIP',
                      'ec2DefaultInstanceTTL', 'ec2DefaultMayExtendTTLBy',
                      'ec2UseNATAddressing'):
                val = getattr(self.cfg, k, None)
                if val:
                    amiData[k] = val
            for k in ('ec2CertificateKeyFile', 'ec2CertificateFile'):
                path = getattr(self.cfg, k, '')
                if os.path.exists(path):
                    f = None
                    try:
                        f = open(path)
                        # we're stripping the "File" off the end of the key
                        amiData[k[:-4]] = f.read()
                    finally:
                        if f:
                            f.close()
            # only the important settings are enough to make us record
            # the presence of ec2 settings
            configured = False
            for key in ('ec2PublicKey', 'ec2PrivateKey', 'ec2AccountId',
                    'ec2S3Bucket', 'ec2LaunchUsers', 'ec2LaunchGroups',
                    'ec2CertificateKey', 'ec2Certificate'):
                if amiData.get(key):
                    configured = True
            if configured:
                import simplejson
                cu.execute("""INSERT INTO Targets (targetType, targetName)
                        VALUES('ec2', 'aws')""")
                targetId = cu.lastid()
                for name, value in amiData.iteritems():
                    value = simplejson.dumps(value)
                    cu.execute("INSERT INTO TargetData VALUES(?, ?, ?)",
                            targetId, name, value)

        return True

    # 45.7
    # - Reset GroupTrove sequence so that it's usable again
    def migrate7(self):
        self.db.setAutoIncrement('GroupTroves', 'groupTroveId')
        return True


# SCHEMA VERSION 46
class MigrateTo_46(SchemaMigration):
    Version = (46, 2)

    # 46.0
    # - Add versionId and stage columns to Builds
    def migrate(self):
        add_columns(self.db, 'Builds', 
                     'productVersionId INTEGER',
                     'stageName VARCHAR(255) DEFAULT ""', 
                    )
        return True

    # 46.1
    # - Add timeCreated column to ProductVersions
    def migrate1(self):
        cu = self.db.cursor()
        add_columns(self.db, 'ProductVersions',
                'timeCreated numeric(14,3)')
        cu.execute('UPDATE ProductVersions SET timeCreated = 0')
        return True

    # 46.2
    # - Add status, statusMessage to Builds
    def migrate2(self):
        cu = self.db.cursor()
        add_columns(self.db, 'Builds',
                'status INTEGER DEFAULT -1',
                'statusMessage VARCHAR(255) DEFAULT ""')
        return True

class MigrateTo_47(SchemaMigration):
    Version = (47, 1)

    # 47.0
    # - Fixups for migration to PostgreSQL
    # - Added "database" and "fqdn" columns to Projects
    # - Populated fqdn column from Labels table
    # - Migrated ReposDatabases/ProjectDatabase into database column and
    #   dropped those tables.
    def migrate(self):
        cu = self.db.cursor()

        # Begin fixups
        if self.db.driver == 'sqlite':
            rebuild_table(self.db, "UrlDownloads",
                    ['urlId', 'timeDownloaded', 'ip'])
            rebuild_table(self.db, "BuildFiles",
                    ['fileId', 'buildId', 'idx', 'title', 'size', 'sha1'])

        cu.execute("UPDATE Projects SET isAppliance = 1 WHERE isAppliance IS NULL")
        cu.execute("UPDATE Projects SET shortname = hostname WHERE shortname IS NULL")
        cu.execute("UPDATE Projects SET creatorId = NULL WHERE creatorId = -1")
        cu.execute("UPDATE Builds SET productVersionId = NULL WHERE productVersionId = 0")
        # End fixups

        add_columns(self.db, 'Projects', "database varchar(128)",
                "fqdn varchar(255)")

        cu.execute("""SELECT p.projectId, p.external, p.hostname, p.domainname,
                    r.driver, r.path, l.label,
                    EXISTS (
                        SELECT * FROM InboundMirrors m
                        WHERE p.projectId = m.targetProjectId
                    ) AS localMirror
                FROM Projects p
                LEFT JOIN Labels l USING ( projectId )
                LEFT JOIN ProjectDatabase d USING ( projectId )
                LEFT JOIN ReposDatabases r USING ( databaseId )""")
        cu2 = self.db.cursor()
        for row in cu:
            if row['label']:
                fqdn = row['label'].split('@')[0]
            else:
                fqdn = '%s.%s' % (row['hostname'], row['domainname'])

            if row['external'] and not row['localMirror']:
                # No database: leave column NULL
                database = None
            if row['driver']:
                # "Alternate" database: set column to the full connect string
                database = '%s %s' % (row['driver'], row['path'])
            else:
                # "Default" database: set column to 'default'
                database = 'default'
            cu2.execute("""UPDATE Projects SET fqdn = ?, database = ?
                    WHERE projectId = ?""", fqdn, database, row['projectId'])
        drop_tables(self.db, 'ProjectDatabase', 'ReposDatabases')
        return True

    # 47.1
    # - PostgreSQL fixup: change type on troveLastChanged to std timestamp
    # - BuildsView is obsolete in 48.0 so we drop it early here to save work
    def migrate1(self):
        cu = self.db.cursor()

        if 'BuildsView' in self.db.views:
            cu.execute("DROP VIEW BuildsView")
            del self.db.views['BuildsView']

        if self.db.driver != 'sqlite':
            cu.execute("""ALTER TABLE Builds
                    ALTER COLUMN troveLastChanged TYPE numeric(14,3)""")

        return True


class MigrateTo_48(SchemaMigration):
    Version = (48, 15)

    # 48.0
    # - Dropped tables: Jobs, JobsData, GroupTroves, GroupTroveItems,
    #       ConaryComponents, GroupTroveRemovedComponents
    # - Dropped BuildsView
    # - Dropped "deleted" column from Builds
    # - Changed type of build status column to "text"
    def migrate(self):
        cu = self.db.cursor()
        drop_tables(self.db, 'JobData', 'Jobs', 'ConaryComponents',
                'GroupTroveRemovedComponents', 'GroupTroveItems',
                'GroupTroves')

        if 'BuildsView' in self.db.views:
            cu.execute("DROP VIEW BuildsView")
            del self.db.views['BuildsView']

        # This will orphan child rows on sqlite but postgres migration
        # will clean them up.
        cu.execute("DELETE FROM Builds WHERE deleted = 1")

        if self.db.driver != 'sqlite':
            # Only change the columns on postgres/mysql which actually
            # support doing so trivially; on sqlite we're just going to be
            # migrating to postgres anyway.
            cu.execute("ALTER TABLE Builds DROP COLUMN deleted")
            if self.db.driver == 'mysql':
                cu.execute("""ALTER TABLE Builds
                        MODIFY COLUMN statusMessage text""")
            else:
                cu.execute("""ALTER TABLE Builds
                        ALTER COLUMN statusMessage TYPE text""")

        return True                    

    # 48.1
    # - Move component and non-typed projects to be "repositories"
    def migrate1(self):
        cu = self.db.cursor()
        cu.execute("""UPDATE Projects SET prodType = 'Repository'
            WHERE prodType IN ('Component', '', NULL)""")
        return True

    # 48.2
    # - Move non-typed projects to be "repositories" again due
    #   to external project creation bug RBL-4938
    def migrate2(self):
        cu = self.db.cursor()
        cu.execute("""UPDATE Projects SET prodType = 'Repository'
            WHERE prodType IN ('', NULL)""")
        return True

    # 48.3
    # - Create missing roles for repositories. (RBL-5019)
    def migrate3(self):
        manager = repository.RepositoryManager(self.cfg, self.db, bypass=True)
        for repos in manager.iterRepositories():
            if not repos.hasDatabase:
                continue
            log.info("Checking repository %s for standardized roles",
                    repos.fqdn)

            if repos.isExternal:
                neededRoles = [repository.ROLE_PERMS[userlevels.ADMIN]]
            else:
                neededRoles = repository.ROLE_PERMS.values()

            try:
                presentRoles = repos.getRoleList()
                numAdded = 0
                for role, write, admin in neededRoles:
                    if role in presentRoles:
                        continue
                    repos.addRoleWithACE(role, write=write, remove=admin,
                            mirror=admin, admin=admin)
                    numAdded += 1
                if numAdded:
                    log.info("Added %d roles to project %s", numAdded,
                            repos.fqdn)
            except:
                log.exception("Error checking roles of project %s -- the "
                        "project may not function correctly.",  repos.fqdn)

            # Don't leave reposdb connections hanging around or we'll run out
            # before we hit all the projects.
            manager.close()

        return True

    # 48.4
    # - Platforms / PlatformSources / PlatformSourceData tables will be
    # created.
    def migrate4(self):
        schema._createPlatforms(self.db)
        return True

    # 48.5
    # - Dashboard report type table 
    def migrate5(self):
        return True

    # 48.6
    # - Dashboard Repository Log scraping table 
    def migrate6(self):
        schema._createRepositoryLogSchema(self.db)
        return True

    # 48.7
    # Preserved for previous migration no longer needed, we don't want to
    # decrease the version number.
    def migrate7(self):
        return True

    # 48.8
    # Add Indexer schema
    def migrate8(self):
        schema._createCapsuleIndexerSchema(self.db)
        return True

    # 48.9
    # Preserved for previous migration no longer needed, we don't want to
    # decrease the version number.
    def migrate9(self):
        return True            
        
    # 48.10
    # Preserved for previous migration no longer needed, we don't want to
    # decrease the version number.
    def migrate10(self):
        return True

    # 48.11
    # Preserved for previous migration no longer needed, we don't want to
    # decrease the version number.
    def migrate11(self):
        return True

    # 48.12
    # - Clear the database column for proxied external projects.
    def migrate12(self):
        cu = self.db.cursor()
        cu.execute("""
            UPDATE Projects p SET database = NULL
            WHERE external = 1 AND NOT EXISTS (
                SELECT * FROM InboundMirrors m
                WHERE p.projectId = m.targetProjectId
            )""")
        return True

    # 48.13
    # - nevra.epoch is not nullable - but we won't enforce the constraint here
    # we will only convert the data
    def migrate13(self):
        cu = self.db.cursor()
        cu.execute("""
            UPDATE ci_rhn_nevra SET epoch = -1 WHERE epoch IS NULL
        """)
        return True

    # 48.14
    # - create ci_rhn_errata_nevra_channel, drop ci_rhn_errata_package
    def migrate14(self):
        # Work around bug in createIndex being called twice with no
        # intermediate loadSchema. This can be removed after consuming conary
        # 2.1.12. See CNY-3380, RBL-6012
        self.db.loadSchema()
        schema._createCapsuleIndexerSchema(self.db)
        drop_tables(self.db, 'ci_rhn_errata_package')
        return True

    # 48.15
    # - yum indexer
    def migrate15(self):
        schema._createCapsuleIndexerSchema(self.db)
        return True

class MigrateTo_49(SchemaMigration):
    Version = (49, 7)

    # 49.0
    # - Added TargetUserCredentials
    # - Dropped platformLoadJobs table
    def migrate(self):
        cu = self.db.cursor()
        cu.execute("""
            CREATE TABLE TargetUserCredentials (
                targetId        integer             NOT NULL
                    REFERENCES Targets ON DELETE CASCADE,
                userId          integer             NOT NULL
                    REFERENCES Users ON DELETE CASCADE,
                credentials     text,
                PRIMARY KEY ( targetId, userId )
            ) %(TABLEOPTS)s """ % self.db.keywords)

        drop_tables(self.db, 'platformLoadJobs')

        return True

    # 49.1
    # - create ci_rhn_errata_nevra_channel, drop ci_rhn_errata_package
    def migrate1(self):
        schema._createCapsuleIndexerSchema(self.db)
        drop_tables(self.db, 'ci_rhn_errata_package')

        from mint import config
        from mint.scripts import migrate_catalog_data
        cfg = config.getConfig()
        conv = migrate_catalog_data.TargetConversion(cfg, self.db)
        conv.run()

        # Drop uniq constraint on targetName
        cu = self.db.cursor()
        cu.execute("ALTER TABLE Targets DROP CONSTRAINT targets_targetname_key")

        self.db.createIndex('Targets',
            'Targets_Type_Name_Uq', 'targetType, targetName', unique = True)
        return True

    def migrate2(self):
        cu = self.db.cursor()
        if 'inventory_managed_system' not in self.db.tables:
            cu.execute("""
                CREATE TABLE "inventory_managed_system" (
                    "id" %(PRIMARYKEY)s,
                    "registration_date" timestamp with time zone NOT NULL,
                    "generated_uuid" varchar(64),
                    "local_uuid" varchar(64),
                    "ssl_client_certificate" varchar(8092),
                    "ssl_client_key" varchar(8092),
                    "ssl_server_certificate" varchar(8092),
                    "launching_user_id" integer REFERENCES "users" ("userid")
                ) %(TABLEOPTS)s""" % self.db.keywords)
            self.db.tables['inventory_managed_system'] = []

        if 'inventory_system_target' not in self.db.tables:
            cu.execute("""
                CREATE TABLE "inventory_system_target" (
                    "id" %(PRIMARYKEY)s,
                    "managed_system_id" integer 
                        REFERENCES "inventory_managed_system" ("id") 
                        DEFERRABLE INITIALLY DEFERRED,
                    "target_id" integer NOT NULL 
                        REFERENCES "targets" ("targetid") 
                        DEFERRABLE INITIALLY DEFERRED,
                    "target_system_id" varchar(256)
                ) %(TABLEOPTS)s""" % self.db.keywords)
            cu.execute("""
            CREATE INDEX "inventory_system_target_managed_system_id" 
                ON "inventory_system_target" ("managed_system_id");
            """)
            cu.execute("""
            CREATE INDEX "inventory_system_target_target_id" 
                ON "inventory_system_target" ("target_id");
            """)
            self.db.tables['inventory_system_target'] = []

        if 'inventory_software_version' not in self.db.tables:
            cu.execute("""
                CREATE TABLE "inventory_software_version" (
                    "id" %(PRIMARYKEY)s,
                    "name" text NOT NULL,
                    "version" text NOT NULL,
                    "flavor" text NOT NULL,
                    UNIQUE ("name", "version", "flavor")
                ) %(TABLEOPTS)s""" % self.db.keywords)
            self.db.tables['inventory_software_version'] = []

        if 'inventory_system_software_version' not in self.db.tables:
            cu.execute("""
                CREATE TABLE "inventory_system_software_version" (
                    "id" %(PRIMARYKEY)s,
                    "managed_system_id" integer NOT NULL 
                        REFERENCES "inventory_managed_system" ("id") 
                        DEFERRABLE INITIALLY DEFERRED,
                    "software_version_id" integer NOT NULL 
                        REFERENCES "inventory_software_version" ("id") 
                        DEFERRABLE INITIALLY DEFERRED
                ) %(TABLEOPTS)s""" % self.db.keywords)
            cu.execute("""
            CREATE INDEX "inventory_system_software_version_managed_system_id" 
                ON "inventory_system_software_version" ("managed_system_id");
            """)
            cu.execute("""
            CREATE INDEX "inventory_system_software_version_software_version_id" 
                ON "inventory_system_software_version" ("software_version_id");
            """)
            self.db.tables['inventory_system_software_version'] = []

        if 'inventory_system_information' not in self.db.tables:
            cu.execute("""
                CREATE TABLE "inventory_system_information" (
                    "id" %(PRIMARYKEY)s,
                    "managed_system_id" integer NOT NULL 
                        REFERENCES "inventory_managed_system" ("id") 
                        DEFERRABLE INITIALLY DEFERRED,
                    "system_name" varchar(64),
                    "memory" integer,
                    "os_type" varchar(64),
                    "os_major_version" varchar(32),
                    "os_minor_version" varchar(32),
                    "system_type" varchar(32)
                ) %(TABLEOPTS)s""" % self.db.keywords)
            cu.execute("""
            CREATE INDEX "inventory_system_information_managed_system_id" 
                ON "inventory_system_information" ("managed_system_id");
            """)
            self.db.tables['inventory_system_information'] = []

        if 'inventory_network_information' not in self.db.tables:
            cu.execute("""
                CREATE TABLE "inventory_network_information" (
                    "id" %(PRIMARYKEY)s,
                    "managed_system_id" integer NOT NULL 
                        REFERENCES "inventory_managed_system" ("id") 
                        DEFERRABLE INITIALLY DEFERRED,
                    "interface_name" varchar(32),
                    "ip_address" varchar(15),
                    "netmask" varchar(20),
                    "port_type" varchar(32)
                ) %(TABLEOPTS)s""" % self.db.keywords)
            cu.execute("""
            CREATE INDEX "inventory_network_information_managed_system_id" 
                ON "inventory_network_information" ("managed_system_id");
            """)
            self.db.tables['inventory_network_information'] = []

        if 'inventory_storage_volume' not in self.db.tables:
            cu.execute("""
                CREATE TABLE "inventory_storage_volume" (
                    "id" %(PRIMARYKEY)s,
                    "managed_system_id" integer NOT NULL 
                        REFERENCES "inventory_managed_system" ("id") 
                        DEFERRABLE INITIALLY DEFERRED,
                    "size" integer,
                    "storage_type" varchar(32),
                    "storage_name" varchar(32)
                ) %(TABLEOPTS)s""" % self.db.keywords)
            cu.execute("""
            CREATE INDEX "inventory_storage_volume_managed_system_id" 
                ON "inventory_storage_volume" ("managed_system_id");
            """)
            self.db.tables['inventory_storage_volume'] = []

        if 'inventory_cpu' not in self.db.tables:
            cu.execute("""
                CREATE TABLE "inventory_cpu" (
                    "id" %(PRIMARYKEY)s,
                    "managed_system_id" integer NOT NULL 
                        REFERENCES "inventory_managed_system" ("id") 
                        DEFERRABLE INITIALLY DEFERRED,
                    "cpu_type" varchar(64),
                    "cpu_count" integer,
                    "cores" integer,
                    "speed" integer,
                    "enabled" boolean
                ) %(TABLEOPTS)s""" % self.db.keywords)
            cu.execute("""
            CREATE INDEX "inventory_cpu_managed_system_id" 
                ON "inventory_cpu" ("managed_system_id");
            """)
            self.db.tables['inventory_cpu'] = []

        schema._createJobsSchema(self.db)
        return True

    def migrate3(self):
        cu = self.db.cursor()
        if 'inventory_software_version_update' not in self.db.tables:
            cu.execute("""
                CREATE TABLE "inventory_software_version_update" (
                    "id" %(PRIMARYKEY)s,
                    "software_version_id" integer NOT NULL 
                        REFERENCES "inventory_software_version" ("id"),
                    "available_update_id" integer NOT NULL 
                        REFERENCES "inventory_software_version" ("id"),
                    "last_refreshed" timestamp with time zone NOT NULL,
                    UNIQUE ("software_version_id", "available_update_id")
            ) %(TABLEOPTS)s """ % self.db.keywords)
            cu.execute("""
                CREATE INDEX "inventory_software_version_update_software_version_id" 
                    ON "inventory_software_version_update" ("software_version_id")
            """)
            self.db.tables['inventory_software_version_update'] = []
        return True

    def migrate4(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE inventory_system_software_version 
            ADD CONSTRAINT inventory_system_software_version_sys_sv_uq 
                UNIQUE (managed_system_id, software_version_id)
        """)
        return True
        
    def migrate5(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE inventory_software_version_update 
            ALTER COLUMN available_update_id DROP NOT NULL
        """)
        return True

    def migrate6(self):
        schema._createCapsuleIndexerSchema(self.db)
        return True

    def migrate7(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE inventory_system_target 
            ALTER COLUMN target_id DROP NOT NULL
        """)
        cu.execute("""
            ALTER TABLE inventory_system_target 
            DROP CONSTRAINT inventory_system_target_target_id_fkey
        """)
        cu.execute("""
            ALTER TABLE inventory_system_target 
            ADD CONSTRAINT inventory_system_target_target_id_fkey 
            FOREIGN KEY (target_id) 
            REFERENCES targets(targetid) ON DELETE SET NULL
        """)
        return True

class MigrateTo_50(SchemaMigration):
    Version = (50, 3)

    def migrate(self):
        cu = self.db.cursor()
        db = self.db

        changed = drop_tables(db,
            "inventory_system_target",
            "inventory_system_software_version",
            "inventory_system_information",
            "inventory_network_information",
            "inventory_storage_volume",
            "inventory_cpu",
            "inventory_software_version_update",
            "inventory_software_version",
            "job_managed_system",
            "inventory_managed_system",
            "inventory_managementnode")
        
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
            changed |= schema._addSystemStates(db, self.cfg)

        if 'inventory_system' not in db.tables:
            cu.execute("""
                CREATE TABLE "inventory_system" (
                    "system_id" %(PRIMARYKEY)s,
                    "name" varchar(8092) NOT NULL,
                    "description" varchar(8092),
                    "created_date" timestamp with time zone NOT NULL,
                    "hostname" varchar(8092),
                    "launch_date" timestamp with time zone,
                    "target_id" integer REFERENCES "targets" ("targetid"),
                    "target_system_id" varchar(255),
                    "target_system_name" varchar(255),
                    "target_system_description" varchar(1024),
                    "target_system_state" varchar(64),
                    "os_type" varchar(64),
                    "os_major_version" varchar(32),
                    "os_minor_version" varchar(32),
                    "registration_date" timestamp with time zone,
                    "generated_uuid" varchar(64) UNIQUE,
                    "local_uuid" varchar(64),
                    "ssl_client_certificate" varchar(8092),
                    "ssl_client_key" varchar(8092),
                    "ssl_server_certificate" varchar(8092),
                    "agent_port" integer,
                    "state_change_date" timestamp with time zone,
                    "launching_user_id" integer REFERENCES "users" ("userid"),
                    "current_state_id" integer NOT NULL
                        REFERENCES "inventory_system_state" ("system_state_id"),
                    "management_node" bool,
                    "managing_zone_id" integer NOT NULL
                        REFERENCES "inventory_zone" ("zone_id")
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
                    "ipv6_address" varchar(32),
                    "device_name" varchar(255),
                    "dns_name" varchar(255) NOT NULL,
                    "netmask" varchar(20),
                    "port_type" varchar(32),
                    "active" bool,
                    "required" bool,
                    UNIQUE ("system_id", "dns_name"),
                    UNIQUE ("system_id", "ip_address"),
                    UNIQUE ("system_id", "ipv6_address")
                ) %(TABLEOPTS)s""" % db.keywords)
            db.tables['inventory_system_network'] = []
            changed = True
            changed |= db.createIndex("inventory_system_network",
                "inventory_system_network_system_id_idx", "system_id")
            changed |= db.createIndex("inventory_system_network",
            "inventory_system_network_dns_name_idx", "dns_name")

        # add local management zone
        changed |= schema._addManagementZone(db, self.cfg)

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
            changed |= schema._addTableRows(db, tableName, 'name',
                [dict(name="system registration",
                      description='on-demand system registration event', priority=110),
                 dict(name="system poll",
                      description='standard system polling event', priority=50),
                 dict(name="immediate system poll",
                      description='on-demand system polling event', priority=105),
                 dict(name="system apply update",
                      description='apply an update to a system',
                      priority=50),
                 dict(name="immediate system apply update",
                      description='on-demand apply an update to a system', priority=105),
                 dict(name="system shutdown",
                      description='shutdown a system', priority=50),
                 dict(name="immediate system shutdown", 
                      description='on-demand shutdown a system', 
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
                    "priority" smallint NOT NULL
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
        changed |= schema._addTableRows(db, 'inventory_job_state', 'name',
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
                    time_created timestamp with time zone NOT NULL,
                    time_updated timestamp with time zone NOT NULL
                ) %(TABLEOPTS)s""" % db.keywords)
            db.tables[tableName] = []
            changed = True

        tableName = "inventory_system_job"
        if 'inventory_system_job' not in db.tables:
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
                )""" % db.keywords)
            db.tables['inventory_system_target_credentials'] = []
            changed = db.createIndex(
                'inventory_system_target_credentials_system_id_credentials_uq',
                'system_id', 'credentials_id', unique=True)
            changed = True

        createTable(db, """
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

        changed |= createTable(db, 'TargetCredentials', """
                CREATE TABLE TargetCredentials (
                    targetCredentialsId     %(PRIMARYKEY)s,
                    credentials             text NOT NULL UNIQUE
                ) %(TABLEOPTS)s""")

        self._migrateTargetUserCredentials(cu)
        return True

    def _migrateTargetUserCredentials(self, cu):
        # Add a serial primary key, drop the old pk, add it as unique
        cu.execute("""
            ALTER TABLE TargetUserCredentials
                DROP CONSTRAINT targetusercredentials_pkey""")
        cu.execute("""
            ALTER TABLE TargetUserCredentials
                ADD COLUMN id SERIAL PRIMARY KEY""")
        cu.execute("""
            ALTER TABLE TargetUserCredentials
                ADD UNIQUE(targetid, userid)""")
        cu.execute("""
            ALTER TABLE TargetUserCredentials
                ADD COLUMN targetCredentialsId  INTEGER
                    REFERENCES TargetCredentials
                        ON DELETE CASCADE
        """)
        cu.execute("""
            INSERT INTO TargetCredentials (credentials)
                SELECT DISTINCT credentials FROM TargetUserCredentials
        """)
        cu.execute("""
            UPDATE TargetUserCredentials AS a
            SET targetCredentialsId = (
                SELECT targetCredentialsId
                  FROM TargetUserCredentials
                 WHERE credentials = a.credentials)
        """)
        cu.execute("""
            ALTER TABLE TargetUserCredentials
                ALTER COLUMN targetCredentialsId SET NOT NULL
        """)
        cu.execute("""
            ALTER TABLE TargetUserCredentials
                DROP COLUMN credentials
        """)

        return True

    def migrate1(self):
        cu = self.db.cursor()
        db = self.db

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

        return changed or True
    
    def migrate2(self):
        cu = self.db.cursor()

        cu.execute("""
            ALTER TABLE inventory_system
                DROP COLUMN os_type,
                DROP COLUMN os_major_version,
                DROP COLUMN os_minor_version
        """)
        cu.execute("ALTER TABLE jobs ADD COLUMN job_uuid VARCHAR(64)")
        cu.execute("UPDATE jobs SET job_uuid=job_id")
        cu.execute("ALTER TABLE jobs ALTER COLUMN job_uuid SET NOT NULL")
        cu.execute("ALTER TABLE jobs ADD UNIQUE(job_uuid)")
        return True

    def migrate3(self):
        cu = self.db.cursor()

        cu.execute("""
            INSERT INTO "inventory_event_type" 
                ("name", "description", "priority")
            VALUES
                ('system launch wait',
                 'wait for a launched system''s network information',
                 105)
        """)
        return True

class MigrateTo_51(SchemaMigration):
    Version = (51, 6)

    def migrate(self):
        cu = self.db.cursor()
        db = self.db
        changed = False
        
        if 'inventory_management_interface' not in db.tables:
            cu.execute("""
                CREATE TABLE "inventory_management_interface" (
                    "management_interface_id" %(PRIMARYKEY)s,
                    "name" varchar(8092) NOT NULL UNIQUE,
                    "description" varchar(8092) NOT NULL,
                    "created_date" timestamp with time zone NOT NULL,
                    "port" integer NOT NULL,
                    "credentials_descriptor" text NOT NULL
                ) %(TABLEOPTS)s""" % db.keywords)
            db.tables['inventory_management_interface'] = []
            changed = True
        
        cu.execute("""
            ALTER TABLE inventory_system
                ADD COLUMN management_interface_id  INTEGER
                    REFERENCES inventory_management_interface
        """)
        
        return True
    
    def migrate1(self):
        cu = self.db.cursor()
        db = self.db
        
        cu.execute("ALTER TABLE inventory_management_interface ADD COLUMN credentials_readonly bool")
        schema._addManagementInterfaces(db)
        cu.execute("UPDATE inventory_management_interface SET credentials_readonly='true' WHERE name='cim'")
        cu.execute("UPDATE inventory_management_interface SET credentials_readonly='false' WHERE name='wmi'")
        
        return True
    
    def migrate2(self):
        cu = self.db.cursor()
        
        cu.execute("UPDATE inventory_management_interface SET port='5989' WHERE name='cim'")
        
        return True

    def migrate3(self):
        cu = self.db.cursor()
        db = self.db

        cu.execute("""
            INSERT INTO "inventory_event_type" 
                ("name", "description", "priority")
            VALUES
                ('system detect management interface',
                 'detect a system''s management interface',
                 50)
        """)

        cu.execute("""
            INSERT INTO "inventory_event_type" 
                ("name", "description", "priority")
            VALUES
                ('immediate system detect management interface',
                 'on-demand detect a system''s management interface',
                 105)
        """)
        
        return True

    def migrate4(self):
        cu = self.db.cursor()
        
        cu.execute("ALTER TABLE inventory_system ADD COLUMN credentials text")
        
        return True
    
    def migrate5(self):
        cu = self.db.cursor()
        changed = True
        
        if 'inventory_system_type' not in self.db.tables:
            cu.execute("""
                CREATE TABLE "inventory_system_type" (
                    "system_type_id" %(PRIMARYKEY)s,
                    "name" varchar(8092) NOT NULL UNIQUE,
                    "description" varchar(8092) NOT NULL,
                    "created_date" timestamp with time zone NOT NULL,
                    "infrastructure" bool
                ) %(TABLEOPTS)s""" % self.db.keywords)
            self.db.tables['inventory_system_type'] = []
            changed |= schema._addSystemTypes(self.db)
            changed = True
            
        cu.execute("""
            ALTER TABLE inventory_system
                ADD COLUMN type_id  INTEGER
                    REFERENCES inventory_system_type
        """)
            
        # update type on the rUS
        cu.execute("SELECT system_type_id from inventory_system_type where name='infrastructure-management-node'")
        ids = cu.fetchall()
        mgmtNodeId = ids[0][0]
        cu.execute("UPDATE inventory_system SET type_id='%d' WHERE name='rPath Update Service'" % mgmtNodeId)
        
        # update type on the other systems
        cu.execute("SELECT system_type_id from inventory_system_type where name='inventory'")
        ids = cu.fetchall()
        invTypeId = ids[0][0]
        cu.execute("UPDATE inventory_system SET type_id='%d' WHERE name<>'rPath Update Service'" % invTypeId)
        
        return True
    
    def migrate6(self):
        cu = self.db.cursor()

        cu.execute("""ALTER TABLE inventory_system DROP COLUMN management_node""")
        
        return True

#### SCHEMA MIGRATIONS END HERE #############################################

def _getMigration(major):
    try:
        ret = sys.modules[__name__].__dict__['MigrateTo_' + str(major)]
    except KeyError:
        return None
    return ret

# return the last major.minor version for a given major
def majorMinor(major):
    migr = _getMigration(major)
    if migr is None:
        return (major, 0)
    return migr.Version


def tryMigrate(db, func):
    # Do all migration steps in one transaction so a failure in createSchema
    # will abort the whole thing. Otherwise we wouldn't rerun the createSchema
    # because the schema version has already been updated.
    return func(skipCommit=True)


# entry point that migrates the schema
def migrateSchema(db, cfg=None):
    version = db.getVersion()
    assert(version >= 37) # minimum version we support
    if version.major > schema.RBUILDER_DB_VERSION.major:
        return version # noop, should not have been called.
    # first, we need to make sure that for the current major we're up
    # to the latest minor
    migrateFunc = _getMigration(version.major)
    if migrateFunc is None:
        raise sqlerrors.SchemaVersionError(
            "Could not find migration code that deals with repository "
            "schema %s" % version, version)
    # migrate all the way to the latest minor for the current major
    tryMigrate(db, migrateFunc(db, cfg))
    version = db.getVersion()
    # migrate to the latest major
    while version.major < schema.RBUILDER_DB_VERSION.major:
        migrateFunc = _getMigration(version.major+1)
        newVersion = tryMigrate(db, migrateFunc(db, cfg))
        assert(newVersion.major == version.major+1)
        version = newVersion
    return version
