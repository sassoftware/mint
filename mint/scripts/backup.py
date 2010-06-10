#
# Copyright (c) 2005-2009 rPath, Inc.
#
# All rights reserved
#

import logging, re, os, sys
import pwd
from mint import config
from mint.db import projects
from mint.db import schema
from mint.db import repository
from conary.lib import util
from conary import dbstore
from conary import versions
import conary.errors
import conary.server.schema
from conary.conaryclient import cmdline
from mint.lib import mintutils, siteauth

log = logging.getLogger(__name__)

schemaCutoff = 37
knownGroupVersions = ('3\.1\.(\d{2}|[56789])(\.\d+)?$', '4\..*', '5\..*')


def backup(cfg, out, backupMirrors = False):
    reposContentsDir = cfg.reposContentsDir.split(' ')
    backupPath = os.path.join(cfg.dataPath, 'tmp', 'backup')
    print >> out, backupPath
    util.rmtree(backupPath, ignore_errors=True)
    util.mkdirChain(backupPath)

    # Dump mintDB
    dumpPath = os.path.join(backupPath, 'db.dump')
    if cfg.dbDriver == 'sqlite':
        util.execute("echo '.dump' | sqlite3 %s > %s" % (cfg.dbPath, dumpPath))
    elif cfg.dbDriver in ('postgresql', 'pgpool'):
        dbName = cfg.dbPath.rsplit('/', 1)[-1]
        util.execute("pg_dump -U postgres -p 5439 '%s' > '%s'"
                % (dbName, dumpPath))

    mintDb = dbstore.connect(cfg.dbPath, cfg.dbDriver)
    repoMgr = repository.RepositoryManager(cfg, mintDb)
    for repoHandle in repoMgr.iterRepositories():
        if not repoHandle.hasDatabase:
            continue
        if (repoHandle.isExternal and not backupMirrors
                and not repoHandle.hasContentSources):
            continue

        dumpPath = os.path.join(backupPath, repoHandle.fqdn + ".dump")
        repoHandle.dump(dumpPath)

        # Only save the first content store since the only installation with
        # multiple stores is rBO, and rBO doesn't use this script.
        print >> out, repoHandle.contentsDirs[0]

    # Handle configs separately so we can exclude rbuilder.conf
    backup_path = os.path.join(cfg.dataPath, 'config')
    if os.path.exists(backup_path):
        for config_file in os.listdir(backup_path):
            if config_file != 'rbuilder.conf':
                path = os.path.join(backup_path, config_file)
                print >> out, path
    capsuleDir = os.path.join(cfg.dataPath, 'capsules')
    if os.path.exists(capsuleDir) and os.listdir(capsuleDir):
        print >> out, capsuleDir


def restore(cfg):
    backupPath = os.path.join(cfg.dataPath, 'tmp', 'backup')

    dumpPath = os.path.join(backupPath, 'db.dump')
    if cfg.dbDriver == 'sqlite':
        if os.path.exists(cfg.dbPath):
            os.unlink(cfg.dbPath)
        util.execute("sqlite3 %s < %s" % (cfg.dbPath, dumpPath))
    elif cfg.dbDriver in ('postgresql', 'pgpool'):
        dbName = cfg.dbPath.rsplit('/', 1)[-1]

        controlDb = dbstore.connect('postgres@localhost:5439/postgres',
                'postgresql')
        ccu = controlDb.cursor()

        # If the database exists ...
        ccu.execute("""SELECT COUNT(*) FROM pg_catalog.pg_database
                WHERE datname = ?""", dbName)
        if ccu.fetchone()[0]:
            # ... then drop it first.
            log.info("Dropping existing mint database")
            ccu.execute("DROP DATABASE %s" % (dbName,))

        ccu.execute("CREATE DATABASE %s ENCODING 'UTF8' OWNER rbuilder"
                % (dbName,))
        controlDb.close()

        util.execute("psql -U postgres -p 5439 -f '%s' '%s' >/dev/null"
                % (dumpPath, dbName))

    driver, path = cfg.dbDriver, cfg.dbPath
    if driver == 'pgpool':
        driver = 'postgresql'
        path = path.replace(':6432', ':5439')
        # HACK: mint config says to connect as rbuilder@ but pgbouncer.ini
        # rewrites it all to postgres@, so the path through the bouncer ends up
        # creating everything as owned by postgres and now that we try to
        # connect around it we can't. So, make things worse and connect as
        # postgres here, too!
        path = path.replace('rbuilder@', 'postgres@')

    db = dbstore.connect(path, driver)
    schema.loadSchema(db, cfg, should_migrate=True)
    log.info("mintdb successfully restored")

    cu = db.transaction()
    repoMgr = repository.RepositoryManager(cfg, db, bypass=True)
    for repoHandle in repoMgr.iterRepositories():
        if not repoHandle.hasDatabase:
            continue

        dumpPath = os.path.join(backupPath, repoHandle.fqdn + ".dump")
        if os.path.exists(dumpPath):
            log.debug("Restoring project %s", repoHandle.shortName)
            for path in repoHandle.contentsDirs:
                util.mkdirChain(path)

            repoHandle.restore(dumpPath)

        elif repoHandle.isExternal:
            # Inbound mirrors that didn't get backed up revert to cache mode.
            log.warning("External project %r was not backed up; reverting to "
                    "cached mode.", repoHandle.shortName)
            repoHandle.drop()

            cu.execute("SELECT * FROM InboundMirrors WHERE targetProjectId=?",
                    repoHandle.projectId)
            localMirror = cu.fetchone_dict()

            # Copy permissions from InboundMirrors to Labels
            cu.execute("UPDATE Projects SET database = NULL "
                    "WHERE projectId = ?", repoHandle.projectId)
            cu.execute("UPDATE Labels SET url = ?, authtype = ?, username = ?, "
                    "password = ?, entitlement = ? WHERE projectId = ?",
                    localMirror['sourceUrl'],
                    localMirror['sourceAuthType'],
                    localMirror['sourceUsername'],
                    localMirror['sourcePassword'],
                    localMirror['sourceEntitlement'],
                    repoHandle.projectId)

            cu.execute( \
                "DELETE FROM InboundMirrors WHERE inboundMirrorId=?",
                localMirror['inboundMirrorId'])

        else:
            log.error("Database dump missing for project %r.", repoHandle.shortName)

    db.commit()

    # delete package index to ensure we don't reference troves until they're
    # restored.
    cu = db.transaction()
    try:
        cu.execute('DELETE FROM PackageIndex')
        cu.execute('DELETE FROM PackageIndexMark')
    except:
        log.warning("Error clearing package index:", exc_info=True)
        db.rollback()
    else:
        db.commit()

    # Everything beyond this point runs as root again
    restorePrivs()

    auth = siteauth.SiteAuthorization(cfg.siteAuthCfgPath)
    auth.update()

    log.info("Restore complete.")


