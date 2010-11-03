#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

"""
Migrate PostgreSQL from one major version to another.

This is accomplished by starting both postmasters and piping a backup from one
into the other.
"""

import logging
import optparse
import os
import psycopg2
import pwd
import subprocess
import sys
import tempfile
import time
import traceback
from conary.lib import util as cny_util
from psycopg2 import extensions as psy_ext

from mint import config
from mint.lib import scriptlibrary
from mint.lib import subprocutil

log = logging.getLogger(__name__)


class DummyCluster(object):
    """Aspects of a postgres cluster needed by the migration script.

    This includes only the functionality of connecting to the postmaster, so an
    already-running instance can be used as a source.
    """

    timeout = 60

    def __init__(self, port):
        self.port = port

    def start(self):
        pass

    def connect(self):
        db = psycopg2.connect(port=self.port)
        # CREATE DATABASE cannot run in a transaction, so don't start one.
        db.set_isolation_level(psy_ext.ISOLATION_LEVEL_AUTOCOMMIT)
        return db

    def waitForPostgres(self):
        start = time.time()
        while True:
            try:
                self.connect()
            except psycopg2.OperationalError, err:
                if ('could not connect' not in err.args[0]
                        and 'starting up' not in err.args[0]
                        ):
                    raise
            else:
                break

            if not self.check():
                raise RuntimeError("Postmaster %s died after starting" %
                        self.port)
            elif time.time() - start > self.timeout:
                self.kill()
                raise RuntimeError(
                        "Postmaster %s did not start after %s seconds" %
                        (self.port, self.timeout))
            time.sleep(0.1)

    def check(self):
        return True

    def wait(self):
        pass

    def kill(self):
        pass


class Postmaster(subprocutil.Subprocess, DummyCluster):
    """Full postmaster harness for starting/stopping a cluster."""

    def __init__(self, dataDir, binDir, port, fsync=True):
        DummyCluster.__init__(self, port)
        self.dataDir = dataDir
        self.binDir = binDir
        self.fsync = fsync
        self.procName = 'postmaster:%s' % port

    # External methods
    def bin(self, path):
        return os.path.join(self.binDir, path)

    def initdb(self):
        log.info("Initializing cluster at %s", self.dataDir)
        subprocutil.logCall([self.bin('initdb'),
            '--pgdata', self.dataDir,
            '--auth=trust',
            '--encoding=UTF8',
            '--locale=C',
            ], preexec_fn=self.copyUIDs)
        log.info("Cluster initialized at %s", self.dataDir)

    def start(self):
        log.info("Starting postmaster on port %s", self.port)
        subprocutil.Subprocess.start(self)

    # subprocutil implementation
    def run(self):
        path = self.bin('postgres')
        args = [path,
                '-D', self.dataDir,
                '-p', str(self.port),
                '--checkpoint_segments=16',
                '--checkpoint_warning=0',
                ]
        if not self.fsync:
            args.append('-F')
        self.copyUIDs()
        os.execl(path, *args)

    # pre-exec helper for initdb
    def copyUIDs(self):
        """Copy EUID/EGID to UID/GID"""
        uid, gid = os.geteuid(), os.getegid()
        if uid != 0 and os.getuid() == 0:
            os.seteuid(0)
            os.setgid(gid)
            os.setuid(uid)


