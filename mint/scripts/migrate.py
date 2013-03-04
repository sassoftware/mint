#
# Copyright (c) rPath, Inc.
#

import logging
import os
import sys

import datetime
from dateutil import tz

from conary import files as cny_files
from conary.conarycfg import loadEntitlement, EntitlementList
from conary.dbstore import migration, sqlerrors
from mint import buildtypes, userlevels
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
    cu.execute("SELECT * FROM %s LIMIT 1" % (table,))
    allFields = set(x.lower() for x in cu.fields())
    for column in columns:
        name = column.split()[0]
        if name.lower() not in allFields:
            cu.execute('ALTER TABLE %s ADD COLUMN %s' % (table, column))
    return True


def drop_columns(db, table, *columns):
    """
    Drop each column while ignoring missing columns.

    >>> drop_columns(db, 'Table', 'column1', 'column2')
    """
    cu = db.cursor()
    cu.execute("SELECT * FROM %s LIMIT 1" % (table,))
    allFields = set(x.lower() for x in cu.fields())
    for column in columns:
        if column.lower() in allFields:
            cu.execute("ALTER TABLE %s DROP %s" % (table, column))
    return True


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


def rebuild_table(db, table, fieldsOut, fieldsIn=None, skipDropIndex=False):
    """
    SQLite offers no way to alter, drop, or change constraints on columns.
    So instead we have to rename it out of the way, build a new table, and
    drop the old one.
    """
    cu = db.cursor()

    tmpTable = None
    if table in db.tables:
        for index in list(db.tables[table]):
            if not skipDropIndex:
                db.dropIndex(table, index)

        tmpTable = table + '_tmp'
        cu.execute("ALTER TABLE %s RENAME TO %s" % (table, tmpTable))
        del db.tables[table]

    schema.createSchema(db, doCommit=False)

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

def createTable2(db, name, definition):
    return schema.createTable(db, name, definition)

def columnExists(db, table, name):
    cu = db.cursor()
    cu.execute("""
        SELECT COUNT(*)
        FROM pg_attribute a
        JOIN pg_class t ON t.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE t.relkind = 'r' AND n.nspname = 'public'
        AND t.relname = ? AND a.attname = ?
        """, table, name)
    return bool(cu.fetchone()[0])


def constraintExists(db, table, name):
    cu = db.cursor()
    cu.execute("""
        SELECT COUNT(*)
        FROM pg_constraint r
        JOIN pg_class t ON t.oid = r.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE t.relkind = 'r' AND n.nspname = 'public'
        AND t.relname = ? AND r.conname = ?
        """, table, name)
    return bool(cu.fetchone()[0])


def renameConstraint(db, table, oldName, newDefinition, conditional=False):
    if constraintExists(db, table, oldName):
        cu = db.cursor()
        cu.execute('ALTER TABLE "%s" DROP CONSTRAINT "%s", %s' % (table,
            oldName, newDefinition))
    elif not conditional:
        raise RuntimeError("Constraint %r on table %r does not exist" %
                (oldName, table))


def quoteIdentifier(name):
    name = name.replace('"', '""')
    return '"%s"' % (name,)


def findForeignKey(db, table, columns):
    """Return the name of a foreign key in the given table and consisting of
    the named columns."""
    cu = db.cursor()
    # Map column names to attribute numbers
    cu.execute("""
        SELECT t.oid, a.attnum, a.attname
        FROM pg_catalog.pg_class t
        JOIN pg_catalog.pg_namespace n ON t.relnamespace = n.oid
        JOIN pg_attribute a ON a.attrelid = t.oid
        WHERE n.nspname = 'public' AND t.relname = ? AND a.attnum > 0
        ORDER BY a.attnum ASC
        """, (table,))
    result = cu.fetchall()
    if not result:
        raise RuntimeError("Missing table %s" % table)
    oid = result[0][0]
    colMap = dict((name, num) for (oid, num, name) in result)
    try:
        colIds = sorted(colMap[colName] for colName in columns)
    except KeyError:
        raise RuntimeError("Missing one or more columns in table %s" % table)
    keyStr = '{' + (','.join(str(x) for x in colIds)) + '}'

    # Look for matching foreign keys
    cu.execute("""
        SELECT c.conname FROM pg_constraint c
        WHERE c.conrelid = ? AND c.contype = 'f'
        AND c.conkey = ?
        """, (oid, keyStr))
    result = cu.fetchone()
    if result:
        return result[0]
    else:
        raise RuntimeError("No matching constraint in table %s" % table)


