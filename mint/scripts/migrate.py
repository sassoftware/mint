#
# Copyright (c) 2005-2009 rPath, Inc.
#

import logging
import os
import sys

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

    for column in columns:
        try:
            cu.execute('ALTER TABLE %s ADD COLUMN %s' % (table, column))
        except sqlerrors.DuplicateColumnName:
            pass


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
