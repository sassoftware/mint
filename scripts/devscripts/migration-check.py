#!/usr/bin/env python

# test migrations to see if they create the same thing as the schema
# usage: ./scripts/devscripts/migration-check.py scripts/devscripts/migration-reference.sql . 

import os
import sys

# Prevent python readline bug from barfing control chars to stdout
class readline:
    def set_completer(self, func): pass
sys.modules['readline'] = readline()

for path in ('/opt/postgresql-9.2/bin', '/usr/bin'):
    if os.path.exists(path + '/initdb'):
        PGBIN = path
        break
else:
    raise RuntimeError("initdb not found")

import logging
import pgsql
import random
import signal
import subprocess
import tempfile
import time
import traceback

from conary import dbstore
from conary.dbstore import sqlerrors
from conary.lib import log
from conary.lib import util


class Postgres(object):
    def __init__(self, path):
        self.path = path
        self.pid = None
        self.port = random.randint(61000, 65536)

    def _postFork(self):
        if os.getuid() == 0:
            os.setgid(99)
            os.setuid(99)

    def connect(self, dbName):
        if not self.check():
            raise RuntimeError("postmaster is dead")
        start = time.time()
        while True:
            try:
                return dbstore.connect('conary@localhost:%s/%s'
                        % (self.port, dbName), 'postgresql')
            except sqlerrors.DatabaseError, err:
                if ('the database system is starting up' in err.msg
                        or 'Connection refused' in err.msg):
                    if time.time() - start > 15:
                        self.kill()
                        raise RuntimeError("Database did not start")
                    time.sleep(0.1)
                    continue
                raise

    def connectPsyco(self, dbName):
        if not self.check():
            raise RuntimeError("postmaster is dead")
        start = time.time()
        import psycopg2
        while True:
            try:
                return psycopg2.connect(database=dbName, user='conary',
                        port=self.port)
            except psycopg2.DatabaseError, err:
                if ('the database system is starting up' in str(err)
                        or 'Connection refused' in str(err)):
                    if time.time() - start > 15:
                        self.kill()
                        raise RuntimeError("Database did not start")
                    time.sleep(0.1)
                    continue
                raise

    def _create(self):
        proc = subprocess.Popen(
                "%s/initdb -D '%s' -E utf8 --locale=C -U conary" % (PGBIN,
                    self.path,),
                shell=True, stdout=sys.stderr, preexec_fn=self._postFork)
        proc.wait()
        if proc.returncode:
            raise RuntimeError("initdb returned %s" % proc.returncode)

    def start(self):
        self._create()
        self.pid = os.fork()
        if not self.pid:
            try:
                try:
                    self._postFork()
                    postmaster = PGBIN + '/postgres'
                    os.execl(postmaster, postmaster,
                            '-D', self.path, # data directory
                            '-F', # turn fsync off
                            '-p', str(self.port), # port
                            '-N', '10', # max connections
                            '--checkpoint_segments=16', # fewer checkpoints
                            '--checkpoint_warning=0', # quit crying
                            )
                except:
                    traceback.print_exc()
            finally:
                os._exit(70)

    def check(self):
        if not self.pid:
            return False
        pid, status = os.waitpid(self.pid, os.WNOHANG)
        if pid:
            self.pid = None
            return False
        else:
            return True

    def kill(self):
        if not self.pid:
            return
        try:
            pgsql.closeall()
        except:
            pass
        signals = [signal.SIGINT, signal.SIGQUIT, signal.SIGKILL]
        reaped = None
        while signals:
            os.kill(self.pid, signals.pop(0))
            reaped, _ = os.waitpid(self.pid, os.WNOHANG)
            if reaped:
                break
            time.sleep(1)
        if not reaped:
            os.waitpid(self.pid, 0)
        self.pid = None


def run_forked(func, *args, **kwargs):
    pid = os.fork()
    if not pid:
        rc = 70
        try:
            try:
                rc = func(*args, **kwargs)
                rc = int(rc or 0)
            except:
                traceback.print_exc()
        finally:
            os._exit(rc)
    _, status = os.waitpid(pid, 0)
    return status