def dropForeignKey(db, table, columns):
    """Drop a foreign key given the table name and included columns."""
    name = findForeignKey(db, table, columns)
    cu = db.cursor()
    cu.execute("ALTER TABLE %s DROP CONSTRAINT %s" %
            (quoteIdentifier(table), quoteIdentifier(name)))
    return name


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
        migrateFunc = _getMigration(int(version.major)+1)
        newVersion = tryMigrate(db, migrateFunc(db, cfg))
        assert(newVersion.major == version.major+1)
        version = newVersion
    return version


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
                WHERE external AND label LIKE ?""", '%s@%%' % host)

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
                import json
                cu.execute("""INSERT INTO Targets (targetType, targetName)
                        VALUES('ec2', 'aws')""")
                targetId = cu.lastid()
                for name, value in amiData.iteritems():
                    value = json.dumps(value)
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
        # contentSources=False is required here because the content sources
        # table hasn't been created yet.
        for repos in manager._iterRepositories('', (), contentSources=False):
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
        db = self.db
        cu = self.db.cursor()

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

        cu.execute("""
            CREATE TABLE PlatformsContentSourceTypes (
                platformId  integer NOT NULL
                    REFERENCES platforms ON DELETE CASCADE,
                contentSourceType  varchar(255) NOT NULL
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['PlatformsContentSourceTypes'] = []
        db.createIndex('PlatformsContentSourceTypes',
                'PlatformsContentSourceTypes_platformId_contentSourceType_uq',
                'platformId,contentSourceType', unique = True)

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
                'platformSourceId,defaultSource', unique = True)
        db.createIndex('PlatformSources',
                'PlatformSources_platformSourceId_orderIndex_uq',
                'platformSourceId,orderIndex', unique = True)

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

        cu.execute("""
            CREATE TABLE PlatformsPlatformSources (
                platformId          integer         NOT NULL
                    REFERENCES platforms ON DELETE CASCADE,
                platformSourceId    integer         NOT NULL
                    REFERENCES platformSources ON DELETE CASCADE
            ) %(TABLEOPTS)s""" % db.keywords)
        db.tables['PlatformsPlatformSources'] = []

        return True

    # 48.5
    # - Dashboard report type table
    def migrate5(self):
        return True

    # 48.6
    # - Dashboard Repository Log scraping table
    def migrate6(self):
        # OBSOLETE
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

        if self.cfg:
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
        db = self.db
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

        createTable(db, """
            CREATE TABLE job_types
            (
                job_type_id %(PRIMARYKEY)s,
                name VARCHAR NOT NULL UNIQUE,
                description VARCHAR NOT NULL
            )""")
        schema._addTableRows(db, 'job_types', 'name',
            [ dict(name="instance-launch", description='Instance Launch'),
              dict(name="platform-load", description='Platform Load'),
              dict(name="software-version-refresh", description='Software Version Refresh'), ])

        createTable(db, """
            CREATE TABLE job_states
            (
                job_state_id %(PRIMARYKEY)s,
                name VARCHAR NOT NULL UNIQUE
            )""")
        schema._addTableRows(db, 'job_states', 'name', [ dict(name='Queued'),
            dict(name='Running'), dict(name='Completed'), dict(name='Failed') ])

        createTable(db, """
            CREATE TABLE rest_methods
            (
                rest_method_id %(PRIMARYKEY)s,
                name VARCHAR NOT NULL UNIQUE
            )""")
        schema._addTableRows(db, 'rest_methods', 'name', [ dict(name='POST'),
            dict(name='PUT'), dict(name='DELETE') ])

        createTable(db, """
            CREATE TABLE jobs
            (
                job_id      %(PRIMARYKEY)s,
                job_type_id INTEGER NOT NULL
                    REFERENCES job_types ON DELETE CASCADE,
                job_state_id INTEGER NOT NULL
                    REFERENCES job_states ON DELETE CASCADE,
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
            )""")

        createTable(db, """
            CREATE TABLE job_history
            (
                job_history_id  %(PRIMARYKEY)s,
                -- job_history_type needed
                job_id          INTEGER NOT NULL
                    REFERENCES jobs ON DELETE CASCADE,
                timestamp   NUMERIC(14,3) NOT NULL,
                content     VARCHAR NOT NULL
            )""")

        createTable(db, """
            CREATE TABLE job_results
            (
                job_result_id   %(PRIMARYKEY)s,
                job_id          INTEGER NOT NULL
                    REFERENCES jobs ON DELETE CASCADE,
                data    VARCHAR NOT NULL
            )""")

        createTable(db, """
            CREATE TABLE job_target
            (
                job_id      INTEGER NOT NULL
                    REFERENCES jobs ON DELETE CASCADE,
                targetId    INTEGER NOT NULL
                    REFERENCES Targets ON DELETE CASCADE
            )""")

        createTable(db, """
            CREATE TABLE job_managed_system
            (
                job_id      INTEGER NOT NULL
                    REFERENCES jobs ON DELETE CASCADE,
                managed_system_id  INTEGER NOT NULL
                    REFERENCES inventory_managed_system ON DELETE CASCADE
            )""")

        db.loadSchema()
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
            changed |= self._addSystemStates0()

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
                    CONSTRAINT "inventory_system_network_system_id_dns_name_key"
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

        createTable(db, """
                CREATE TABLE TargetCredentials (
                    targetCredentialsId     %(PRIMARYKEY)s,
                    credentials             text NOT NULL UNIQUE
                )""")

        createTable(db, """
            CREATE TABLE "inventory_system_target_credentials" (
                "id" %(PRIMARYKEY)s,
                "system_id" INTEGER NOT NULL
                    REFERENCES "inventory_system" ("system_id")
                    ON DELETE CASCADE,
                "credentials_id" INTEGER NOT NULL
                    REFERENCES TargetCredentials (targetCredentialsId)
                    ON DELETE CASCADE
            )""")

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

        self._migrateTargetUserCredentials(cu)
        return True

    def _addSystemStates0(self):
        db = self.db
        changed = False
        changed |= schema._addTableRows(db, 'inventory_system_state', 'name',
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
                  FROM TargetCredentials
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
    Version = (51, 31)

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

    def _addSystemTypes5(self):
        db = self.db
        changed = False

        changed |= schema._addTableRows(db, 'inventory_system_type', 'name',
                [dict(name='inventory',
                      description='Inventory',
                      created_date=str(datetime.datetime.now(tz.tzutc())),
                      infrastructure=False,
                )])

        changed |= schema._addTableRows(db, 'inventory_system_type', 'name',
                [dict(name='infrastructure-management-node',
                      description='rPath Update Service (Infrastructure)',
                      created_date=str(datetime.datetime.now(tz.tzutc())),
                      infrastructure=True,
                )])

        changed |= schema._addTableRows(db, 'inventory_system_type', 'name',
                [dict(name='infrastructure-windows-build-node',
                      description='rPath Windows Build Service (Infrastructure)',
                      created_date=str(datetime.datetime.now(tz.tzutc())),
                      infrastructure=True,
                )])

        return changed

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
            changed |= self._addSystemTypes5()
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

    def migrate7(self):
        cu = self.db.cursor()

        cu.execute("""update inventory_management_interface set credentials_descriptor=? where name='wmi'""" , schema.wmi_credentials_descriptor)
        cu.execute("""update inventory_management_interface set credentials_descriptor=? where name='cim'""" , schema.cim_credentials_descriptor)

        return True

    def migrate8(self):
        cu = self.db.cursor()

        cu.execute("""update inventory_system_state set description='Initial synchronization pending' where name='registered'""")

        return True

    def migrate9(self):
        schema._addTableRows(self.db, 'inventory_system_state', 'name',
                [
                    dict(name="non-responsive-credentials", description="Not responding: Invalid credentials", created_date=str(datetime.datetime.now(tz.tzutc()))),
                ])
        return True

    def migrate10(self):
        add_columns(self.db, 'inventory_job',
            "status_code INTEGER NOT NULL DEFAULT 100",
            "status_text VARCHAR NOT NULL DEFAULT 'Initializing'",
            "status_detail VARCHAR",
        )
        return True

    def migrate11(self):
        schema._addTableRows(self.db, 'inventory_system_state', 'name',
                [
                    dict(name="unmanaged-credentials", description="Unmanaged: Invalid credentials", created_date=str(datetime.datetime.now(tz.tzutc()))),
                ])
        return True

    def migrate12(self):
        cu = self.db.cursor()

        cu.execute("""update inventory_management_interface set credentials_descriptor=? where name='wmi'""" , schema.wmi_credentials_descriptor)
        cu.execute("""update inventory_management_interface set credentials_descriptor=? where name='cim'""" , schema.cim_credentials_descriptor)

        return True

    def migrate13(self):
        cu = self.db.cursor()
        db = self.db

        if 'inventory_stage' not in db.tables:
            cu.execute("""
                CREATE TABLE "inventory_stage" (
                    "stage_id" %(PRIMARYKEY)s,
                    "name" varchar(256) NOT NULL,
                    "label" text NOT NULL,
                    "major_version_id" INTEGER REFERENCES
                        ProductVersions (productVersionId)
                )""" % db.keywords)
            db.tables['inventory_stage'] = []
            changed = True

        cu.execute("""
            ALTER TABLE "inventory_system"
            ADD "stage_id" INTEGER REFERENCES "inventory_stage" ("stage_id")
        """)

        cu.execute("""
            ALTER TABLE "inventory_system"
            ADD "major_version_id" INTEGER REFERENCES ProductVersions (productVersionId)
        """)

        cu.execute("""
            ALTER TABLE "inventory_system"
            ADD "appliance_id" INTEGER REFERENCES Projects (projectId)
        """)

        return changed

    def migrate14(self):
        cu = self.db.cursor()
        db = self.db

        cu.execute("""
            ALTER TABLE "inventory_system_type"
            ALTER "infrastructure" SET NOT NULL
        """)

        return True

    def migrate15(self):
        cu = self.db.cursor()
        db = self.db

        cu.execute("""
            ALTER TABLE "inventory_system"
            RENAME "type_id" to "system_type_id"
        """)

        return True

    def migrate16(self):
        cu = self.db.cursor()

        cu.execute("alter table inventory_system_type ADD COLUMN creation_descriptor text")
        cu.execute("""update inventory_system_type set creation_descriptor=? where name='inventory'""",
            schema.inventory_creation_descriptor)
        cu.execute("""update inventory_system_type set creation_descriptor=? where name='infrastructure-management-node'""",
            schema.management_node_creation_descriptor)
        cu.execute("""update inventory_system_type set creation_descriptor=? where name='infrastructure-windows-build-node'""",
            schema.windows_build_node_creation_descriptor)

        return True

    def migrate17(self):
        # Add platformName as nullable, fill it in with the label, then set to
        # not null
        add_columns(self.db, 'Platforms',
            'platformName    varchar(1024)',
            'configurable    boolean NOT NULL DEFAULT false',
            'abstract        boolean NOT NULL DEFAULT false',
            'time_refreshed  timestamp with time zone NOT NULL DEFAULT current_timestamp',
        )

        cu = self.db.cursor()
        cu.execute("UPDATE Platforms SET platformName = label")
        cu.execute("ALTER TABLE Platforms ALTER COLUMN platformName SET NOT NULL")
        return True

    def migrate18(self):
        # Add isFromDisk, by default false - set to True only for platforms
        # provided by the rbuilder
        add_columns(self.db, 'Platforms',
            'isFromDisk      boolean NOT NULL DEFAULT false',
        )

        if self.cfg is None:
            # Skip data mangling in migration tests
            return True

        class Plat(object):
            __slots__ = ['platformName', 'abstract', 'configurable',
                'isFromDisk']
            def __init__(self, **kwargs):
                for slotName in self.__slots__:
                    setattr(self, slotName, kwargs.get(slotName, None))
                self.isFromDisk = False

        cu = self.db.cursor()
        sql = """UPDATE Platforms
            SET platformName=?, abstract=?, configurable=?, isFromDisk=?
            WHERE label=?
        """
        platformsString = """
rhel.rpath.com@rpath:rhel-4-as,Red Hat Enterprise Linux 4,0,1
rhel.rpath.com@rpath:rhel-5-server,Red Hat Enterprise Linux 5,0,1
rhel.rpath.com@rpath:rhel-5-client-workstation,Red Hat Enterprise Linux Desktop Workstation 5,0,1
sles.rpath.com@rpath:sles-10sp3,Encapsulated SLES 10 Delivered by rPath,0,1
centos.rpath.com@rpath:centos-5e,Encapsulated CentOS 5 Delivered by rPath,0,1
conary.rpath.com@rpl:2,rPath Linux 2,0,0
windows.rpath.com@rpath:windows-common,Windows Foundation Platform,1,0
"""
        platforms = {}
        for row in platformsString.split('\n'):
            row = row.strip()
            if not row:
                continue
            arr = [ x.strip() for x in row.split(',') ]
            label, platformName, abstract, configurable = (arr[0], arr[1],
                bool(int(arr[2])), bool(int(arr[3])))
            platforms[label] = Plat(platformName=platformName,
                abstract=abstract, configurable=configurable, isFromDisk=True)
        for label, platformName in zip(self.cfg.availablePlatforms,
                                               self.cfg.availablePlatformNames):
            platforms[label] = Plat(platformName=platformName)
        for label in self.cfg.configurablePlatforms:
            plat = platforms.get(label, None)
            if plat is None:
                continue
            plat.configurable = True
        for label in self.cfg.abstractPlatforms:
            plat = platforms.get(label, None)
            if plat is None:
                continue
            plat.abstract = True
        for label, plat in platforms.items():
            cu.execute(sql, (plat.platformName, bool(plat.abstract),
                bool(plat.configurable), plat.isFromDisk, label))
        return True

    def migrate19(self):
        cu = self.db.cursor()

        cu.execute("ALTER TABLE inventory_system ADD COLUMN configuration text")
        return True

    def migrate20(self):
        cu = self.db.cursor()

        cu.execute("""
            UPDATE "inventory_event_type"
            SET "description" = 'System registration'
            WHERE "name" = 'system registration'
        """)
        cu.execute("""
            UPDATE "inventory_event_type"
            SET "description" = 'System sychnorization'
            WHERE "name" = 'system poll'
        """)
        cu.execute("""
            UPDATE "inventory_event_type"
            SET "description" = 'On-demand system synchronization'
            WHERE "name" = 'immediate system poll'
        """)
        cu.execute("""
            UPDATE "inventory_event_type"
            SET "description" = 'Scheduled system update'
            WHERE "name" = 'system apply update'
        """)
        cu.execute("""
            UPDATE "inventory_event_type"
            SET "description" = 'System update'
            WHERE "name" = 'immediate system apply update'
        """)
        cu.execute("""
            UPDATE "inventory_event_type"
            SET "description" = 'Scheduled system shutdown'
            WHERE "name" = 'system shutdown'
        """)
        cu.execute("""
            UPDATE "inventory_event_type"
            SET "description" = 'System shutdown'
            WHERE "name" = 'immediate system shutdown'
        """)
        cu.execute("""
            UPDATE "inventory_event_type"
            SET "description" = 'Launched system network data discovery'
            WHERE "name" = 'system launch wait'
        """)
        cu.execute("""
            UPDATE "inventory_event_type"
            SET "description" = 'System management interface detection'
            WHERE "name" = 'system detect management interface'
        """)
        cu.execute("""
            UPDATE "inventory_event_type"
            SET "description" = 'On-demand system management interface detection'
            WHERE "name" = 'immediate system detect management interface'
        """)

        return True

    def migrate21(self):
        cu = self.db.cursor()

        cu.execute("""
            INSERT INTO "inventory_event_type"
                ("name", "description", "priority")
            VALUES
                ('immediate system configuration',
                 'Update system configuration',
                 105)
        """)

        return True

    def migrate22(self):
        cu = self.db.cursor()
        cu.execute("ALTER TABLE Builds ADD job_uuid uuid")
        return True

    def migrate23(self):
        drop_tables(self.db, 'LaunchedAMIs', 'BlessedAMIs')
        return True

    def migrate24(self):
        cu = self.db.cursor()

        # descriptors were updated
        cu.execute("""update inventory_system_type set creation_descriptor=? where name='inventory'""",
            schema.inventory_creation_descriptor)
        cu.execute("""update inventory_system_type set creation_descriptor=? where name='infrastructure-management-node'""",
            schema.management_node_creation_descriptor)
        cu.execute("""update inventory_system_type set creation_descriptor=? where name='infrastructure-windows-build-node'""",
            schema.windows_build_node_creation_descriptor)

        return True

    def migrate25(self):
        cu = self.db.cursor()
        db = self.db

        if 'django_site' not in db.tables:
            cu.execute("""
                CREATE TABLE "django_site" (
                    "id" %(PRIMARYKEY)s,
                    "domain" VARCHAR(100) NOT NULL UNIQUE,
                    "name" VARCHAR(100) NOT NULL UNIQUE
                )""" % db.keywords)
            db.tables['django_site'] = []
            changed = True
            changed |= schema._addTableRows(db, 'django_site', 'name',
                [
                    dict(id=1, domain="rbuilder.inventory", name="rBuilder Inventory")])

        if 'django_redirect' not in db.tables:
            cu.execute("""
                CREATE TABLE "django_redirect" (
                    "id" %(PRIMARYKEY)s,
                    "site_id" INTEGER NOT NULL UNIQUE
                        REFERENCES "django_site" ("id"),
                    "old_path" VARCHAR(200) NOT NULL UNIQUE,
                    "new_path" VARCHAR(200) NOT NULL
                )""" % db.keywords)
            db.tables['django_redirect'] = []
            changed = True

        return True

    def migrate26(self):
        cu = self.db.cursor()

        cu.execute("""
            ALTER TABLE inventory_system
            DROP CONSTRAINT inventory_system_target_id_fkey
        """)
        cu.execute("""
            ALTER TABLE inventory_system
            ADD CONSTRAINT inventory_system_target_id_fkey
            FOREIGN KEY (target_id)
            REFERENCES targets(targetid) ON DELETE SET NULL
        """)

        return True


    def migrate27(self):
        cu = self.db.cursor()

        cu.execute("""
            ALTER TABLE "inventory_system_network"
            ALTER "ipv6_address" TYPE TEXT
        """)

        return True

    def migrate28(self):
        cu = self.db.cursor()

        cu.execute("""
            ALTER TABLE "django_redirect"
            DROP CONSTRAINT "django_redirect_site_id_key"
        """)

        return True

    def migrate29(self):
        cu = self.db.cursor()

        # descriptors were updated
        cu.execute("""update inventory_system_type set creation_descriptor=? where name='inventory'""",
            schema.inventory_creation_descriptor)
        cu.execute("""update inventory_system_type set creation_descriptor=? where name='infrastructure-management-node'""",
            schema.management_node_creation_descriptor)
        cu.execute("""update inventory_system_type set creation_descriptor=? where name='infrastructure-windows-build-node'""",
            schema.windows_build_node_creation_descriptor)

        return True

    def migrate30(self):
        cu = self.db.cursor()

        cu.execute("""
            ALTER TABLE "inventory_system_network"
            DROP CONSTRAINT "inventory_system_network_system_id_dns_name_key"
        """)

        return True

    def migrate31(self):
        """Post-5.8.0 schema fixups"""
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE inventory_system_type
            ALTER creation_descriptor SET NOT NULL
            """)
        cu.execute("""
            UPDATE inventory_event_type
            SET description = 'System synchronization'
            WHERE name = 'system poll'
            """)

        if not columnExists(self.db, "inventory_system_event", "event_data"):
            cu.execute("""
                ALTER TABLE inventory_system_event
                ADD event_data varchar
                """)
        if not constraintExists(self.db, "inventory_system_target_credentials",
                "inventory_system_target_credentials_system_id_key"):
            cu.execute("""
                ALTER TABLE inventory_system_target_credentials
                ADD CONSTRAINT inventory_system_target_credentials_system_id_key
                UNIQUE ( system_id, credentials_id )
                """)
        renameConstraint(self.db, table="inventory_system",
                oldName="inventory_system_type_id_fkey",
                newDefinition="""
                ADD CONSTRAINT inventory_system_system_type_id_fkey
                    FOREIGN KEY ( system_type_id )
                    REFERENCES inventory_system_type
                """,
                conditional=True)
        return True

class MigrateTo_52(SchemaMigration):
    Version = (52, 3)

    def migrate(self):
        return True

    def migrate1(self):
        createTable(self.db, """
                CREATE TABLE TargetImagesDeployed (
                    id              %(PRIMARYKEY)s,
                    targetId        integer             NOT NULL
                        REFERENCES Targets ON DELETE CASCADE,
                    fileId          integer             NOT NULL
                        REFERENCES BuildFiles ON DELETE CASCADE,
                    targetImageId   varchar(128)        NOT NULL
                ) %(TABLEOPTS)s""")
        return True

    def migrate2(self):
        cursor = self.db.cursor()
        cursor.execute("""
            ALTER TABLE inventory_system
                DROP CONSTRAINT inventory_system_generated_uuid_key""")
        return True

    def migrate3(self):
        cursor = self.db.cursor()
        cursor.execute("""
            ALTER TABLE inventory_trove
            ADD out_of_date BOOL
        """)

        # Invalidate trove update cache so that all updates will be recomputed
        cursor.execute("""
            UPDATE inventory_trove
            SET last_available_update_refresh = NULL
        """)

        return True

class MigrateTo_53(SchemaMigration):
    Version = (53, 6)

    def migrate(self):
        db = self.db

        schema.createTable(db, 'querysets_queryset', """
            CREATE TABLE "querysets_queryset" (
                "query_set_id" %(PRIMARYKEY)s,
                "name" TEXT NOT NULL UNIQUE,
                "created_date" TIMESTAMP WITH TIME ZONE NOT NULL,
                "modified_date" TIMESTAMP WITH TIME ZONE NOT NULL,
                "resource_type" TEXT NOT NULL
            )""")
        schema._addTableRows(db, "querysets_queryset", "name",
            [dict(name="All Systems", resource_type="system",
                created_date=str(datetime.datetime.now(tz.tzutc())),
                modified_date=str(datetime.datetime.now(tz.tzutc()))),
             dict(name="Active Systems", resource_type="system",
                created_date=str(datetime.datetime.now(tz.tzutc())),
                modified_date=str(datetime.datetime.now(tz.tzutc()))),
             dict(name="Inactive Systems", resource_type="system",
                created_date=str(datetime.datetime.now(tz.tzutc())),
                modified_date=str(datetime.datetime.now(tz.tzutc()))),
             dict(name="Physical Systems", resource_type="system",
                created_date=str(datetime.datetime.now(tz.tzutc())),
                modified_date=str(datetime.datetime.now(tz.tzutc()))),
            ])
        allQSId = schema._getRowPk(db, "querysets_queryset", "query_set_id",
            name="All Systems")
        activeQSId = schema._getRowPk(db, "querysets_queryset", "query_set_id",
            name="Active Systems")
        inactiveQSId = schema._getRowPk(db, "querysets_queryset", "query_set_id",
            name="Inactive Systems")
        physicalQSId = schema._getRowPk(db, "querysets_queryset", "query_set_id",
            name="Physical Systems")

        schema.createTable(db, 'querysets_filterentry', """
            CREATE TABLE "querysets_filterentry" (
                "filter_entry_id" %(PRIMARYKEY)s,
                "field" TEXT NOT NULL,
                "operator" TEXT NOT NULL,
                "value" TEXT,
                UNIQUE("field", "operator", "value")
            )""")
        schema._addTableRows(db, "querysets_filterentry",
            'filter_entry_id',
            [dict(field="current_state.name", operator="EQUAL", value="responsive"),
             dict(field="current_state.name", operator="IN",
                value="(unmanaged,unmanaged-credentials,registered,non-responsive-unknown,non-responsive-net,non-responsive-host,non-responsive-shutdown,non-responsive-suspended,non-responsive-credentials)"),
             dict(field="target", operator='IS_NULL', value="True")],
            ['field', 'operator', 'value'])
        activeFiltId = schema._getRowPk(db, "querysets_filterentry", 'filter_entry_id',
            field="current_state.name", operator="EQUAL", value="responsive")
        inactiveFiltId = schema._getRowPk(db, "querysets_filterentry", 'filter_entry_id',
            field="current_state.name", operator="IN",
                        value="(unmanaged,unmanaged-credentials,registered,non-responsive-unknown,non-responsive-net,non-responsive-host,non-responsive-shutdown,non-responsive-suspended,non-responsive-credentials)")
        physicalFiltId = schema._getRowPk(db, "querysets_filterentry", 'filter_entry_id',
            field="target", operator='IS_NULL', value="True")

        schema.createTable(db, 'querysets_querytag', """
            CREATE TABLE "querysets_querytag" (
                "query_tag_id" %(PRIMARYKEY)s,
                "query_set_id" INTEGER
                    REFERENCES "querysets_queryset" ("query_set_id")
                    ON DELETE CASCADE,
                "query_tag" TEXT NOT NULL UNIQUE
            )""")
        schema._addTableRows(db, "querysets_querytag", "query_tag",
            [dict(query_set_id=allQSId, query_tag="query-tag-All Systems-1"),
             dict(query_set_id=activeQSId, query_tag="query-tag-Active Systems-2"),
             dict(query_set_id=inactiveQSId, query_tag="query-tag-Inactive Systems-3"),
             dict(query_set_id=physicalQSId, query_tag="query-tag-Physical Systems-4"),
            ])

        schema.createTable(db, 'querysets_inclusionmethod', """
            CREATE TABLE "querysets_inclusionmethod" (
                "inclusion_method_id" %(PRIMARYKEY)s,
                "inclusion_method" TEXT NOT NULL UNIQUE
            )""")
        schema._addTableRows(db, "querysets_inclusionmethod",
            "inclusion_method",
            [dict(inclusion_method="chosen"),
             dict(inclusion_method="filtered")])

        schema.createTable(db, 'querysets_systemtag', """
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

        schema.createTable(db, "querysets_queryset_filter_entries", """
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

        schema._addTableRows(db, "querysets_queryset_filter_entries",
            'id',
            [dict(queryset_id=activeQSId, filterentry_id=activeFiltId),
             dict(queryset_id=inactiveQSId, filterentry_id=inactiveFiltId),
             dict(queryset_id=physicalQSId, filterentry_id=physicalFiltId)],
            ['queryset_id', 'filterentry_id'])

        schema.createTable(db, "querysets_queryset_children", """
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
        schema._addTableRows(db, "querysets_queryset_children",
            'id',
            [dict(from_queryset_id=allQSId, to_queryset_id=activeQSId),
             dict(from_queryset_id=allQSId, to_queryset_id=inactiveQSId)],
            uniqueCols=('from_queryset_id', 'to_queryset_id'))

        return True

    def migrate1(self):
        db = self.db

        schema.createTable(db, 'changelog_change_log', """
            CREATE TABLE "changelog_change_log" (
                "change_log_id" %(PRIMARYKEY)s,
                "resource_type" TEXT NOT NULL,
                "resource_id" INTEGER NOT NULL
            )""")

        schema.createTable(db, 'changelog_change_log_entry', """
            CREATE TABLE "changelog_change_log_entry" (
                "change_log_entry_id" %(PRIMARYKEY)s,
                "change_log_id" INTEGER
                    REFERENCES "changelog_change_log" ("change_log_id")
                    ON DELETE CASCADE NOT NULL,
                "entry_text" TEXT NOT NULL,
                "entry_date" TIMESTAMP WITH TIME ZONE NOT NULL
            )""")

        return True

    def migrate2(self):
        cursor = self.db.cursor()
        cursor.execute("""
            ALTER TABLE "querysets_queryset"
            ADD COLUMN "description" TEXT
        """)
        cursor.execute("""
            UPDATE "querysets_queryset"
            SET "description" = "name"
        """)

        return True

    def migrate3(self):
        cursor = self.db.cursor()
        cursor.execute("""
            ALTER TABLE "querysets_queryset"
            ADD COLUMN "can_modify" BOOLEAN NOT NULL DEFAULT TRUE
        """)
        cursor.execute("""
            UPDATE "querysets_queryset" SET "can_modify" = false
        """)

        return True

    def migrate4(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE inventory_stage
            DROP CONSTRAINT inventory_stage_major_version_id_fkey
        """)
        cu.execute("""
            ALTER TABLE inventory_stage
            ADD CONSTRAINT inventory_stage_major_version_id_fkey
            FOREIGN KEY (major_version_id)
            REFERENCES productversions(productversionid) ON DELETE SET NULL
        """)

        return True

    def migrate5(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE querysets_querytag
            RENAME query_tag to name
        """)

        cu.execute("""
            ALTER TABLE querysets_inclusionmethod
            RENAME inclusion_method to name
        """)

        cu.execute("""
            UPDATE querysets_querytag
            SET name='query-tag-All_Systems-1'
            WHERE name='query-tag-All Systems-1'
        """)
        cu.execute("""
            UPDATE querysets_querytag
            SET name='query-tag-Active_Systems-2'
            WHERE name='query-tag-Active Systems-2'
        """)
        cu.execute("""
            UPDATE querysets_querytag
            SET name='query-tag-Inactive_Systems-3'
            WHERE name='query-tag-Inactive Systems-3'
        """)
        cu.execute("""
            UPDATE querysets_querytag
            SET name='query-tag-Physical_Systems-4'
            WHERE name='query-tag-Physical Systems-4'
        """)

        cu.execute("""
            ALTER TABLE querysets_querytag
            ADD CONSTRAINT querysets_querytag_query_set_id_uq
            UNIQUE (query_set_id)
        """)

        cu.execute("""
            ALTER TABLE querysets_querytag
            ALTER query_set_id SET NOT NULL
        """)

        return True

    def migrate6(self):
        cu = self.db.cursor()
        if not columnExists(self.db, "inventory_trove", "out_of_date"):
            cu.execute("""
                ALTER TABLE inventory_trove
                ADD out_of_date BOOL
            """)

        # Invalidate trove update cache so that all updates will be recomputed
        cu.execute("""
            UPDATE inventory_trove
            SET last_available_update_refresh = NULL
        """)

        return True

class MigrateTo_54(SchemaMigration):
    Version = (54, 0)

    def migrate(self):
        return True

class MigrateTo_55(SchemaMigration):
    Version = (55, 3)

    def migrate(self):
        return True

    def migrate1(self):
        cu = self.db.cursor()
        cu.execute("UPDATE inventory_event_type SET priority=70 WHERE name = 'system registration'")
        return True

    def migrate2(self):
        # Add field for imported images. The best way to find that linkage post
        # facto is to look in the repository by SHA1, yecch.
        cu = self.db.cursor()
        cu.execute("ALTER TABLE Builds ADD output_trove text")

        # Skip the computed part if we're running a test or initial schema.
        if not self.cfg:
            return True

        cu.execute("""SELECT fqdn, buildId, sha1 FROM Builds
            JOIN BuildFiles USING (buildId)
            JOIN Projects USING (projectId)
            WHERE troveVersion = '/local@local:COOK/0.100:1-1-1'""")
        buildsBySha1ByProject = {}
        for fqdn, buildId, sha1 in cu:
            buildsBySha1ByProject.setdefault(fqdn, {}
                    ).setdefault(sha1, set()).add(buildId)

        manager = repository.RepositoryManager(self.cfg, self.db, bypass=True)
        client = manager.getClient(userId=repository.ANY_READER)
        repos = client.repos
        updates = []
        for fqdn, buildsBySha1 in buildsBySha1ByProject.items():
            # Get latest versions of all troves, then filter to just the
            # image-foo troves
            leaves = repos.getAllTroveLeaves(fqdn, {})
            allQuery = {}
            for name, versions in leaves.iteritems():
                if not name.startswith('image-'):
                    continue
                for version in versions:
                    allQuery.setdefault(name, {})[version.trailingLabel()
                            ] = None
            if not allQuery:
                manager.reset()
                continue
            # Get all versions of all image troves
            allVersions = repos.getTroveVersionsByLabel(allQuery)
            allJobs = set()
            for name, versions in allVersions.iteritems():
                for version, flavors in versions.items():
                    for flavor in flavors:
                        allJobs.add(
                                (name, (None, None), (version, flavor), True))
            # Get changeset of all image troves with files but not contents.
            # Map contents SHA-1 back to the trove tuple.
            allJobs = sorted(allJobs)
            cs = repos.createChangeSet(allJobs, withFiles=True,
                    withFileContents=False, recurse=False)
            troveSpecsBySha1 = {}
            for name, _, (version, flavor), _ in allJobs:
                try:
                    trvCs = cs.getNewTroveVersion(name, version, flavor)
                except KeyError:
                    # Trove is missing
                    continue
                if trvCs.getTroveInfo().factory() != 'rbuilder-image':
                    # Not an imported image
                    continue
                for pathId, path, fileId, fileVer in trvCs.getNewFileList():
                    fileStreamBlob = cs.getFileChange(None, fileId)
                    fileStream = cny_files.ThawFile(fileStreamBlob, pathId)
                    sha1 = fileStream.contents.sha1()
                    if sha1:
                        sha1 = sha1.encode('hex')
                        tup = '%s=%s' % (name, version)
                        troveSpecsBySha1.setdefault(sha1, set()
                                ).add((version, tup))
            manager.reset()

            for sha1, buildIds in buildsBySha1.items():
                tups = troveSpecsBySha1.get(sha1)
                if not tups:
                    continue
                # Pick latest version if more than one trove had that SHA-1
                tup = sorted(tups)[-1][1]
                for buildId in buildIds:
                    updates.append((tup, buildId))

        if updates:
            cu.executemany("""UPDATE Builds SET output_trove = ?
                    WHERE buildId = ?""", updates)

        return True

    def migrate3(self):
        db = self.db
        schema._addTableRows(db, 'job_types', 'name',
        [
          dict(name="image-deployment", description="Image Deployment"),
        ])
        return True

class MigrateTo_56(SchemaMigration):
    Version = (56, 2)

    def migrate(self):
        return True

    def migrate1(self):
        db = self.db
        createTable = schema.createTable
        changed = False

        changed |= createTable(db, "packages_package_action_type", """
            CREATE TABLE "packages_package_action_type" (
                "package_action_type_id" %(PRIMARYKEY)s,
                "name" text NOT NULL,
                "description" text NOT NULL,
                "created_date" timestamp with time zone NOT NULL,
                "modified_date" timestamp with time zone NOT NULL
            )""")

        changed |= createTable(db, "packages_package", """
            CREATE TABLE "packages_package" (
                "package_id" %(PRIMARYKEY)s,
                "name" TEXT NOT NULL UNIQUE,
                "description" TEXT,
                "created_date" TIMESTAMP WITH TIME ZONE NOT NULL,
                "modified_date" TIMESTAMP WITH TIME ZONE NOT NULL,
                "created_by_id" INTEGER
                    REFERENCES "users" ("userid"),
                "modified_by_id" INTEGER
                    REFERENCES "users" ("userid")
            )""")

        changed |= createTable(db, "packages_package_version", """
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

        changed |= createTable(db, "packages_package_version_action", """
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

        changed |= createTable(db, "packages_package_version_job", """
            CREATE TABLE "packages_package_version_job" (
                "package_version_job_id" %(PRIMARYKEY)s,
                "package_version_id" integer NOT NULL
                    REFERENCES "packages_package_version" ("package_version_id"),
                "package_action_type_id" integer NOT NULL
                    REFERENCES "packages_package_action_type"
                        ("package_action_type_id"),
                "job_id" integer
                    REFERENCES "inventory_job" ("job_id"),
                "job_data" text,
                "created_date" timestamp with time zone NOT NULL,
                "modified_date" timestamp with time zone NOT NULL,
                "created_by_id" integer
                    REFERENCES "users" ("userid"),
                "modified_by_id" integer
                    REFERENCES "users" ("userid")
            )""")

        changed |= createTable(db, "packages_package_version_url", """
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

        changed |= createTable(db, "packages_package_source", """
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

        changed |= createTable(db, "packages_package_source_action", """
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

        changed |= createTable(db, "packages_package_source_job", """
            CREATE TABLE "packages_package_source_job" (
                "package_source_job_id" %(PRIMARYKEY)s,
                "package_source_id" integer NOT NULL
                    REFERENCES "packages_package_source" ("package_source_id"),
                "package_action_type_id" integer NOT NULL
                    REFERENCES "packages_package_action_type"
                        ("package_action_type_id"),
                "job_id" integer
                    REFERENCES "inventory_job" ("job_id"),
                "job_data" text,
                "created_date" timestamp with time zone NOT NULL,
                "modified_date" timestamp with time zone NOT NULL,
                "created_by_id" integer
                    REFERENCES "users" ("userid"),
                "modified_by_id" integer
                    REFERENCES "users" ("userid")
            )""")

        changed |= createTable(db, "packages_package_build", """
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

        changed |= createTable(db, "packages_package_build_troves", """
            CREATE TABLE "packages_package_build_troves" (
                "id" %(PRIMARYKEY)s,
                "packagebuild_id" integer NOT NULL
                    REFERENCES "packages_package_build" ("package_build_id"),
                "trove_id" integer NOT NULL
                    REFERENCES "inventory_trove" ("trove_id"),
                UNIQUE ("packagebuild_id", "trove_id")
            )""")

        changed |= createTable(db, "packages_package_build_action", """
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

        changed |= createTable(db, "packages_package_build_job", """
            CREATE TABLE "packages_package_build_job" (
                "package_build_job_id" %(PRIMARYKEY)s,
                "package_build_id" integer NOT NULL
                    REFERENCES "packages_package_build" ("package_build_id"),
                "package_action_type_id" integer NOT NULL,
                "job_id" integer
                    REFERENCES "inventory_job" ("job_id"),
                "job_data" text,
                "created_date" timestamp with time zone NOT NULL,
                "modified_date" timestamp with time zone NOT NULL,
                "created_by_id" integer
                    REFERENCES "users" ("userid"),
                "modified_by_id" integer
                    REFERENCES "users" ("userid")
            )""")

        changed |= db.createIndex("packages_package",
            "packages_package_created_by_id", "created_by_id")
        changed |= db.createIndex("packages_package",
            "packages_package_modified_by_id", "modified_by_id")
        changed |= db.createIndex("packages_package_version",
            "packages_package_version_package_id", "package_id")
        changed |= db.createIndex("packages_package_version",
            "packages_package_version_created_by_id", "created_by_id")
        changed |= db.createIndex("packages_package_version_action",
            "packages_package_version_action_package_version_id", "package_version_id")
        changed |= db.createIndex("packages_package_version_action",
            "packages_package_version_action_package_action_type_id", "package_action_type_id")
        changed |= db.createIndex("packages_package_version_job",
            "packages_package_version_job_package_version_id", "package_version_id")
        changed |= db.createIndex("packages_package_version_job",
            "packages_package_version_job_package_action_type_id", "package_action_type_id")
        changed |= db.createIndex("packages_package_version_job",
            "packages_package_version_job_job_id", "job_id")
        changed |= db.createIndex("packages_package_version_job",
            "packages_package_version_job_created_by_id", "created_by_id")
        changed |= db.createIndex("packages_package_version_job",
            "packages_package_version_job_modified_by_id", "modified_by_id")
        changed |= db.createIndex("packages_package_version_url",
            "packages_package_version_url_package_version_id", "package_version_id")
        changed |= db.createIndex("packages_package_version_url",
            "packages_package_version_url_created_by_id", "created_by_id")
        changed |= db.createIndex("packages_package_version_url",
            "packages_package_version_url_modified_by_id", "modified_by_id")
        changed |= db.createIndex("packages_package_source",
            "packages_package_source_package_version_id", "package_version_id")
        changed |= db.createIndex("packages_package_source",
            "packages_package_source_created_by_id", "created_by_id")
        changed |= db.createIndex("packages_package_source",
            "packages_package_source_modified_by_id", "modified_by_id")
        changed |= db.createIndex("packages_package_source",
            "packages_package_source_trove_id", "trove_id")
        changed |= db.createIndex("packages_package_source_action",
            "packages_package_source_action_package_source_id", "package_source_id")
        changed |= db.createIndex("packages_package_source_action",
            "packages_package_source_action_package_action_type_id", "package_action_type_id")
        changed |= db.createIndex("packages_package_source_job",
            "packages_package_source_job_package_source_id", "package_source_id")
        changed |= db.createIndex("packages_package_source_job",
            "packages_package_source_job_package_action_type_id", "package_action_type_id")
        changed |= db.createIndex("packages_package_source_job",
            "packages_package_source_job_job_id", "job_id")
        changed |= db.createIndex("packages_package_source_job",
            "packages_package_source_job_created_by_id", "created_by_id")
        changed |= db.createIndex("packages_package_source_job",
            "packages_package_source_job_modified_by_id", "modified_by_id")
        changed |= db.createIndex("packages_package_build",
            "packages_package_build_package_source_id", "package_source_id")
        changed |= db.createIndex("packages_package_build",
            "packages_package_build_created_by_id", "created_by_id")
        changed |= db.createIndex("packages_package_build",
            "packages_package_build_modified_by_id", "modified_by_id")
        changed |= db.createIndex("packages_package_build_action",
            "packages_package_build_action_package_build_id", "package_build_id")
        changed |= db.createIndex("packages_package_build_action",
            "packages_package_build_action_package_action_type_id", "package_action_type_id")
        changed |= db.createIndex("packages_package_build_job",
            "packages_package_build_job_package_build_id", "package_build_id")
        changed |= db.createIndex("packages_package_build_job",
            "packages_package_build_job_package_action_type_id", "package_action_type_id")
        changed |= db.createIndex("packages_package_build_job",
            "packages_package_build_job_job_id", "job_id")
        changed |= db.createIndex("packages_package_build_job",
            "packages_package_build_job_created_by_id", "created_by_id")
        changed |= db.createIndex("packages_package_build_job",
            "packages_package_build_job_modified_by_id", "modified_by_id")

        return True

    def migrate2(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE "inventory_job"
            RENAME TO "jobs_job"
        """)
        cu.execute("""
            ALTER TABLE "inventory_job_state"
            RENAME TO "jobs_job_state"
        """)

        return True

class MigrateTo_57(SchemaMigration):
    Version = (57, 0)

    def migrate(self):
        return True


class MigrateTo_58(SchemaMigration):
    Version = (58, 75)

    def migrate(self):
        return True

    def migrate1(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE "inventory_system"
            RENAME "appliance_id" TO "project_id"
        """)

        cu.execute("""
            ALTER TABLE "inventory_stage"
            RENAME "major_version_id" TO "project_version_id"
        """)


        cu.execute("""
            ALTER TABLE "inventory_stage"
            ADD "promotable" bool
        """)

        return True

    def migrate2(self):
        schema._addTableRows(self.db, "querysets_queryset", "name", [
        dict(name="All Users", resource_type='user',
              description='All users',
              created_date=str(datetime.datetime.now(tz.tzutc())),
              modified_date=str(datetime.datetime.now(tz.tzutc())),
              can_modify=False)
        ])

        schema._addTableRows(self.db, "querysets_filterentry",
            'filter_entry_id',
            [
             dict(field='user_name', operator='IS_NULL', value="False"),
             ],
            ['field', 'operator', 'value'])

        allUserFiltId = schema._getRowPk(self.db, "querysets_filterentry", 'filter_entry_id',
                field="user_name", operator='IS_NULL', value="False")

        allUserQSId = schema._getRowPk(self.db, "querysets_queryset", "query_set_id",
            name="All Users")

        schema._addTableRows(self.db, "querysets_querytag", "name",
             [dict(query_set_id=allUserQSId, name="query-tag-all_users-5"),
            ])

        schema._addTableRows(self.db, "querysets_queryset_filter_entries",
            'id',
            [
             dict(queryset_id=allUserQSId, filterentry_id=allUserFiltId),
             ],
            ['queryset_id', 'filterentry_id'])

        schema.createTable(self.db, 'querysets_usertag', """
            CREATE TABLE "querysets_usertag" (
                "user_tag_id" %(PRIMARYKEY)s,
                "user_id" INTEGER
                    REFERENCES "users" ("userid")
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
                UNIQUE ("user_id", "query_tag_id", "inclusion_method_id")
            )""")

        return True

    def migrate3(self):
        return True

    def migrate4(self):
        return True

    def migrate5(self):
        return True

    def migrate6(self):
        return True

    def migrate7(self):
        return True

    def migrate8(self):
        drop_columns(self.db, 'Users', 'isAdmin')
        return True

    def migrate9(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE querysets_queryset ADD COLUMN presentation_type TEXT""")
        schema._createInfrastructureSystemsQuerySetSchema(self.db, version=(58,9))
        schema._createWindowsBuildSystemsQuerySet(self.db, version=(58,9))
        schema._createUpdateSystemsQuerySet(self.db, version=(58,9))
        return True

    def migrate10(self):
        # no longer needed
        #schema._createAllProjectsQuerySetSchema(self.db)
        #schema._createExternalProjectsQuerySetSchema(self.db)
        return True

    def migrate11(self):
        createTable(self.db, """
            CREATE TABLE "querysets_projecttag" (
                "project_tag_id" %(PRIMARYKEY)s,
                "project_id" INTEGER
                    REFERENCES "projects" ("projectid")
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
                UNIQUE ("project_id", "query_tag_id", "inclusion_method_id")
            )""")
        return True

    def migrate12(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE inventory_stage RENAME TO project_branch_stage""")
        return True

    def migrate13(self):
        cu = self.db.cursor()
        cu.execute("""DELETE FROM querysets_queryset WHERE name='All Appliances'""")
        schema._createAllProjectBranchStages13(self.db, version=(58,13))

        createTable(self.db, """
            CREATE TABLE "querysets_stagetag" (
                "stage_tag_id" %(PRIMARYKEY)s,
                "stage_id" INTEGER
                    REFERENCES "project_branch_stage" ("stage_id")
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
                UNIQUE ("stage_id", "query_tag_id", "inclusion_method_id")
            )""")

        return True

    def migrate14(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE ProductVersions ALTER COLUMN projectId DROP NOT NULL""")
        return True

    def migrate15(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE ProductVersions ALTER COLUMN namespace DROP NOT NULL""")
        return True

    def migrate16(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE project_branch_stage
                ADD COLUMN created_date timestamp with time zone NOT NULL
                DEFAULT current_timestamp""")
        return True

    def migrate17(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE project_branch_stage RENAME COLUMN project_version_id TO project_branch_id""")
        return True

    def migrate18(self):
        cu = self.db.cursor()

        # remove old external appliances query set and filter
        cu.execute("""DELETE FROM querysets_queryset WHERE name='External Appliances'""")
        cu.execute("""DELETE FROM querysets_filterentry WHERE field='external' AND operator='EQUAL' AND value='1'""")
        cu.execute("""DELETE FROM querysets_filterentry WHERE field='is_appliance' AND operator='EQUAL' AND value='1'""")

        # add the filter terms for "all" in the set
        # NOTE: this is bad form for the future, always use system.name, ETC so we can migrate
        # them, not just "name"
        allFilterId = schema._addQuerySetFilterEntry(self.db, "name", "IS_NULL", "False")

        # get the all projects qs
        qsId = schema._getRowPk(self.db, "querysets_queryset", "query_set_id", name="All Projects")

        # link the all projects query set to the "all" filter
        schema._addTableRows(self.db, "querysets_queryset_filter_entries", 'id',
            [dict(queryset_id=qsId, filterentry_id=allFilterId)],
            ['queryset_id', 'filterentry_id'])

        return True

    def migrate19(self):
        cu = self.db.cursor()
        cu.execute("""UPDATE querysets_queryset SET presentation_type='project' WHERE name='All Projects'""")
        return True

    def migrate20(self):
        cu = self.db.cursor()
        cu.execute("""UPDATE querysets_queryset SET resource_type='project' WHERE name='All Projects'""")
        cu.execute("""UPDATE querysets_queryset SET presentation_type=NULL WHERE name='All Projects'""")
        schema._createAllProjectBranchStages(self.db, version=(58,20))
        return True

    def migrate21(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE project_branch_stage ADD COLUMN project_id integer
                      REFERENCES Projects (projectId) ON DELETE SET NULL""")
        return True

    def migrate22(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE Projects ALTER COLUMN disabled DROP DEFAULT""")
        cu.execute("""ALTER TABLE Projects ALTER COLUMN disabled TYPE BOOLEAN USING CASE WHEN disabled=0 THEN FALSE ELSE TRUE END""")
        cu.execute("""ALTER TABLE Projects ALTER COLUMN disabled SET DEFAULT FALSE""")

        cu.execute("""ALTER TABLE Projects ALTER COLUMN hidden DROP DEFAULT""")
        cu.execute("""ALTER TABLE Projects ALTER COLUMN hidden TYPE BOOLEAN USING CASE WHEN hidden=0 THEN FALSE ELSE TRUE END""")
        cu.execute("""ALTER TABLE Projects ALTER COLUMN hidden SET DEFAULT FALSE""")

        cu.execute("""ALTER TABLE Projects ALTER COLUMN external DROP DEFAULT""")
        cu.execute("""ALTER TABLE Projects ALTER COLUMN external TYPE BOOLEAN USING CASE WHEN external=0 THEN FALSE ELSE TRUE END""")
        cu.execute("""ALTER TABLE Projects ALTER COLUMN external SET DEFAULT FALSE""")

        cu.execute("""ALTER TABLE Projects ALTER COLUMN isAppliance DROP DEFAULT""")
        cu.execute("""ALTER TABLE Projects ALTER COLUMN isAppliance TYPE BOOLEAN USING CASE WHEN isAppliance=0 THEN FALSE ELSE TRUE END""")
        cu.execute("""ALTER TABLE Projects ALTER COLUMN isAppliance SET DEFAULT TRUE""")

        cu.execute("""ALTER TABLE Projects ALTER COLUMN backupExternal DROP DEFAULT""")
        cu.execute("""ALTER TABLE Projects ALTER COLUMN backupExternal TYPE BOOLEAN USING CASE WHEN backupExternal=0 THEN FALSE ELSE TRUE END""")
        cu.execute("""ALTER TABLE Projects ALTER COLUMN backupExternal SET DEFAULT FALSE""")

        return True

    def migrate23(self):
        cu = self.db.cursor()
        cu.execute("""
            INSERT INTO "inventory_event_type"
                ("name", "description", "priority")
            VALUES
                ('system assimilation',
                 'System Assimilation',
                 105)
        """)
        return True

    def migrate24(self):
        # URL and creds for local/mirror projects are redundant.
        cu = self.db.cursor()
        cu.execute("ALTER TABLE Labels ALTER url DROP NOT NULL")
        cu.execute("""UPDATE LABELS SET url = NULL, authtype = 'none',
            username = NULL, password = NULL, entitlement = NULL
            WHERE (SELECT database FROM projects
                WHERE Projects.projectId = Labels.projectId) IS NOT NULL""")
        # Drop unused table
        drop_tables(self.db, 'RepNameMap')
        return True

    def migrate25(self):
        # adding the stageid to the images(builds)
        cu = self.db.cursor()
        cu.execute("ALTER TABLE Builds ADD COLUMN stageid INTEGER REFERENCES project_branch_stage ON DELETE SET NULL")
        return True

    def migrate26(self):
        # Add missing ON DELETE clauses to FKs
        cu = self.db.cursor()
        dropForeignKey(self.db, "inventory_system", ["launching_user_id"])
        dropForeignKey(self.db, "inventory_system", ["stage_id"])
        dropForeignKey(self.db, "inventory_system", ["major_version_id"])
        dropForeignKey(self.db, "inventory_system", ["project_id"])
        cu.execute("""ALTER TABLE inventory_system
                ADD FOREIGN KEY (launching_user_id)
                    REFERENCES users(userid)
                    ON DELETE SET NULL,
                ADD FOREIGN KEY (stage_id)
                    REFERENCES "project_branch_stage" ("stage_id")
                    ON DELETE SET NULL,
                ADD FOREIGN KEY (major_version_id)
                    REFERENCES productversions(productversionid)
                    ON DELETE SET NULL,
                ADD FOREIGN KEY (project_id)
                    REFERENCES projects(projectid)
                    ON DELETE SET NULL""")
        dropForeignKey(self.db, "packages_package", ["created_by_id"])
        dropForeignKey(self.db, "packages_package", ["modified_by_id"])
        cu.execute("""ALTER TABLE packages_package
                ADD FOREIGN KEY (created_by_id)
                    REFERENCES users(userid)
                    ON DELETE SET NULL,
                ADD FOREIGN KEY (modified_by_id)
                    REFERENCES users(userid)
                    ON DELETE SET NULL""")
        return True

    def _rename_jobs_table(self):
        # Various mistakes were made in renaming this table (twice), so just
        # rerun this for all of the minor migrations involved until everything
        # settles. This way people who have installed or migrated all end up
        # with the right table.
        cu = self.db.cursor()
        for name in ('inventory_event_type', 'inventory_job_type'):
            if name in self.db.tables:
                cu.execute("ALTER TABLE %s RENAME TO jobs_job_type" % name)
                self.db.tables['jobs_job_type'] = self.db.tables.pop(name)
                break

    def migrate27(self):
        self._rename_jobs_table()
        return True

    def migrate28(self):
        self._rename_jobs_table()
        # adding the descriptor and descriptor_data to jobs_job
        cu = self.db.cursor()
        cu.execute("ALTER TABLE jobs_job ADD COLUMN descriptor VARCHAR")
        cu.execute("ALTER TABLE jobs_job ADD COLUMN descriptor_data VARCHAR")
        return True

    def migrate29(self):
        self._rename_jobs_table()
        # adding the column resource_type to jobs_job_type
        cu = self.db.cursor()
        cu.execute("ALTER TABLE jobs_job_type ADD COLUMN resource_type VARCHAR")
        return True

    def migrate30(self):
        self._rename_jobs_table()
        # This is the last migration with job_type problems
        cu = self.db.cursor()
        cu.execute("UPDATE jobs_job_type SET resource_type = 'System'")
        cu.execute("ALTER TABLE jobs_job_type ALTER resource_type SET NOT NULL")
        return True


    def migrate31(self):
        cu = self.db.cursor()
        cu.execute("ALTER TABLE builds ALTER stageid DROP NOT NULL")
        return True

    def migrate32(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE jobs_job_type RENAME COLUMN event_type_id TO job_type_id""")
        cu.execute("""ALTER TABLE jobs_job RENAME COLUMN event_type_id TO job_type_id""")
        cu.execute("""ALTER TABLE jobs_job ALTER job_type_id SET NOT NULL""")
        cu.execute("""ALTER TABLE inventory_system_event RENAME COLUMN event_type_id TO job_type_id""")
        return True

    def migrate33(self):
        # Add a serial primary key, drop the old pk, add it as unique for usergroupmembers table
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE UserGroupMembers
                DROP CONSTRAINT usergroupmembers_pkey""")
        cu.execute("""
            ALTER TABLE UserGroupMembers
                ADD COLUMN userGroupMemberId SERIAL PRIMARY KEY""")
        self.db.createIndex('UserGroupMembers', 'UserGroupMembersIdx',
            'userGroupId, userId', unique = True)
        return True

    def migrate34(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE users ALTER salt
                TYPE text USING encode(salt, 'hex')""")
        return True

    def migrate35(self):
        # Add a serial primary key, drop the old pk, add it as unique for targetdata table
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE TargetData
                DROP CONSTRAINT targetdata_pkey""")
        cu.execute("""
            ALTER TABLE TargetData
                ADD COLUMN targetdataId SERIAL PRIMARY KEY""")
        self.db.createIndex('TargetData', 'TargetDataIdx',
            'targetId, name', unique = True)
        return True

    def migrate36(self):
        cu = self.db.cursor()
        cu.execute("UPDATE jobs_job_type SET priority=70 WHERE name = 'system registration'")
        return True

    def migrate37(self):
        # Add a new management interface type (SSH)
        cu = self.db.cursor()
        cu.execute("""insert into inventory_management_interface (name, description, created_date, port, credentials_descriptor, credentials_readonly) values (?,?,now(),?,?,?)""" , 'ssh', 'Secure Shell (SSH)', 22, schema.ssh_credentials_descriptor, 'false')
        return True

    def migrate38(self):
        # Add Unique constraint to project and label in labels
        cu = self.db.cursor()
        cu.execute("ALTER TABLE Labels ALTER label DROP NOT NULL")
        cu.execute("UPDATE Labels SET label = NULL WHERE label = ''")
        cu.execute("""
            ALTER TABLE Labels
            ADD CONSTRAINT labels_project_id_uq
            UNIQUE (projectId)
        """)
        cu.execute("""
            ALTER TABLE Labels
            ADD CONSTRAINT labels_label_uq
            UNIQUE (label)
        """)
        return True

    def migrate39(self):
        cu = self.db.cursor()
        cu.execute("ALTER TABLE Labels ALTER label DROP NOT NULL")
        cu.execute("UPDATE Labels SET label = NULL WHERE label = ''")
        cu.execute("""ALTER TABLE Labels
            ADD CONSTRAINT label_not_empty CHECK (label != '')
            """)
        return True

    def migrate40(self):
        cu = self.db.cursor()
        cu.execute("ALTER TABLE Labels ALTER label DROP NOT NULL")
        return True

    def migrate41(self):
        cu = self.db.cursor()
        # Make ProductVersions.projectId NOT NULL
        cu.execute("DELETE FROM ProductVersions WHERE projectId IS NULL")
        cu.execute("ALTER TABLE ProductVersions ALTER projectId SET NOT NULL")
        # Add new columns for improved branch schema
        cu.execute("""ALTER TABLE ProductVersions
                ADD label text UNIQUE,
                ADD cache_key text""")
        cu.execute("""UPDATE ProductVersions v SET label =
            p.fqdn || '@' || v.namespace || ':' || p.shortname || '-' || v.name
            FROM Projects p WHERE p.projectid = v.projectid""")
        cu.execute("ALTER TABLE ProductVersions ALTER label SET NOT NULL")
        # Make project_branch_stage FKs NOT NULL and CASCADE
        cu.execute("""DELETE FROM project_branch_stage
                WHERE project_id IS NULL OR project_branch_id IS NULL""")
        dropForeignKey(self.db, 'project_branch_stage', ['project_id'])
        dropForeignKey(self.db, 'project_branch_stage', ['project_branch_id'])
        cu.execute("""ALTER TABLE project_branch_stage
            ADD FOREIGN KEY (project_id)
                REFERENCES Projects (projectId)
                ON DELETE CASCADE,
            ALTER project_id SET NOT NULL,
            ADD FOREIGN KEY (project_branch_id)
                REFERENCES ProductVersions (productVersionId)
                ON DELETE CASCADE,
            ALTER project_branch_id SET NOT NULL
            """)

        # Fixups to make initial schema consistent with migrations.
        cu.execute("""ALTER TABLE jobs_job_type
                ALTER resource_type TYPE text""")
        cu.execute("""
            UPDATE "jobs_job_type"
            SET description = 'System assimilation'
            WHERE name = 'system assimilation'
        """)
        return True

    def migrate42(self):
        cu = self.db.cursor()
        cu.execute("""
            INSERT INTO "jobs_job_type"
                ("name", "description", "priority","resource_type")
            VALUES
                ('image builds',
                 'Image builds',
                 105,
                 'Image')
        """)
        return True

    def migrate43(self):
        '''Add RBAC schema items'''

        cu = self.db.cursor()
        cu.execute("""
        CREATE TABLE rbac_role (
            role_id      TEXT PRIMARY KEY
        ) %(TABLEOPTS)s""" % self.db.keywords)
        self.db.tables['rbac_role'] = []

        cu.execute("""
        CREATE TABLE rbac_context (
            context_id     TEXT PRIMARY KEY
        ) %(TABLEOPTS)s""" % self.db.keywords)
        self.db.tables['rbac_context'] = []

        cu.execute("""
        CREATE TABLE rbac_user_role (
            rbac_user_role_id  %(PRIMARYKEY)s,
            role_id      TEXT NOT NULL
               REFERENCES rbac_role (role_id)
               ON DELETE CASCADE
               ON UPDATE CASCADE,
            user_id      INTEGER NOT NULL
               REFERENCES Users (userId)
               ON DELETE CASCADE,
            UNIQUE ( "role_id", "user_id" )
        ) %(TABLEOPTS)s""" % self.db.keywords)
        self.db.tables['rbac_user_role'] = []

        cu.execute("""
        CREATE TABLE rbac_permission (
            permission_id   %(PRIMARYKEY)s,
            role_id         TEXT NOT NULL
               REFERENCES rbac_role (role_id)
               ON DELETE CASCADE
               ON UPDATE CASCADE,
            context_id      TEXT NOT NULL
               REFERENCES rbac_context (context_id)
               ON DELETE CASCADE
               ON UPDATE CASCADE,
            action          TEXT NOT NULL,
            UNIQUE ( "role_id", "context_id", "action" )
        ) %(TABLEOPTS)s""" % self.db.keywords)
        self.db.tables['rbac_permission'] = []

        cu.execute("""
        ALTER TABLE inventory_system ADD COLUMN
            "rbac_context_id" TEXT
             REFERENCES rbac_context (context_id)
             ON DELETE SET NULL
        """)
        self.db.createIndex('rbac_user_role', 'RbacUserRoleSearchIdx',
            'role_id, user_id')
        self.db.createIndex('rbac_permission', 'RbacPermissionSearchIdx',
            'role_id, context_id')
        self.db.createIndex('rbac_permission', 'RbacPermissionLookupIdx',
            'role_id, context_id, action')
        return True

    def migrate44(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE project_branch_stage
            ADD CONSTRAINT project_branch_stage_nameid_uq
                UNIQUE (project_branch_id, name)
        """)
        return True

    def migrate45(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE PlatformsContentSourceTypes
                ADD COLUMN contentSourceTypeId SERIAL PRIMARY KEY""")
        return True

    def migrate46(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE PlatformsPlatformSources
                ADD COLUMN platforms_platform_sources_id SERIAL PRIMARY KEY""")
        return True

    def migrate47(self):
        '''permissions use querysets not a seperate rbac_context entity'''
        cu = self.db.cursor()

        # remove old items (not shipped)
        cu.execute("DROP TABLE rbac_context CASCADE")
        cu.execute("DROP TABLE rbac_permission CASCADE")
        cu.execute("""
        ALTER TABLE inventory_system DROP COLUMN
            "rbac_context_id"
        """)

        # add new version
        cu.execute("""
        CREATE TABLE rbac_permission (
            permission_id   %(PRIMARYKEY)s,
            role_id         TEXT NOT NULL
               REFERENCES rbac_role (role_id)
               ON DELETE CASCADE
               ON UPDATE CASCADE,
            queryset_id      INTEGER NOT NULL
               REFERENCES querysets_queryset (query_set_id)
               ON DELETE CASCADE
               ON UPDATE CASCADE,
            action          TEXT NOT NULL,
            UNIQUE ( "role_id", "queryset_id", "action" )
        ) %(TABLEOPTS)s""" % self.db.keywords)
        self.db.tables['rbac_permission'] = []
        self.db.createIndex('rbac_user_role', 'RbacUserRoleSearchIdx',
            'user_id')
        self.db.createIndex('rbac_permission', 'RbacPermissionLookupIdx',
            'role_id, queryset_id, action')

        return True

    def migrate48(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE querysets_queryset
                ADD COLUMN "tagged_date" TIMESTAMP WITH TIME ZONE""")
        return True

    def migrate49(self):
        schema._addTableRows(self.db, "querysets_inclusionmethod",
            "name",
            [dict(name="transitive")])
        return True

    def migrate50(self):
        # these never shipped but following querysets were installed wrong
        # so the filters didn't work, delete querysets & reinstall
        cu = self.db.cursor()

        cu.execute("DELETE FROM querysets_queryset WHERE name='All Project Stages'")
        cu.execute("DELETE FROM querysets_queryset WHERE name='All Projects'")

        schema._createAllProjectBranchStages(self.db, version=(58,50))
        schema._createAllProjects(self.db, version=(58,50))

        return True

    def migrate51(self):
        # change the way "All Systems" to work like the other querysets
        db = self.db
        cu = db.cursor()
        # find the existing All Systems query set
        # as previously defined, it will have children but no filter tags
        allQsId = schema._getRowPk(db, 'querysets_queryset', 'query_set_id',
            name='All Systems')
        # remove any child query sets assigned to 'All Systems'
        cu.execute('DELETE FROM querysets_queryset_children WHERE from_queryset_id=?', allQsId)
        # create a filter to match the presense of any system name
        try:
            cu.execute("""INSERT INTO querysets_filterentry (field, operator, value)
                VALUES('system.name', 'IS_NULL', false)""")
        except sqlerrors.ConstraintViolation:
            # possible but unlikley the customer already made this one, so tolerate
            # duplicate insertion failure
            pass
        filterId = schema._getRowPk(db, "querysets_filterentry", "filter_entry_id",
            field='system.name', operator='IS_NULL', value='false')
        cu.execute("""INSERT INTO querysets_queryset_filter_entries
            (queryset_id, filterentry_id)
            VALUES(?, ?)""", allQsId, filterId)
        return True

    def migrate52(self):
        # tags tables need larger PKs
        db = self.db
        cu = db.cursor()

        cu.execute("""ALTER TABLE querysets_systemtag
            ALTER COLUMN system_tag_id TYPE %(BIGINT)s
        """ % db.keywords)
        cu.execute("""ALTER TABLE querysets_usertag
            ALTER COLUMN user_tag_id TYPE %(BIGINT)s
        """ % db.keywords)
        cu.execute("""ALTER TABLE querysets_projecttag
            ALTER COLUMN project_tag_id TYPE %(BIGINT)s
        """ % db.keywords)
        cu.execute("""ALTER TABLE querysets_stagetag
             ALTER COLUMN stage_tag_id TYPE %(BIGINT)s
        """ % db.keywords)
        return True

    def migrate53(self):
        # remove intermediate querytag table
        db = self.db
        cu = db.cursor()
        tables = [
            [ 'querysets_systemtag',  'system_id',  'system',  'querysets_systemtag_uq' ],
            [ 'querysets_projecttag', 'project_id', 'project', 'querysets_projecttag_uq' ],
            [ 'querysets_stagetag',   'stage_id',   'stage',   'querysets_stagetag_uq' ],
            [ 'querysets_usertag',    'user_id',    'user',    'querysets_usertag_uq' ],
        ]
        # unrelated, but names need to be consistent from earlier schema change
        cu.execute("""UPDATE querysets_queryset SET description='All systems'
            WHERE name='All Systems'
        """)
        # unrelated, but index was not set correctly vs schema.py in previous migration
        cu.execute("DROP INDEX IF EXISTS rbacuserrolesearchidx")
        self.db.createIndex('rbac_user_role', 'rbacuserrolesearchidx',
                'user_id, role_id', unique=True)

        for t in tables:
            constraint = t[3]
            cu.execute("""
                ALTER TABLE %s ADD COLUMN query_set_id INTEGER
                    REFERENCES querysets_queryset(query_set_id)
                    ON DELETE CASCADE
            """ % t[0])
            cu.execute("""
                UPDATE %s SET query_set_id=(
                   SELECT query_set_id FROM querysets_querytag where query_tag_id=%s.query_tag_id
                )
            """ % (t[0],t[0]))

            cu.execute("""
                ALTER TABLE %s ADD CONSTRAINT %s
                    UNIQUE (%s, query_set_id, inclusion_method_id)
            """ % (t[0], constraint, t[1]))
            cu.execute("""
                ALTER TABLE %s DROP COLUMN query_tag_id
            """ % t[0])
        cu.execute("DROP TABLE querysets_querytag")
        return True

    def migrate54(self):
        '''Add dates to rbac tables'''
        db = self.db
        cu = db.cursor()
        tables = [ 'rbac_user_role', 'rbac_permission', 'rbac_role' ]
        fields = [
             "created_date timestamp with time zone NOT NULL",
             "modified_date timestamp with time zone NOT NULL",
        ]
        for table in tables:
            for field in fields:
                cu.execute("ALTER TABLE %s ADD COLUMN %s" % (table, field))
        return True

    def migrate55(self):
        # Data migration is covered in the 55.2 migration, nobody else would
        # have installed between then and here.
        add_columns(self.db, 'Builds', 'output_trove text')
        return True

    def migrate56(self):
        # add new querysets for roles & grants
        cu = self.db.cursor()
        db = self.db
        filterId = schema._addQuerySetFilterEntry(db, "rbac_role.role_id", "IS_NULL", "false")
        schema._addQuerySet(db, "All Roles", "All roles", "role", False, filterId, 'rbac',
               version=(58,56))
        filterId = schema._addQuerySetFilterEntry(db, "rbac_permission.permission_id", "IS_NULL", "false")
        schema._addQuerySet(db, "All Grants", "All grants", "grant", False, filterId, 'rbac',
               version=(58,56))
        createTable(self.db, """
            CREATE TABLE "querysets_permissiontag" (
                "permission_tag_id" TEXT PRIMARY KEY,
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
                CONSTRAINT querysets_permissiontag_uq UNIQUE ("permission_id", "query_set_id", "inclusion_method_id")
            )""")

        createTable(self.db, """
            CREATE TABLE "querysets_roletag" (
                "role_tag_id" TEXT PRIMARY KEY,
                "role_id" TEXT
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
                CONSTRAINT querysets_roletag_uq UNIQUE ("role_id", "query_set_id", "inclusion_method_id")
            )""")
        return True

    def migrate57(self):
        cu = self.db.cursor()
        cu.execute("""
            INSERT INTO "jobs_job_type"
                ("name", "description", "priority", "resource_type")
            VALUES
                ('refresh queryset',
                 'Refresh queryset',
                 105,
                 'QuerySet')
        """)
        # fix previous migration -- needs different primary key type
        cu.execute("DROP TABLE querysets_permissiontag")
        cu.execute("DROP TABLE querysets_roletag")
        createTable(self.db, """
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
                CONSTRAINT querysets_permissiontag_uq UNIQUE ("permission_id", "query_set_id", "inclusion_method_id")
            )""" % self.db.keywords)

        createTable(self.db, """
            CREATE TABLE "querysets_roletag" (
                "role_tag_id" %(BIGPRIMARYKEY)s,
                "role_id" TEXT
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
                CONSTRAINT querysets_roletag_uq UNIQUE ("role_id", "query_set_id", "inclusion_method_id")
            )""" % self.db.keywords)
        return True

    def migrate58(self):
        # we want integer IDs for rbac role
        cu = self.db.cursor()
        cu.execute("DROP TABLE rbac_permission CASCADE")
        cu.execute("DROP TABLE rbac_user_role CASCADE")
        cu.execute("DROP TABLE rbac_role CASCADE")
        cu.execute("DROP TABLE querysets_roletag CASCADE")
        cu.execute("DROP TABLE querysets_permissiontag CASCADE")

        createTable(self.db, """
            CREATE TABLE rbac_role (
                role_id      %(PRIMARYKEY)s,
                role_name    TEXT,
                created_date timestamp with time zone NOT NULL,
                modified_date timestamp with time zone NOT NULL
            ) %(TABLEOPTS)s """ % self.db.keywords)

        createTable(self.db, """
            CREATE TABLE rbac_user_role (
                rbac_user_role_id  %(PRIMARYKEY)s,
                role_id      INTEGER NOT NULL
                    REFERENCES rbac_role ( role_id )
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                user_id      INTEGER NOT NULL
                    REFERENCES Users ( userId )
                    ON DELETE CASCADE,
                created_date timestamp with time zone NOT NULL,
                modified_date timestamp with time zone NOT NULL,
                UNIQUE ( "role_id", "user_id" )
            ) %(TABLEOPTS)s """ % self.db.keywords)

        createTable(self.db, """
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
                action          TEXT NOT NULL,
                created_date timestamp with time zone NOT NULL,
                modified_date timestamp with time zone NOT NULL,
                UNIQUE ( "role_id", "queryset_id", "action" )
            ) %(TABLEOPTS)s """ % self.db.keywords)

        createTable(self.db, """
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
                CONSTRAINT querysets_roletag_uq UNIQUE ("role_id", "query_set_id", "inclusion_method_id")
            )""" % self.db.keywords)

        # hasn't changed, but easiest way to keep the constraints happy is to just recreate it
        # seeing it hasn't shipped
        createTable(self.db, """
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
                CONSTRAINT querysets_permissiontag_uq UNIQUE ("permission_id", "query_set_id", "inclusion_method_id")
            )""" % self.db.keywords)

        self.db.tables['rbac_permission'] = []
        self.db.createIndex('rbac_permission', 'RbacPermissionLookupIdx',
            'role_id, queryset_id, action')

        return True

    def migrate59(self):
        db = self.db
        cu = self.db.cursor()
        columns = [ 'created_by', 'modified_by' ]
        tables = [ 'rbac_user_role', 'rbac_role' ]
        for table in tables:
            for column in columns:
                cu.execute("""ALTER TABLE %s ADD COLUMN %s
                     INTEGER
                     REFERENCES Users ( userId )
                     ON DELETE CASCADE
                """ % (table, column))
        cu.execute("ALTER TABLE rbac_role ADD COLUMN description TEXT")

        createTable(self.db, """
            CREATE TABLE "rbac_permission_type" (
                "permission_type_id" %(PRIMARYKEY)s,
                "name" TEXT NOT NULL UNIQUE,
                "description" TEXT NOT NULL
            )""" % db.keywords)

        schema._addTableRows(self.db, 'rbac_permission_type', 'name', [
            dict(name="ReadMembers", description='Read Member Resources'),
            dict(name="ModMembers",  description='Modify Member Resources'),
            dict(name="ReadSet",     description='Read Set'),
            dict(name="ModSetDef",   description='Modify Set Definition'),
        ])

        cu.execute("""DROP TABLE rbac_permission CASCADE""")
        createTable(self.db, """
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
                created_by INTEGER
                     REFERENCES Users ( userId )
                     ON DELETE CASCADE,
                modified_by INTEGER
                     REFERENCES Users ( userId )
                     ON DELETE CASCADE,
                created_date timestamp with time zone NOT NULL,
                modified_date timestamp with time zone NOT NULL,
                UNIQUE ( "role_id", "queryset_id", "permission_type_id" )
            ) %(TABLEOPTS)s """ % self.db.keywords)
        self.db.tables['rbac_permission'] = []
        self.db.createIndex('rbac_permission', 'RbacPermissionLookupIdx',
            'role_id, queryset_id, permission_type_id')

        cu.execute("DROP TABLE querysets_permissiontag")
        # still hasn't changed, but easiest way to keep the constraints happy is to just recreate it
        # seeing it hasn't shipped
        createTable(self.db, """
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
                CONSTRAINT querysets_permissiontag_uq UNIQUE ("permission_id", "query_set_id", "inclusion_method_id")
            )""" % self.db.keywords)

        return True

    def migrate60(self):
        db = self.db
        cu = db.cursor()
        cu.execute("""
            CREATE TABLE target_types (
            target_type_id     %(PRIMARYKEY)s,
            name              TEXT NOT NULL UNIQUE,
            description       TEXT NOT NULL,
            created_date      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
            modified_date     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp) %(TABLEOPTS)s """ % db.keywords)
        schema._addTableRows(db, 'target_types', 'name',
            [
                dict(name="ec2",
                    description="Amazon Elastic Compute Cloud"),
                dict(name="eucalyptus",
                    description="Eucalyptus"),
                dict(name="openstack",
                    description="OpenStack"),
                dict(name="vcloud",
                    description="VMware vCloud"),
                dict(name="vmware",
                    description="VMware ESX/vSphere"),
                dict(name="xenent",
                    description="Citrix Xen Server"),
            ])
        # Delete targets of unknown types
        cu.execute("""
           DELETE FROM Targets
            WHERE targetType NOT IN
               (SELECT name FROM target_types)""")
        # Add new target columns, with constraints disabled
        cu.execute("""ALTER TABLE Targets
            ADD COLUMN target_type_id    integer
                    REFERENCES target_types (target_type_id)
                    ON DELETE CASCADE,
            ADD COLUMN zone_id           integer
                    REFERENCES inventory_zone (zone_id)
                    ON DELETE CASCADE,
            ADD COLUMN description       TEXT,
            ADD COLUMN created_date      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
            ADD COLUMN modified_date     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp
        """)
        cu.execute("ALTER TABLE Targets RENAME targetName TO name")
        cu.execute("ALTER TABLE Targets ALTER COLUMN name TYPE TEXT")
        # Populate rows
        cu.execute("SELECT zone_id FROM inventory_zone WHERE name=?",
            'Local rBuilder')
        zoneId = cu.fetchone()[0]
        # Default description to name
        cu.execute("UPDATE Targets SET zone_id=?, description=name", zoneId)
        cu.execute("""
            UPDATE Targets AS tt
               SET target_type_id=(
                    SELECT target_type_id
                      FROM target_types
                     WHERE tt.targetType = target_types.name)""")
        cu.execute("ALTER TABLE Targets DROP COLUMN targetType")
        # Set not null constraints
        cu.execute("""
            ALTER TABLE Targets
                ALTER COLUMN zone_id SET NOT NULL,
                ALTER COLUMN target_type_id SET NOT NULL,
                ALTER COLUMN description SET NOT NULL""")
        cu.execute("CREATE UNIQUE INDEX Targets_Type_Name_Uq ON Targets(target_type_id, name)")
        return True

    def migrate61(self):
        db = self.db
        cu = db.cursor()
        cu.execute("""
            UPDATE querysets_queryset SET presentation_type = resource_type
                WHERE presentation_type IS NULL
        """)
        return True

    def migrate62(self):
        db = self.db
        cu = db.cursor()
        cu.execute("""ALTER TABLE jobs_job
            ADD COLUMN job_token varchar(64) UNIQUE""")
        schema._addTableRows(db, 'jobs_job_type', 'name', [
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
        ])
        schema.createTable(db, 'jobs_job_target_type', """
        CREATE TABLE jobs_job_target_type (
            id          %(PRIMARYKEY)s,
            job_id      integer NOT NULL
                        REFERENCES jobs_job(job_id) ON DELETE CASCADE,
            target_type_id integer NOT NULL
                        REFERENCES target_types(target_type_id) ON DELETE CASCADE
        )""")
        schema.createTable(db, 'jobs_job_target', """
        CREATE TABLE jobs_job_target (
            id          %(PRIMARYKEY)s,
            job_id      integer NOT NULL
                        REFERENCES jobs_job(job_id) ON DELETE CASCADE,
            target_id integer NOT NULL
                        REFERENCES Targets(targetid) ON DELETE CASCADE
        )""")
        return True

    def migrate63(self):
        drop_tables(self.db,
                'CommunityIds',
                'NewsCache',
                'NewsCacheInfo',
                'ApplianceSpotlight',
                'FrontPageSelections',
                'UseIt',
                'LatestCommit',
                'PopularProjects',
                'TopProjects',
                )
        return True

    def migrate64(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE ProductVersions
            ADD source_group text,
            ADD platform_id integer REFERENCES Platforms ON DELETE SET NULL,
            ADD platform_label text""")
        return True

    def migrate65(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE Users
                ADD is_admin bool NOT NULL DEFAULT false""")
        cu.execute("""UPDATE Users u
            SET is_admin = EXISTS (
                SELECT * FROM UserGroupMembers m
                JOIN UserGroups g USING (userGroupId)
                WHERE m.userId = u.userId AND g.usergroup = 'MintAdmin'
            ) """)
        drop_tables(self.db,
                'UserGroupMembers',
                'UserGroups',
                )
        return True

    def migrate66(self):
        # This includes migration 55.3
        db = self.db
        schema._addTableRows(db, 'job_types', 'name',
        [
          dict(name="image-deployment", description="Image Deployment"),
        ])
        tableName = 'jobs_job_type'
        schema._addTableRows(db, tableName, 'name', [
             dict(name="configure target credentials",
                  description="Configure target credentials for the current user",
                  priority=105,
                  resource_type="Target"),
        ])
        return True

    def migrate67(self):
        db = self.db
        cu = db.cursor()
        cu.execute("""ALTER TABLE jobs_job
                ADD created_by INTEGER REFERENCES Users ON DELETE SET NULL""")
        schema.createTable(db, 'target_image', """
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

        schema.createTable(db, 'target_image_credentials', """
                CREATE TABLE target_image_credentials (
                    id                      %(PRIMARYKEY)s,
                    target_image_id         INTEGER NOT NULL
                        REFERENCES target_image ON DELETE CASCADE,
                    target_credentials_id   INTEGER NOT NULL
                        REFERENCES TargetCredentials ON DELETE CASCADE
                ) %(TABLEOPTS)s""")

        schema.createTable(db, 'jobs_job_result', """
            CREATE TABLE jobs_job_result (
                job_result_id %(PRIMARYKEY)s,
                job_id          INTEGER NOT NULL
                    REFERENCES jobs_job ON DELETE CASCADE,
                data            TEXT NOT NULL
            ) %(TABLEOPTS)s""")

        schema.createTable(db, 'jobs_job_history', """
            CREATE TABLE jobs_job_history
            (
                job_history_id  %(PRIMARYKEY)s,
                job_id          INTEGER NOT NULL
                    REFERENCES jobs_job ON DELETE CASCADE,
                content         TEXT NOT NULL,
                created_date    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp
            ) %(TABLEOPTS)s""")
        return True

    def migrate68(self):
        db = self.db
        cu = db.cursor()
        cu.execute("""
           ALTER TABLE inventory_system ADD should_migrate
               BOOLEAN NOT NULL DEFAULT FALSE
        """)
        return True

    def migrate69(self):
        '''make querysets for targets'''
        db = self.db
        createTable(self.db, """
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
                CONSTRAINT querysets_targettag_uq UNIQUE ("target_id", "query_set_id", "inclusion_method_id")
            )""" % self.db.keywords)

        # TODO: also have to add filter entry
        filterId = schema._addQuerySetFilterEntry(db, "target.name", "IS_NULL", "false")
        schema._addQuerySet(db, "All Targets", "All targets", "target", False, filterId,
            version=(58,69))

        return True

    def migrate70(self):
        '''add source image to systems table'''
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE "inventory_system"
                 ADD COLUMN "source_image_id" INTEGER
                     REFERENCES "builds" ("buildid")
                     ON DELETE CASCADE
        """)
        return True

    def migrate71(self):
        """modify table for build data"""
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE BuildData
                DROP CONSTRAINT builddata_pkey""")
        cu.execute("""
            ALTER TABLE BuildData
                ADD COLUMN buildDataId bigserial PRIMARY KEY""")
        cu.execute("""
            ALTER TABLE BuildData
                ADD CONSTRAINT builddata_uq UNIQUE (buildid, name)""")
        return True

    def migrate72(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE BuildFilesUrlsMap
                DROP CONSTRAINT buildfilesurlsmap_pkey""")
        cu.execute("""
            ALTER TABLE BuildFilesUrlsMap
                ADD COLUMN buildfilesurlsmapid serial PRIMARY KEY""")
        cu.execute("""
            ALTER TABLE BuildFilesUrlsMap
                ADD CONSTRAINT buildfilesurlsmap_uq UNIQUE (fileid, urlid)""")
        return True

    def migrate73(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE Builds ADD base_image integer
            REFERENCES Builds ON DELETE SET NULL""")
        cu.execute("""UPDATE Builds b SET base_image = (
            SELECT o.buildId FROM BuildData d
            JOIN Builds o ON d.value = o.output_trove
            AND d.name = 'baseImageTrove'
            AND d.buildId = b.buildId)""")
        return True

    def migrate74(self):
        schema._addTableRows(self.db, 'jobs_job_type', 'name', [
         dict(name="system capture",
              description="Capture a system's image",
              priority=105,
              resource_type="System"),
        ])
        return True

    def migrate75(self):
        # keep dirk target querysets working
        self.db.cursor().execute("""
             UPDATE querysets_filterentry SET field = 'target.target_id' WHERE
                 field = 'target.targetid'
        """)
        return True