def prerestore(cfg):
    util.execute("service httpd stop")
    # pgbouncer holds database connections open for 45s
    util.execute("service pgbouncer stop")


def clean(cfg):
    backupPath = os.path.join(cfg.dataPath, 'tmp', 'backup')
    util.rmtree(backupPath, ignore_errors = True)

def metadata(cfg, out):
    db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
    cu = db.cursor()
    cu.execute("SELECT COALESCE(MAX(version), 0) FROM DatabaseVersion")
    schemaVersion = cu.fetchone()[0]
    print >> out, "rBuilder_schemaVersion=%d" % schemaVersion
    cu.execute("SELECT COALESCE(MAX(minor), 0) FROM DatabaseVersion")
    schemaMinor = cu.fetchone()[0]
    print >> out, "rBuilder_schemaMinor=%d" % schemaMinor
    sys.stdout.flush()

# XXX This version is used internally since our handler expects
#     an exception, while rAPA expects a True/False return.
def _isValid(cfg, input):
    if not isValid(cfg, input):
        raise RuntimeError("Invalid Backup")

def isValid(cfg, input):
    data = input.read()
    metaData = dict()
    for x in data.splitlines():
        if '=' in x:
           k, v = x.split('=', 1)
           metaData[k] = v
    schemaVersion = int(metaData.get('rBuilder_schemaVersion', 0))
    if schemaVersion == 0 or schemaVersion < schemaCutoff:
        return False
    NVF = metaData.get('NVF')
    if not NVF:
        return False
    verStr = cmdline.parseTroveSpec(NVF)[1]
    try:
        trailingVer = versions.VersionFromString(verStr).trailingRevision().version
    except conary.errors.ParseError:
        return False
    foundMatch = False
    for pat in knownGroupVersions:
        if re.match(pat, trailingVer):
            foundMatch = True
            break
    return foundMatch

def usage(out = sys.stderr):
    print >> out, sys.argv[0] + ":"
    print >> out, "    [b/backup]: back up databases and issue manifest."
    print >> out, "    [r/restore]: restore databases."
    print >> out, "    [c/clean]: clean up temporary files used during backup."
    print >> out, "    [m/metadata]: print appliance metadata in name=value format."
    print >> out, "    [isValid]: determine if metadata on stdin is for a compatible backup."
    print >> out, "    [prerestore]: prepare to restore databases."

def handle(func, *args, **kwargs):
    errno = 0
    if kwargs.pop('dropPriv', True):
        apacheUID, apacheGID = pwd.getpwnam('apache')[2:4]
        os.setegid(apacheGID)
        os.seteuid(apacheUID)
    try:
        func(*args, **kwargs)
    except:
        log.exception("Unhandled error in restore process:")
        sys.exit(1)
    sys.exit(errno)


def restorePrivs():
    os.seteuid(0)
    os.setegid(0)


def run():
    cfg = config.MintConfig()
    cfg.read(config.RBUILDER_CONFIG)

    logPath = os.path.join(cfg.logPath, 'scripts.log')
    mintutils.setupLogging(logPath, fileLevel=logging.DEBUG)

    migration = bool(os.getenv('RBA_MIGRATION'))
    mode = (len(sys.argv) > 1) and sys.argv[1] or ''
    log.debug("rBuilder backup script invoked in mode %r", mode)
    if mode in ('r', 'restore'):
        handle(restore, cfg)
    elif mode  == 'prerestore':
        handle(prerestore, cfg, dropPriv = False)
    elif mode in ('b', 'backup'):
        handle(backup, cfg, sys.stdout, backupMirrors = migration)
    elif mode in ('c', 'clean'):
        handle(clean, cfg)
    elif mode in ('m', 'metadata'):
        handle(metadata, cfg, sys.stdout)
    elif mode == 'isValid':
        handle(_isValid, cfg, sys.stdin)
    elif mode.upper() in ('?', 'H', 'HELP'):
        usage(out = sys.stdout)
    else:
        usage()

if __name__ == '__main__':
    sys.exit(run())