_ctr = 0
def createdb(server):
    global _ctr
    _ctr += 1
    mdb = server.connect('postgres')
    mcu = mdb.cursor()
    dbname = "dump%s" % _ctr
    mcu.execute("CREATE DATABASE %s ENCODING 'utf8'" % dbname)
    return dbname


def migratedb(server, dbname):
    def forked():
        server.check = lambda: True
        from mint.db import schema
        db = server.connect(dbname)
        schema.loadSchema(db, should_migrate=True)
    if run_forked(forked):
        sys.exit("migration failed")


def dumpdb(server, dbname, path):
    if os.system("pg_dump -U conary -p %s %s -f %s" % (server.port, dbname,
            path)):
        sys.exit("dump failed")


def restoredb(server, dbname, path):
    if os.system("psql -U conary -p %s -d %s -f %s -1 -X" % (server.port,
            dbname, path)):
        sys.exit("restore failed")


def hgresolve(tag):
    p = subprocess.Popen(['hg', 'id', '-ir', tag], stdout=subprocess.PIPE)
    rev = p.communicate()[0].strip()
    if not rev or p.returncode:
        raise RuntimeError("Failed to resolve hg tag %r" % (tag,))
    return rev.split()[0]


def main():
    log.setupLogging(consoleLevel=logging.DEBUG, consoleFormat='file')

    start, end = sys.argv[1:]

    if os.path.exists(start):
        startrev = None
        if end == '.':
            # file -> working copy
            endrev = None
        else:
            # file -> revision
            endrev = hgresolve(end)
    else:
        # revision -> revision
        startrev = hgresolve(start)
        endrev = hgresolve(end)

    if (startrev or endrev) and os.system("hg id |grep -q +") == 0:
        sys.exit("working copy is not clean, commit or qrefresh first")

    workdir = None
    workdir = tempfile.mkdtemp()
    os.chmod(workdir, 0755)
    if os.getuid() == 0:
        os.chown(workdir, 99, 99)
    server = Postgres(workdir)
    try:
        server.start()

        # Initialize the old version
        migrated_db = createdb(server)
        if startrev:
            if os.system("hg up -C %s 1>&2" % startrev):
                sys.exit("hg failed")
            print 'Migrating from:'
            sys.stdout.flush()
            os.system("hg parents")
        else:
            restoredb(server, migrated_db, start)
            print 'Migrating from file', start
        migratedb(server, migrated_db)
        dumpdb(server, migrated_db, 'old.sql')
        with open('old.sql', 'a') as f:
            print >> f, '-- Generated on %s from revision %s' % (
                    time.strftime('%F %T %z'), startrev or '<unknown>')
        # Migrate to the new version
        if endrev:
            if os.system("hg up -C %s 1>&2" % endrev):
                sys.exit("hg failed")
            print 'Migrating to:'
            sys.stdout.flush()
            os.system("hg parents")
        else:
            print 'Migrating to working copy'
        migratedb(server, migrated_db)
        dumpdb(server, migrated_db, 'migrated.sql')
        with open('migrated.sql', 'a') as f:
            print >> f, ('-- Generated on %s by migrating from revision %s '
                    'to revision %s' % (time.strftime('%F %T %z'),
                        startrev or '<unknown>',
                        endrev or '<unknown>'))

        # Initialize a fresh copy of the new version
        fresh_db = createdb(server)
        migratedb(server, fresh_db)
        dumpdb(server, fresh_db, 'fresh.sql')
        with open('fresh.sql', 'a') as f:
            print >> f, '-- Generated on %s from revision %s' % (
                    time.strftime('%F %T %z'), endrev or '<unknown>')

        # Compare
        print
        print
        print 'Comparison result:'
        import explodeschema
        result = explodeschema.diff(server.connectPsyco(migrated_db),
                server.connectPsyco(fresh_db))

    finally:
        server.kill()
        util.rmtree(workdir)

    print
    if result:
        print 'FAILURE'
    else:
        print 'SUCCESS'


if __name__ == '__main__':
    main()