class MigrateTo_59(SchemaMigration):
    '''Edge-P2'''
    Version = (59, 4)

    def migrate(self):
        '''make some querysets always visible regardless of RBAC'''
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE querysets_queryset
                ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT FALSE
        """)

        cu.execute("""
            UPDATE querysets_queryset SET is_public = FALSE;
        """)
        cu.execute("""
            UPDATE querysets_queryset SET is_public = TRUE WHERE
               name='All Systems' OR name='All Projects'
               OR name='All Project Stages' OR NAME='All Users'
               OR name='All Targets'
        """)
        return True

    def migrate1(self):
        '''track additional audit params on users'''
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE Users ADD COLUMN
                timeModified numeric(14,3)
        """)
        cu.execute("""
            ALTER TABLE Users ADD COLUMN created_by integer
                REFERENCES Users ON DELETE SET NULL
        """)
        cu.execute("""
            ALTER TABLE Users ADD COLUMN modified_by integer
                REFERENCES Users ON DELETE SET NULL
        """)
        return True

    def migrate2(self):
        createTable(self.db, """
            CREATE TABLE auth_tokens (
                token_id            %(BIGPRIMARYKEY)s,
                token               text            NOT NULL UNIQUE,
                expires_date        timestamptz     NOT NULL,
                user_id             integer         NOT NULL
                    REFERENCES Users ON UPDATE CASCADE ON DELETE CASCADE,
                image_id            integer
                    REFERENCES Builds ON UPDATE CASCADE ON DELETE CASCADE
            )""")
        return True

    def migrate3(self):
        # All Platforms is not a valid queryset, so don't ship, but
        # don't delete any that are just named coincidentally (by users)
        cu = self.db.cursor()
        cu.execute("""
            DELETE from querysets_queryset WHERE name='All Platforms'
        """)
        return True

    def migrate4(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE querysets_queryset ADD COLUMN
               is_static BOOLEAN NOT NULL DEFAULT FALSE
        """)
        return True

class MigrateTo_60(SchemaMigration):
    '''Edge-P3'''
    Version = (60, 11)

    def migrate(self):
        '''"My" querysets feature'''
        cu = self.db.cursor()
        for field in [ 'created_by', 'modified_by', 'personal_for' ]:
            cu.execute("""
                ALTER TABLE querysets_queryset ADD COLUMN %s INTEGER REFERENCES Users (userid) ON DELETE SET NULL
            """ % field)
        for field in [ 'created_by', 'modified_by' ]:
            cu.execute("""
                ALTER TABLE inventory_system ADD COLUMN %s INTEGER REFERENCES Users (userid) ON DELETE SET NULL
            """ % (field))
        cu.execute("""
            ALTER TABLE inventory_system ADD COLUMN modified_date TIMESTAMP WITH TIME ZONE
        """)
        cu.execute("""
            ALTER TABLE Users ADD COLUMN can_create BOOLEAN NOT NULL DEFAULT FALSE
        """)
        cu.execute("""
            ALTER TABLE rbac_role ADD COLUMN is_identity BOOLEAN NOT NULL DEFAULT FALSE
        """)
        schema._addTableRows(self.db, 'rbac_permission_type', 'name', [
            dict(name="CreateResource", description='Create Resource'),
        ])
        return True

    def migrate1(self):
        '''continued ownership tracking for "My QuerySets"'''
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE projects ADD COLUMN modified_by INTEGER REFERENCES Users (userid) ON DELETE SET NULL
        """)
        return True

    def migrate2(self):
        cu = self.db.cursor()
        cu.execute("""update inventory_management_interface
                set credentials_descriptor=? where name='wmi'""" ,
                schema.wmi_credentials_descriptor)
        return True

    def migrate3(self):
        '''do not delete users, mark them as deleted'''
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE users ADD COLUMN deleted BOOLEAN NOT NULL DEFAULT false
        """)
        return True

    def migrate4(self):
        schema._createNonIdentityRoles(self.db, version=(60,4))
        return True

    def migrate5(self):
        db = self.db
        cu = db.cursor()
        add_columns(db, "target_types", "build_type_id INTEGER")
        # Rename xenent to xen-enterprise, so simplify driver discovery
        cu.execute("UPDATE target_types SET name='xen-enterprise' WHERE name='xenent'")
        tbmap = [
            ('ec2', buildtypes.AMI),
            ('eucalyptus', buildtypes.RAW_FS_IMAGE),
            ('openstack', buildtypes.RAW_HD_IMAGE),
            ('vcloud', buildtypes.VMWARE_ESX_IMAGE),
            ('vmware', buildtypes.VMWARE_ESX_IMAGE),
            ('xen-enterprise', buildtypes.XEN_OVA),
        ]
        q = "UPDATE target_types SET build_type_id=? WHERE name=?"
        for targetTypeName, buildTypeId in tbmap:
            cu.execute(q, buildTypeId, targetTypeName)
        cu.execute("ALTER TABLE target_types ALTER COLUMN build_type_id SET NOT NULL")
        schema.createTable(db, 'target_deployable_image', """
                target_deployable_image_id %(PRIMARYKEY)s,
                target_id               integer             NOT NULL
                    REFERENCES Targets ON DELETE CASCADE,
                target_image_id         INTEGER
                    REFERENCES target_image ON DELETE CASCADE,
                file_id                 integer NOT NULL
                    REFERENCES BuildFiles ON DELETE CASCADE,
        """)

        schema.createTable(db, 'jobs_job_image', """
            id          %(PRIMARYKEY)s,
            job_id      integer NOT NULL
                        REFERENCES jobs_job(job_id)
                        ON DELETE CASCADE,
            image_id integer NOT NULL
                        REFERENCES Builds(buildId)
                        ON DELETE CASCADE,
        """)
        return True

    def migrate6(self):
        # Case-insensitive unique constraints
        if self.db.driver != 'sqlite':
            self.db.createIndex('Users', 'users_username_casei_uq',
                    '( UPPER(username) )', unique=True)
            self.db.createIndex('Projects', 'projects_shortname_casei_uq',
                    '( UPPER(shortname) )', unique=True)
        return True

    def migrate7(self):
        schema._createAllImages(self.db, version=(60,7))
        return True

    def migrate8(self):
        # add tag tables for image querysets
        schema.createTable(self.db, 'querysets_imagetag', """
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
        """)
        return True

    def migrate9(self):
        cu = self.db.cursor()
        cu.execute("""
            UPDATE querysets_queryset set is_public=true
            WHERE name like 'All Images'
        """)
        return True

    def migrate10(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE Targets ADD COLUMN state INTEGER NOT NULL DEFAULT 0
        """)
        schema._addTableRows(self.db, 'jobs_job_type', 'name', [
             dict(name="configure target",
                  description="Configure target",
                  priority=105,
                  resource_type="TargetType"),
        ])
        return True


    def migrate11(self):
        db = self.db
        schema.createTable(db, 'target_system', """
                target_system_id        %(PRIMARYKEY)s,
                name                    TEXT NOT NULL,
                description             TEXT NOT NULL,
                target_id               integer             NOT NULL
                    REFERENCES Targets ON DELETE CASCADE,
                target_internal_id      TEXT             NOT NULL,
                ip_addr_1               TEXT,
                ip_addr_2               TEXT,
                state                   TEXT NOT NULL,
                created_date            TIMESTAMP WITH TIME ZONE NOT NULL
                    DEFAULT current_timestamp,
                modified_date           TIMESTAMP WITH TIME ZONE NOT NULL
                    DEFAULT current_timestamp,
                UNIQUE ( target_id, target_internal_id )
            """)

        schema.createTable(db, 'target_system_credentials', """
                id                      %(PRIMARYKEY)s,
                target_system_id        INTEGER NOT NULL
                    REFERENCES target_system ON DELETE CASCADE,
                target_credentials_id   INTEGER NOT NULL
                    REFERENCES TargetCredentials ON DELETE CASCADE
            """)
        return True

