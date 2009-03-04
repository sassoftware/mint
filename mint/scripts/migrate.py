#
# Copyright (c) 2005-2008 rPath, Inc.
#

import os
import sys

from conary.conarycfg import loadEntitlement, EntitlementList
from conary.dbstore import migration, sqlerrors
from conary.lib.tracelog import logMe
from mint.db import schema

# SCHEMA Migration
class SchemaMigration(migration.SchemaMigration):

    def __init__(self, db, cfg=None):
        migration.SchemaMigration.__init__(self, db)
        self.cfg = cfg

    def message(self, msg = None):
        if msg is None:
            msg = self.msg
        if msg == "":
            msg = "Finished migration to schema version %s" % (self.Version,)
        logMe(1, msg)
        self.msg = msg

# Helper functions
def add_columns(cu, table, *columns):
    '''
    Add each column while ignoring existing columns.

    >>> add_columns(cu, 'Table', 'something INTEGER',
    ...     'somethingelse STRING')
    '''

    for column in columns:
        try:
            cu.execute('ALTER TABLE %s ADD COLUMN %s' % (table, column))
        except sqlerrors.DuplicateColumnName:
            pass

def drop_tables(cu, *tables):
    '''
    Drop each table, ignoring any missing tables.

    >>> drop_tables(cu, 'sometable', 'anothertable')
    '''

    for table in tables:
        try:
            cu.execute('DROP TABLE %s' % (table,))
        except sqlerrors.InvalidTable:
            pass

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
        cu = self.db.cursor()
        drop_tables(cu, 'rMakeBuild', 'rMakeBuildItems')
        return True

    # 44.1
    # - Add backupExternal column to Projects table
    def migrate1(self):
        cu = self.db.cursor()
        add_columns(cu, 'Projects', 'backupExternal INT DEFAULT 0')
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
        drop_tables(cu, 'rAPAPasswords', 'OutboundMirrorTargets')

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
        cu = self.db.cursor()

        add_columns(cu, 'Projects', "shortname VARCHAR(128)",
                                    "prodtype VARCHAR(128) DEFAULT ''",
                                    "version VARCHAR(128) DEFAULT ''")

        return True

    # 45.2
    # - Add columns to support mirroring of published releases
    def migrate2(self):
        cu = self.db.cursor()
        add_columns(cu, 'PublishedReleases', "shouldMirror INTEGER NOT NULL DEFAULT 0",
                                             "timeMirrored INTEGER")
        add_columns(cu, 'OutboundMirrors',
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
        cu = self.db.cursor()
        add_columns(cu, 'ProductVersions', 'namespace VARCHAR(16) DEFAULT %r' % self.cfg.namespace)
        #Drop and readd the unique index
        self.db.dropIndex('ProductVersions', 'ProductVersionsProjects')
        self.db.createIndex('ProductVersions', 'ProductVersionsNamespacesProjects',
            'projectId,namespace,name', unique = True)
        return True

    # 45.5
    # - Add namespace column to Project
    def migrate5(self):
        cu = self.db.cursor()
        add_columns(cu, 'Projects', 'namespace VARCHAR(16) DEFAULT %r' % self.cfg.namespace)
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
    # - Add versionId and stage columns to Builds
    def migrate7(self):
        cu = self.db.cursor()
        add_columns(cu, 'Builds', 
                     'productVersionId INTEGER DEFAULT 0',
                     'stage VARCHAR(255) DEFAULT ""', 
                    )
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
    db.transaction()
    try:
        rv = func()
    except:
        db.rollback()
        raise
    else:
        db.commit()
    return rv


# entry point that migrates the schema
def migrateSchema(db, cfg=None):
    version = db.getVersion()
    assert(version >= 37) # minimum version we support
    if version.major > schema.RBUILDER_DB_VERSION.major:
        return version # noop, should not have been called.
    logMe(2, "migrating from version", version)
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