class Script(scriptlibrary.GenericScript):
    logFileName = 'scripts.log'
    newLogger = True

    def action(self):
        parser = optparse.OptionParser()
        parser.add_option('-c', '--config-file',
                default=config.RBUILDER_CONFIG)
        parser.add_option('-q', '--quiet', action='store_true')
        parser.add_option('--from-port')
        parser.add_option('--from-bindir')
        parser.add_option('--from-datadir')
        parser.add_option('--to-bindir')
        parser.add_option('--to-datadir')
        parser.add_option('--user')
        options, args = parser.parse_args()

        if not options.to_bindir or not options.to_datadir:
            parser.error("--to-bindir and --to-datadir are required")
        if ((not options.from_bindir or not options.from_datadir)
                and not options.from_port):
            parser.error("Either --from-port or --from-bindir and "
                    "--from-datadir are required")

        self.loadConfig(options.config_file)
        self.resetLogging(quiet=options.quiet)

        self.uidgid = None
        if options.user:
            _, _, uid, gid = pwd.getpwnam(options.user)[:4]
            self.uidgid = uid, gid

        if os.path.exists(os.path.join(options.to_datadir, 'PG_VERSION')):
            sys.exit("Target dir %s already exists!" % options.to_datadir)

        tempDir = tempfile.mkdtemp(dir=os.path.dirname(options.to_datadir))
        try:
            if self.uidgid:
                os.chown(tempDir, uid, gid)
            self.dropPrivs()

            # Source cluster
            if options.from_bindir and options.from_datadir:
                self.cluster1 = Postmaster(dataDir=options.from_datadir,
                        binDir=options.from_bindir, port=65000)
            else:
                self.cluster1 = DummyCluster(port=options.from_port)

            # Target cluster
            self.cluster2 = Postmaster(dataDir=tempDir,
                    binDir=options.to_bindir, port=65001, fsync=False)

            try:
                self.migrate()
            finally:
                log.info("Shutting down")
                self.cluster1.kill()
                self.cluster2.kill()
                self.cluster1.wait()
                self.cluster2.wait()

            self.restorePrivs()
            os.rename(tempDir, options.to_datadir)

        finally:
            try:
                if os.path.isdir(tempDir):
                    try:
                        self.restorePrivs()
                    except:
                        traceback.print_exc()
                    log.info("Cleaning up temporary target dir")
                    cny_util.rmtree(tempDir)
            except:
                traceback.print_exc()

    def migrate(self):
        self.cluster2.initdb()
        self.cluster1.start()
        self.cluster2.start()
        time.sleep(1)
        self.cluster1.waitForPostgres()
        self.cluster2.waitForPostgres()
        log.info("Postmasters are running.")

        self.migrateGlobals()
        self.migrateDatabases()

    def migrateGlobals(self):
        log.info("Migrating global data")
        source = subprocess.Popen([
            self.cluster2.bin('pg_dumpall'),
            '--username=postgres',
            '--port=' + str(self.cluster1.port),
            '--globals-only',
            '--no-tablespaces',
            ], shell=False, stdout=subprocess.PIPE)
        target = subprocess.Popen([
            self.cluster2.bin('psql'),
            '--username=postgres',
            '--dbname=postgres',
            '--port=65001',
            '--no-psqlrc',
            ], shell=False, stdin=subprocess.PIPE)
        cny_util.copyfileobj(source.stdout, target.stdin)
        if source.wait():
            raise RuntimeError("pg_dumpall failed with exit code %s" %
                    source.returncode)
        target.stdin.close()
        if target.wait():
            raise RuntimeError("psql failed with exit code %s" %
                    target.returncode)

    def migrateDatabases(self):
        log.info("Migrating databases")

        db1 = self.cluster1.connect()
        cu1 = db1.cursor()
        cu1.execute("""SELECT datname,
            pg_catalog.pg_get_userbyid(datdba) AS owner,
            pg_catalog.pg_encoding_to_char(encoding) AS encoding
            FROM pg_database WHERE datallowconn""")
        databases = sorted(cu1)

        db2 = self.cluster2.connect()
        cu2 = db2.cursor()
        cu2.execute("SELECT datname FROM pg_database WHERE datallowconn")
        existing = set(x[0] for x in cu2)

        for n, (database, owner, encoding) in enumerate(databases):
            log.info("Creating database %s (%d/%d)", database, n + 1,
                    len(databases))
            if database in existing:
                log.info("Database already exists. Skipping creation.")
                continue
            cu2.execute("""CREATE DATABASE %(database)s
                OWNER %(owner)s
                TEMPLATE template0
                ENCODING %%(encoding)s
                """ % dict(
                    database=escape_identifier(database),
                    owner=escape_identifier(owner),
                    ),
                dict(encoding=encoding))

        db1.close()
        db2.close()

        for n, (database, owner, encoding) in enumerate(databases):
            log.info("Migrating database %s (%d/%d)", database, n + 1,
                    len(databases))
            self.migrateOneDatabase(database)

    def migrateOneDatabase(self, database):
        source = subprocess.Popen([
            self.cluster2.bin('pg_dump'),
            '--username=postgres',
            '--port=' + str(self.cluster1.port),
            '--format=custom',
            '--compress=0',
            '--verbose',  # FIXME
            database,
            ], shell=False, stdout=subprocess.PIPE)
        target = subprocess.Popen([
            self.cluster2.bin('pg_restore'),
            '--username=postgres',
            '--dbname=' + database,
            '--port=65001',
            '--single-transaction',
            '--verbose',  # FIXME
            ], shell=False, stdin=subprocess.PIPE)
        cny_util.copyfileobj(source.stdout, target.stdin)
        if source.wait():
            raise RuntimeError("pg_dumpall failed with exit code %s" %
                    source.returncode)
        target.stdin.close()
        if target.wait():
            raise RuntimeError("psql failed with exit code %s" %
                    target.returncode)

    def dropPrivs(self, permanent=False):
        if not self.uidgid:
            return
        uid, gid = self.uidgid
        if permanent:
            self.restorePrivs()
            os.setgid(gid)
            os.setuid(uid)
        else:
            os.setegid(gid)
            os.seteuid(uid)

    def restorePrivs(self):
        if not self.uidgid:
            return
        os.setegid(0)
        os.seteuid(0)


def escape_identifier(value):
    return '"%s"' % (value.replace('"', '""'),)