class MigrateTo_61(SchemaMigration):
    '''Edge P4, P5, P6'''
    Version = (61, 8)

    def migrate(self):
        cu = self.db.cursor()
        cu.execute("""DROP TABLE changelog_change_log_entry""")
        cu.execute("""DROP TABLE changelog_change_log""")
        return True

    def migrate1(self):
        # account for some previously renamed model names that could be in queryset filter terms
        cu = self.db.cursor()
        cu.execute("update querysets_filterentry set field = 'target.name' where field = 'target.targetname'")
        cu.execute("update querysets_filterentry set field = 'project_branch.namespace' where field = 'major_version.namespace'")
        return True

    def migrate2(self):

        schema.createTable(self.db, 'jobs_created_system', """
            creation_id     %(PRIMARYKEY)s,
            job_id          INTEGER NOT NULL
                REFERENCES jobs_job ON DELETE CASCADE,
            system_id       INTEGER NOT NULL
                REFERENCES inventory_system ON DELETE SET NULL,
        """)

        schema.createTable(self.db, 'jobs_created_image', """
            creation_id     %(PRIMARYKEY)s,
            job_id          INTEGER NOT NULL
                REFERENCES jobs_job ON DELETE CASCADE,
            image_id        INTEGER NOT NULL
                REFERENCES builds (buildid) ON DELETE SET NULL,
        """)
        return True

    def migrate3(self):
        # See mingle #1456
        cu = self.db.cursor()
        cu.execute("""UPDATE BuildFiles f
            SET title = 'VMware (R) ESX OVF 1.0 Image'
            FROM BuildFilesUrlsMap m JOIN FilesUrls u USING (urlId)
            WHERE m.fileId = f.fileId
            AND u.url LIKE '%.ova' AND f.title = ''
            """)
        cu.execute("""UPDATE BuildFiles
            SET title = 'Unknown build file' WHERE title = '' """)
        cu.execute("""ALTER TABLE BuildFiles
            ADD CONSTRAINT title_not_empty CHECK (title != ''),
            ALTER title DROP DEFAULT""")
        return True

    def migrate4(self):
        # mingle #1564
        add_columns(self.db, 'Platforms',
                'hidden          boolean NOT NULL DEFAULT false')
        return True

    def migrate5(self):
        # mingle #1641
        schema._addTableRows(self.db, 'jobs_job_type', 'name', [
             dict(name="immediate system registration",
                  description='On-demand system registration',
                  priority=110,
                  resource_type='System'),
        ])
        return True

    def migrate6(self):
        # make role names unique with DB constraint to avoid race condition
        # this is 5.3 -- if we release it.
        cu = self.db.cursor()
        # first delete any duplicate role names that may exist
        # so adding the contraint will not fail
        seen   = {}
        delete = []

        cu.execute("SELECT role_id, role_name from rbac_role")
        row = cu.fetchone()
        while row is not None:
            if seen.has_key(row[1]):
                delete.append(row[0])
            seen[row[1]] = 1
            row = cu.fetchone()
        for x in delete:
            cu.execute("DELETE from rbac_role where role_id=%s" % x)
        cu.execute("""ALTER TABLE rbac_role ADD UNIQUE (role_name)""")
        return True

    def migrate7(self):
        # this is P6
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE inventory_system ADD COLUMN out_of_date BOOLEAN NOT NULL DEFAULT False""")
        cu.execute("""ALTER TABLE inventory_system ADD COLUMN has_active_jobs BOOLEAN NOT NULL DEFAULT False""")
        cu.execute("""ALTER TABLE inventory_system ADD COLUMN has_running_jobs BOOLEAN NOT NULL DEFAULT False""")
        return True

    def migrate8(self):
        # make additional querysets show up in left navigation
        cu = self.db.cursor()
        cu.execute("""UPDATE querysets_queryset SET is_public = TRUE WHERE NAME = 'Active Systems'
                         AND resource_type='system' AND can_modify = FALSE""")
        cu.execute("""UPDATE querysets_queryset SET is_public = TRUE WHERE NAME = 'Infrastructure Systems'
                         AND resource_type='system' AND can_modify = FALSE""")
        return True

class MigrateTo_62(SchemaMigration):
    '''Fork!'''
    Version = (62, 8)

    def migrate(self):

        createTable2(self.db, 'inventory_survey', """
                "survey_id" %(PRIMARYKEY)s,
                "uuid" TEXT NOT NULL,
                "system_id" INTEGER NOT NULL REFERENCES "inventory_system" (system_id) ON DELETE CASCADE,
                "name" TEXT NOT NULL,
                "description" TEXT,
                "comment" TEXT,
                "created_date" TIMESTAMP WITH TIME ZONE NOT NULL,
                "modified_date" TIMESTAMP WITH TIME ZONE NOT NULL,
                "created_by" INTEGER NOT NULL REFERENCES "users" (userid) ON DELETE SET NULL,
                "modified_by" INTEGER NOT NULL REFERENCES "users" (userid) ON DELETE SET NULL,
                "removable" BOOLEAN NOT NULL DEFAULT TRUE,
                "raw_xml" TEXT
        """)

        createTable2(self.db, 'inventory_survey_tags', """
                "tag_id" %(PRIMARYKEY)s,
                "survey_id" INTEGER REFERENCES "inventory_survey" NOT NULL,
                "name" TEXT
        """)

        createTable2(self.db, 'inventory_rpm_package', """
                "rpm_package_id" %(PRIMARYKEY)s,
                "name" TEXT NOT NULL,
                "epoch" INTEGER,
                "version" TEXT NOT NULL,
                "release" TEXT NOT NULL,
                "architecture" TEXT NOT NULL,
                "description" TEXT,
                "signature" TEXT,
        """)

        createTable2(self.db, 'inventory_conary_package', """
                "conary_package_id" %(PRIMARYKEY)s,
                "name" TEXT NOT NULL,
                "version" TEXT NOT NULL,
                "flavor" TEXT NOT NULL,
                "description" TEXT NOT NULL,
                "revision" TEXT NOT NULL,
                "architecture" TEXT NOT NULL,
                "signature" TEXT NOT NULL,
                "rpm_package_id" INTEGER REFERENCES inventory_rpm_package (rpm_package_id) ON DELETE SET NULL
        """)

        createTable2(self.db, 'inventory_service', """
                service_id %(PRIMARYKEY)s,
                name TEXT,
                autostart BOOLEAN DEFAULT FALSE,
                runlevels TEXT
        """)

        createTable2(self.db, 'inventory_survey_rpm_package', """
                "map_id" %(PRIMARYKEY)s,
                "survey_id" INTEGER NOT NULL REFERENCES "inventory_survey" (survey_id) ON DELETE CASCADE,
                "rpm_package_id" INTEGER NOT NULL REFERENCES "inventory_rpm_package" (rpm_package_id) ON DELETE CASCADE,
                "install_date" TIMESTAMP WITH TIME ZONE NOT NULL
        """)

        createTable2(self.db, 'inventory_survey_conary_package', """
                "map_id" %(PRIMARYKEY)s,
                "survey_id" INTEGER NOT NULL REFERENCES "inventory_survey" (survey_id) ON DELETE CASCADE,
                "conary_package_id" INTEGER NOT NULL REFERENCES "inventory_conary_package" (conary_package_id) ON DELETE CASCADE,
                "install_date" TIMESTAMP WITH TIME ZONE NOT NULL
        """)

        createTable2(self.db, 'inventory_survey_service', """
                "map_id" %(PRIMARYKEY)s,
                "survey_id" INTEGER NOT NULL REFERENCES "inventory_survey" (survey_id) ON DELETE CASCADE,
                "service_id" INTEGER NOT NULL REFERENCES "inventory_service" (service_id) ON DELETE CASCADE,
                running BOOLEAN DEFAULT FALSE,
                status TEXT
        """)

        createTable2(self.db, 'inventory_survey_diff', """
                diff_id %(PRIMARYKEY)s,
                created_date TIMESTAMP WITH TIME ZONE NOT NULL,
                left_survey_id INTEGER NOT NULL REFERENCES "inventory_survey" ("survey_id") ON DELETE CASCADE,
                right_survey_id INTEGER NOT NULL REFERENCES "inventory_survey" ("survey_id") ON DELETE SET NULL,
                xml TEXT
        """)
        return True

    def migrate1(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE inventory_survey ALTER created_by
            DROP NOT NULL""")
        cu.execute("""ALTER TABLE inventory_survey ALTER modified_by
            DROP NOT NULL""")
        return True

    def migrate2(self):
        db = self.db
        schema._addTableRows(db, 'jobs_job_type', 'name', [
             dict(name="system scan",
                  description="Scan system",
                  priority=105,
                  resource_type="System"),
        ])
        db.createIndex('jobs_created_system', 'jobs_created_system_jid_sid_uq',
            'job_id, system_id', unique=True)
        db.createIndex('jobs_created_image', 'jobs_created_image_jid_iid_uq',
            'job_id, image_id', unique=True)
        createTable2(db, 'jobs_created_survey', """
            id          %(PRIMARYKEY)s,
            job_id      integer NOT NULL
                        REFERENCES jobs_job(job_id)
                        ON DELETE CASCADE,
            survey_id integer NOT NULL
                        REFERENCES inventory_survey(survey_id)
                        ON DELETE CASCADE,
        """)
        db.createIndex('jobs_created_survey', 'jobs_created_survey_jid_sid_uq',
            'job_id, survey_id', unique=True)
        return True

    def migrate3(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE inventory_system ADD COLUMN "latest_survey_id" INTEGER
            REFERENCES "inventory_survey" (survey_id) ON DELETE SET NULL
        """)
        return True

    def migrate4(self):
        self.db.createIndex('inventory_survey', 'SurveyUuidIdx', 'uuid')
        self.db.createIndex('inventory_survey', 'SystemIdIdx', 'system_id')
        self.db.createIndex('inventory_survey_diff', 'SurveyDiffLeftRightIdx',
            'left_survey_id,right_survey_id', unique=True)

        return True

    def migrate5(self):

        ''' add windows survey tables & also add some more indexes on previous tables '''

        db = self.db
        createTable2(db, 'inventory_windows_package', """
            "windows_package_id" %(PRIMARYKEY)s,
            "publisher" TEXT NOT NULL,
            "product_code" TEXT NOT NULL,
            "package_code" TEXT NOT NULL,
            "product_name" TEXT NOT NULL,
            "type" TEXT NOT NULL,
            "upgrade_code" TEXT NOT NULL,
            "version" TEXT NOT NULL
        """)

        createTable2(db, 'inventory_survey_windows_package', """
            "map_id" %(PRIMARYKEY)s,
            "survey_id" INTEGER NOT NULL REFERENCES "inventory_survey" (survey_id) ON DELETE CASCADE,
            "windows_package_id" INTEGER NOT NULL REFERENCES "inventory_windows_package" (windows_package_id) ON DELETE CASCADE,
            "install_date" TIMESTAMP WITH TIME ZONE NOT NULL,
            "install_source" TEXT NOT NULL,
            "local_package" TEXT NOT NULL
        """)

        db.createIndex('inventory_survey_windows_package', 'inventory_survey_windows_package_sid', 'survey_id')

        createTable2(db, 'inventory_windows_patch', """
            "windows_patch_id" %(PRIMARYKEY)s,
            "display_name" TEXT NOT NULL,
            "uninstallable" BOOLEAN NOT NULL,
            "patch_code" TEXT NOT NULL,
            "product_code" TEXT NOT NULL,
            "transforms" TEXT
        """)

        createTable2(db, 'inventory_windows_patch_windows_package', """
            "map_id" %(PRIMARYKEY)s,
            "windows_package_id" INTEGER NOT NULL REFERENCES "inventory_windows_package" (windows_package_id) ON DELETE CASCADE,
            "windows_patch_id" INTEGER NOT NULL REFERENCES "inventory_windows_patch" (windows_patch_id) ON DELETE CASCADE
        """)

        db.createIndex('inventory_windows_patch_windows_package',
            'inventory_windows_patch_windows_package_uq',
            'windows_package_id,windows_patch_id', unique=True)

        createTable2(db, 'inventory_survey_windows_patch', """
            "map_id" %(PRIMARYKEY)s,
            "survey_id" INTEGER NOT NULL REFERENCES "inventory_survey" (survey_id) ON DELETE CASCADE,
            "windows_patch_id" INTEGER NOT NULL REFERENCES "inventory_windows_patch" (windows_patch_id) ON DELETE CASCADE,
            "local_package" TEXT NOT NULL,
            "install_date" TIMESTAMP WITH TIME ZONE NOT NULL,
            "is_installed" BOOLEAN NOT NULL
        """)

        createTable2(db, 'inventory_windows_service', """
            "windows_service_id" %(PRIMARYKEY)s,
            "name" TEXT NOT NULL,
            "display_name" TEXT NOT NULL,
            "type" TEXT NOT NULL,
            "handle" TEXT NOT NULL,
            "required_services" TEXT NOT NULL
        """)

        createTable2(db, 'inventory_survey_windows_service', """
            "map_id" %(PRIMARYKEY)s,
            "survey_id" INTEGER NOT NULL REFERENCES "inventory_survey" (survey_id) ON DELETE CASCADE,
            "windows_service_id" INTEGER NOT NULL REFERENCES "inventory_windows_service" (windows_service_id) ON DELETE CASCADE,
            "status" TEXT NOT NULL
        """)

        db.createIndex('inventory_survey_windows_service', 'inventory_survey_windows_service_sid', 'survey_id')

        # end windows survey tables, begin additional indices for linux tables

        db.createIndex('inventory_survey_rpm_package', 'inventory_survey_conary_rpm_package_sid',
            'survey_id')
        db.createIndex('inventory_survey_conary_package', 'inventory_survey_conary_package_sid',
            'survey_id')
        db.createIndex('inventory_survey_service', 'inventory_survey_service_sid',
            'survey_id')

        return True

    def migrate6(self):
        ''' Add created/modified to all types to projects, branches, and stages '''
        cu = self.db.cursor()
        # record creator, modifier, and modifier time for branches
        # creation time was already tracked
        cu.execute("""
            ALTER TABLE productversions ADD COLUMN "created_by" INTEGER
                REFERENCES "users" (userid) ON DELETE SET NULL
        """)
        cu.execute("""
            ALTER TABLE productversions ADD COLUMN "modified_by" INTEGER
                REFERENCES "users" (userid) ON DELETE SET NULL
        """)
        cu.execute("""
            ALTER TABLE productversions ADD COLUMN timeModified numeric(14,3)
        """)
        # and the same for stages
        # creation time was already tracked
        cu.execute("""
            ALTER TABLE project_branch_stage ADD COLUMN created_by INTEGER
                REFERENCES "users" (userid) ON DELETE SET NULL
        """)
        cu.execute("""
            ALTER TABLE project_branch_stage ADD COLUMN modified_by INTEGER
                REFERENCES "users" (userid) ON DELETE SET NULL
        """)
        cu.execute("""
            ALTER TABLE project_branch_stage ADD COLUMN modified_date
                timestamp with time zone
                DEFAULT current_timestamp
        """)

        return True

    def migrate7(self):
        db = self.db
        schema._addTableRows(db, 'jobs_job_type', 'name', [
             dict(name="image build cancellation",
                  description="Cancel an image build",
                  priority=105,
                  resource_type="Image"),
        ])
        return True

    def migrate8(self):
        db = self.db
        self.db.cursor().execute("ALTER TABLE inventory_survey ADD COLUMN values_xml TEXT")
        return True

class MigrateTo_63(SchemaMigration):
    '''Goad'''
    Version = (63, 28)

    def migrate(self):
        ''' add initial tables for config environments'''

        # note -- these are not used, let's whack them in harpoon?
        createTable2(self.db, "config_environments", """
            "id" %(PRIMARYKEY)s,
            "name" TEXT UNIQUE,
            "description" TEXT,
            created_by INTEGER
                REFERENCES Users ON DELETE SET NULL,
            modified_by INTEGER
                REFERENCES Users ON DELETE SET NULL,
            created_date TIMESTAMP WITH TIME ZONE NOT NULL
                DEFAULT current_timestamp,
            modified_date TIMESTAMP WITH TIME ZONE NOT NULL
                DEFAULT current_timestamp,
            config_descriptor TEXT,
        """)

        createTable2(self.db, "querysets_queryset_config_environments", """
            "id" %(PRIMARYKEY)s,
            "queryset_id" INTEGER
                REFERENCES "querysets_queryset" ("query_set_id")
                ON DELETE CASCADE
                NOT NULL,
            "config_environment_id" INTEGER
                REFERENCES "config_environments" ("id")
                ON DELETE CASCADE
                NOT NULL
        """)

        createTable2(self.db, "config_environment_config_values", """
            "id" %(PRIMARYKEY)s,
            "config_environment_id" INTEGER REFERENCES "config_environments" ("id") ON DELETE CASCADE,
            "key" TEXT,
            "value" TEXT
        """)

        createTable2(self.db, "system_config_values", """
            "id" %(PRIMARYKEY)s,
            "system_id" INTEGER REFERENCES "inventory_system" ("system_id") ON DELETE CASCADE,
            "key" TEXT,
            "value" TEXT
        """)

        return True

    def migrate1(self):
        ''' track which conary packages are top level in surveys '''
        self.db.cursor().execute("""
            ALTER TABLE inventory_survey_conary_package ADD COLUMN is_top_level
            BOOLEAN NOT NULL DEFAULT FALSE
        """)
        return True

    def migrate2(self):
        ''' track all sorts of new survey details '''

        cu = self.db.cursor()
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN desired_values_xml TEXT")
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN observed_values_xml TEXT")
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN validator_values_xml TEXT")
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN discovered_values_xml TEXT")

        createTable2(self.db, 'inventory_survey_values', """
            "survey_value_id" %(PRIMARYKEY)s,
            "survey_id" INTEGER NOT NULL REFERENCES inventory_survey (survey_id),
            "type" INTEGER NOT NULL,
            "key" TEXT NOT NULL,
            "subkey" TEXT,
            "value" TEXT
        """)
        return True

    def migrate3(self):
        ''' new survey additions '''
        cu = self.db.cursor()
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN compliance_summary_xml TEXT")
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN config_values_descriptor_xml TEXT")
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN desired_values_descriptor_xml TEXT")
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN updates_pending BOOLEAN NOT NULL DEFAULT FALSE")
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN has_errors BOOLEAN NOT NULL DEFAULT FALSE")
        return True

    def migrate4(self):
        cu = self.db.cursor()
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN preview_xml TEXT")
        return True

    def migrate5(self):
        cu = self.db.cursor()
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN config_diff_xml TEXT")
        return True

    def migrate6(self):
        db = self.db
        schema._addTableRows(db, 'jobs_job_type', 'name', [
             dict(name="system update software",
                  description="Update your system",
                  priority=105,
                  resource_type="System"),
        ])

        createTable2(self.db, 'inventory_update', """
              "update_id"    %(PRIMARYKEY)s,
              "system_id"    INTEGER NOT NULL REFERENCES "inventory_system" (system_id) ON DELETE CASCADE,
              "dry_run"      BOOLEAN DEFAULT TRUE,
              "specs"        TEXT,
              "created_date" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp
              """)

        return True

    def migrate7(self):
        cu = self.db.cursor()
        cu.execute("""
            INSERT INTO "jobs_job_type"
                ("name", "description", "priority", "resource_type")
            VALUES
                ('system apply configuration',
                 'Apply system configuration',
                 105, 'System')
        """)
        return True

    def migrate8(self):
        cu = self.db.cursor()
        cu.execute("""
           ALTER TABLE inventory_system ADD COLUMN configuration_set
               BOOLEAN NOT NULL DEFAULT FALSE
        """)
        cu.execute("""
           ALTER TABLE inventory_system ADD COLUMN configuration_applied
               BOOLEAN NOT NULL DEFAULT FALSE
        """)
        return True

    def migrate9(self):
        cu = self.db.cursor()
        cu.execute("""
           ALTER TABLE inventory_survey_windows_service ADD COLUMN running
               BOOLEAN NOT NULL DEFAULT FALSE
        """)
        return True

    def migrate10(self):
        cu = self.db.cursor()
        cu.execute("""
           ALTER TABLE inventory_survey
           ADD COLUMN system_model      TEXT,
           ADD COLUMN system_model_modified_date    TIMESTAMP WITH TIME ZONE,
           ADD COLUMN has_system_model  BOOLEAN NOT NULL DEFAULT FALSE
        """)
        return True

    def migrate11(self):
        self.db.dropIndex('inventory_survey', 'SurveyUuidIdx')
        self.db.createIndex('inventory_survey', 'SurveyUuidIdx', 'uuid', unique=True)
        return True

    def migrate12(self):
        ''' sync jobs no longer exist '''
        cu = self.db.cursor()
        cu.execute("""
            DELETE FROM jobs_job WHERE job_type_id = (SELECT job_type_id FROM jobs_job_type
                WHERE name = 'system poll')
        """)
        return True

    def migrate13(self):
        createTable2(self.db, 'jobs_created_preview', """
            creation_id %(PRIMARYKEY)s,
            job_id      integer NOT NULL
                        REFERENCES jobs_job(job_id)
                        ON DELETE CASCADE,
            preview     text,
            system_id   INTEGER NOT NULL
                        REFERENCES inventory_system ON DELETE SET NULL,
        """)
        self.db.createIndex('jobs_created_preview', 'jobs_created_preview_jid_sid',
            'job_id, system_id')
        return True

    def migrate14(self):
        ''' installed software is now just a record of the last update action '''
        cu = self.db.cursor()
        cu.execute("DROP TABLE inventory_system_installed_software")
        cu.execute("ALTER TABLE inventory_system ADD COLUMN last_update_trove_spec TEXT")
        cu.execute("""
           UPDATE inventory_system_state SET description = 'Registered' WHERE name = 'registered'
        """)
        return True

    def migrate15(self):
        ''' keep a list of desired top level items '''
        cu = self.db.cursor()
        cu.execute("ALTER TABLE inventory_system DROP COLUMN last_update_trove_spec")
        createTable2(self.db, 'inventory_system_desired_top_level_item', """
                "id" %(PRIMARYKEY)s,
                "system_id" integer NOT NULL
                    REFERENCES "inventory_system" ("system_id")
                    ON DELETE CASCADE,
                "trove_spec" TEXT NOT NULL,
                "created_date" TIMESTAMP WITH TIME ZONE NOT NULL,
        """)
        self.db.createIndex("inventory_system_desired_top_level_item",
            "inventory_system_des_toplitem_sid_tspec", "system_id, trove_spec",
            unique=True)
        return True

    def migrate16(self):
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE jobs_created_preview ADD COLUMN created_date
                TIMESTAMP WITH TIME ZONE
                NOT NULL DEFAULT current_timestamp""")
        return True

    def migrate17(self):
        ''' store snapshots of system/project/branch with the survey '''
        cu = self.db.cursor()
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN system_snapshot_xml TEXT")
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN project_snapshot_xml TEXT")
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN stage_snapshot_xml TEXT")
        return True

    def migrate18(self):
        cu = self.db.cursor()
        cu.execute("ALTER TABLE inventory_conary_package ADD COLUMN unfrozen TEXT")
        return True

    def migrate19(self):
        cu = self.db.cursor()
        cu.execute("ALTER TABLE inventory_survey_windows_service ADD COLUMN start_mode TEXT")
        cu.execute("ALTER TABLE inventory_survey_windows_service ADD COLUMN start_account TEXT")
        return True

    def migrate20(self):
        createTable2(self.db, 'inventory_windows_os_patch', """
            "windows_os_patch_id" %(PRIMARYKEY)s,
            "hotfix_id" TEXT UNIQUE,
            "name" TEXT,
            "fix_comments" TEXT,
            "description" TEXT,
            "cs_name" TEXT,
            "caption" TEXT,
            "service_pack_in_effect" TEXT
        """)
        createTable2(self.db, 'inventory_survey_windows_os_patch', """
            "map_id" %(PRIMARYKEY)s,
            "survey_id" INTEGER NOT NULL REFERENCES "inventory_survey" (survey_id) ON DELETE CASCADE,
            "windows_os_patch_id" INTEGER NOT NULL REFERENCES "inventory_windows_os_patch" (windows_os_patch_id) ON DELETE CASCADE,
            "install_date" TIMESTAMP WITH TIME ZONE NOT NULL,
            "installed_by" TEXT NOT NULL,
            "status" TEXT,
        """)
        return True

    def migrate21(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE inventory_windows_os_patch ADD CONSTRAINT inventory_windows_os_patch_uq UNIQUE (hotfix_id)
        """)
        cu.execute("""
            ALTER TABLE inventory_system RENAME COLUMN configuration TO configuration_legacy
        """)
        cu.execute("""
            ALTER TABLE inventory_system ADD COLUMN configuration_xml TEXT
        """)
        return True

    def migrate22(self):
        cu = self.db.cursor()
        cu.execute("""
            ALTER TABLE inventory_windows_os_patch DROP COLUMN cs_name
        """)
        cu.execute("""
            ALTER TABLE inventory_survey_windows_os_patch ADD COLUMN cs_name TEXT
        """)
        return True

    def migrate23(self):
        cu = self.db.cursor()
        # deleting a source image should not delete a system record
        cu.execute("ALTER TABLE inventory_system DROP CONSTRAINT inventory_system_source_image_id_fkey")
        cu.execute("""
            ALTER TABLE inventory_system ADD CONSTRAINT
            inventory_system_source_image_id_fkey
            FOREIGN KEY (source_image_id) REFERENCES builds(buildid) ON DELETE SET NULL
        """)
        # deleting a survey should delete the survey values
        cu.execute("ALTER TABLE inventory_survey_values DROP CONSTRAINT inventory_survey_values_survey_id_fkey")
        cu.execute("""
            ALTER TABLE inventory_survey_values ADD CONSTRAINT
            inventory_survey_values_survey_id_fkey
            FOREIGN KEY (survey_id) REFERENCES inventory_survey(survey_id) ON DELETE CASCADE
        """)
        # deleting the right survey from a diff should also delete the diff
        cu.execute("""
            ALTER TABLE inventory_survey_diff DROP CONSTRAINT "inventory_survey_diff_right_survey_id_fkey"
        """)
        cu.execute("""
            ALTER TABLE inventory_survey_diff ADD CONSTRAINT "inventory_survey_diff_right_survey_id_fkey"
            FOREIGN KEY (right_survey_id) REFERENCES inventory_survey(survey_id) ON DELETE CASCADE
        """)
        return True

    def migrate24(self):
        ''' keep a list of observed top level items '''
        cu = self.db.cursor()
        createTable2(self.db, 'inventory_system_observed_top_level_item', """
                "id" %(PRIMARYKEY)s,
                "system_id" integer NOT NULL
                    REFERENCES "inventory_system" ("system_id")
                    ON DELETE CASCADE,
                "trove_spec" TEXT NOT NULL,
                "created_date" TIMESTAMP WITH TIME ZONE NOT NULL,
        """)
        self.db.createIndex("inventory_system_observed_top_level_item",
            "inventory_system_obs_toplitem_sid_tspec", "system_id, trove_spec",
            unique=True)
        return True

    def migrate25(self):
        ''' new survey additions '''
        cu = self.db.cursor()
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN overall_compliance BOOLEAN")
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN execution_error_count INTEGER")
        return True

    def migrate26(self):
        ''' store survey OS type '''
        cu = self.db.cursor()
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN os_type TEXT")
        return True

    def migrate27(self):
        """Enforce timestamped tuples in system software"""
        cu = self.db.cursor()
        for name in ('observed', 'desired'):
            name = 'inventory_system_%s_top_level_item' % name
            constraint = r"trove_spec ~ E'.*=/.*/[^/[]+:[^/[]+\\[.*]$'"
            cu.execute("DELETE FROM %s WHERE NOT (%s)" % (name, constraint))
            if self.db.kind == 'sqlite':
                continue
            cu.execute("""ALTER TABLE %s ADD CONSTRAINT trove_spec_check
                CHECK ( %s )""" % (name, constraint))
        return True

    def migrate28(self):
        ''' store windows autostart '''
        cu = self.db.cursor()
        cu.execute("ALTER TABLE inventory_survey_windows_service ADD COLUMN autostart BOOLEAN DEFAULT FALSE")
        return True


class MigrateTo_64(SchemaMigration):
    '''goad-p3'''
    Version = (64, 2)

    def migrate(self):
        ''' productversions.build_standard_group '''
        cu = self.db.cursor()
        cu.execute("ALTER TABLE productversions ADD COLUMN build_standard_group BOOLEAN NOT NULL DEFAULT FALSE")
        return True

    def migrate1(self):
        '''add overall_validation to survey for summary view '''
        cu = self.db.cursor()
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN overall_validation BOOLEAN NOT NULL DEFAULT FALSE")
        return True

    def migrate2(self):
        '''add overall_validation to survey for summary view '''
        cu = self.db.cursor()
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN config_diff_count INTEGER")
        return True

class MigrateTo_65(SchemaMigration):
    '''goad-p4'''
    Version = (65, 2)

    def migrate(self):
        cu = self.db.cursor()
        cu.execute("UPDATE builds SET troveversion='/local@local:COOK/0.100:1-1-1' WHERE troveversion='/local@local:COOK/1-1-1'")
        return True

    def migrate1(self):
        drop_tables(self.db, 'systemupdate', 'repositorylogstatus')
        cu = self.db.cursor()
        cu.execute("""ALTER TABLE Builds
            ALTER troveName TYPE text,
            ALTER troveVersion TYPE text,
            ALTER troveFlavor TYPE text,
            ALTER stageName TYPE text,
            ALTER stageName SET DEFAULT ''
            """)
        cu.execute("""ALTER TABLE Commits
            ALTER troveName TYPE text,
            ALTER version TYPE text""")
        cu.execute("""ALTER TABLE PackageIndex
            ALTER name TYPE text,
            ALTER version TYPE text,
            ALTER serverName TYPE text,
            ALTER branchName TYPE text""")
        cu.execute("""ALTER TABLE ProductVersions
            ALTER namespace TYPE text,
            ALTER name TYPE text""")
        cu.execute("""ALTER TABLE Platforms
            ALTER label TYPE text""")
        return True
        
    def migrate2(self):
        cu = self.db.cursor()
        cu.execute("ALTER TABLE inventory_survey ADD COLUMN software_sync_compliance BOOLEAN")
        return True

class MigrateTo_66(SchemaMigration):
    '''amethyst'''
    Version = (66, 2)

    def migrate(self):
        cu = self.db.cursor()
        cu.execute("update target_types set build_type_id = ? where name = ?",
            buildtypes.TARBALL, 'ec2')
        return True

    def migrate1(self):
        cu = self.db.cursor()
        cu.execute("update target_types set build_type_id = ? where name = ?",
            buildtypes.AMI, 'ec2')
        return True

    def migrate2(self):
        self.db.dropIndex('ProductVersions', 'ProductVersions_uq')
        self.db.createIndex('ProductVersions', 'ProductVersions_uq',
            'projectId,label', unique=True)
        return True


class MigrateTo_67(SchemaMigration):
    '''beryl'''
    Version = (67, 1)

    def migrate(self):
        drop_tables(self.db, 'Sessions')
        return True

    def migrate1(self):
        cu = self.db.cursor()
        cu.execute("ALTER TABLE Platforms ADD upstream_url text")
        return True
