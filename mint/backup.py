#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#

import re, os, sys
import pwd
from mint import config
from mint import projects
from mint import schema
from conary.lib import util
from conary import dbstore
from conary import versions
import conary.errors
import conary.server.schema
from conary.conaryclient import cmdline

schemaCutoff = 37
knownGroupVersions = ('3\.1\.5.*', '4\..*')

staticPaths = ['config', 'logs', 'installable_iso.conf',
               'toolkit', 'iso_gen.conf', 'live_iso.conf',
               'bootable_image.conf']
# toolkit is linked to outgoing job server architecture.

def backup(cfg, out, backupMirrors = False):
    reposContentsDir = cfg.reposContentsDir.split(' ')
    backupPath = os.path.join(cfg.dataPath, 'tmp', 'backup')
    print >> out, backupPath
    util.mkdirChain(backupPath)
    dumpPath = os.path.join(backupPath, 'db.dump')
    if cfg.dbDriver == 'sqlite':
        util.execute("echo '.dump' | sqlite3 %s > %s" % (cfg.dbPath, dumpPath))
    extraArgs = ""
    if not backupMirrors:
        extraArgs = " WHERE NOT external"
    if cfg.reposDBDriver == 'sqlite':
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        cu = db.cursor()
        cu.execute("SELECT hostname, domainname FROM Projects%s" % extraArgs)
        for reposDir in ['.'.join(x) for x in cu.fetchall()]:
            cu.execute("SELECT toName FROM RepNameMap WHERE fromName=?",
                    reposDir)
            res = cu.fetchone()
            reposDir = res and res[0] or reposDir
            reposDBPath = cfg.reposDBPath % reposDir
            dumpPath = os.path.join(backupPath, '%s.dump' % reposDir)
            if os.path.exists(reposDBPath):
                util.execute("echo '.dump' | sqlite3 %s > %s" % \
                              (reposDBPath, dumpPath))
                print >> out, reposContentsDir[0] % reposDir
    elif cfg.reposDBDriver == 'postgresql':
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        cu = db.cursor()
        cu.execute("SELECT hostname, domainname FROM Projects%s" % extraArgs)
        for reposDir in ['.'.join(x) for x in cu.fetchall()]:
            reposDbName = reposDir.translate(projects.transTables['postgresql'])
            dbUser = cfg.reposDBPath.split('@')[0]
            dumpPath = os.path.join(backupPath, '%s.dump' % reposDbName)
            rdb = dbstore.connect(cfg.reposDBPath % 'postgres', 'postgresql')
            rcu = rdb.cursor()
            rcu.execute("SELECT datname FROM pg_database WHERE datname=?",
                         reposDbName)
            if rcu.fetchone():
                util.execute("pg_dump -U %s -c -O -d %s > %s" %\
                             (dbUser, reposDbName, dumpPath))
                print >> out, reposContentsDir[0] % reposDir
            rdb.close()

    for d in staticPaths:
        path = os.path.join(cfg.dataPath, d)
        if os.path.exists(path):
            print >> out, path

def restore(cfg):
    backupPath = os.path.join(cfg.dataPath, 'tmp', 'backup')
    dumpPath = os.path.join(backupPath, 'db.dump')
    if cfg.dbDriver == 'sqlite':
        if os.path.exists(cfg.dbPath):
            os.unlink(cfg.dbPath)
        util.execute("sqlite3 %s < %s" % (cfg.dbPath, dumpPath))
    db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
    schema.loadSchema(db, cfg, should_migrate=True)
    cu = db.cursor()
    cu.execute("SELECT hostname, domainname, projectId FROM Projects")
    for hostname, domainname, projectId in [x for x in cu.fetchall()]:
        repo = hostname + '.' + domainname
        cu.execute('SELECT toName FROM RepNameMap WHERE fromName=?', repo)
        r = cu.fetchone()
        if r:
            repo = r[0]
        dumpPath =  os.path.join(backupPath, repo).translate(projects.transTables[cfg.reposDBDriver]) + '.dump'
        reposPath = os.path.join(cfg.reposPath, repo)
        if os.path.exists(dumpPath):
            util.mkdirChain(os.path.join(reposPath, 'tmp'))
            if cfg.reposDBDriver == 'sqlite':
                dbPath = cfg.reposDBPath % repo
                if os.path.exists(dbPath):
                    os.unlink(dbPath)
                util.execute('sqlite3 %s < %s' % (dbPath, dumpPath))
                rdb = dbstore.connect(dbPath, cfg.reposDBDriver)
                conary.server.schema.loadSchema(rdb, doMigrate=True)
                rdb.close()
            elif cfg.reposDBDriver == 'postgresql':
                pgRepo = repo.translate(projects.transTables['postgresql'])
                dbPath = cfg.reposDBPath % pgRepo
                rdb = dbstore.connect('%s' % (cfg.reposDBPath % 'postgres'),
                                      cfg.reposDBDriver)
                rcu = rdb.cursor()
                rcu.execute("SELECT datname FROM pg_database WHERE datname=?",
                             pgRepo)
                if rcu.fetchone():
                    rcu.execute("DROP DATABASE %s" % pgRepo)
                    rcu.execute("CREATE DATABASE %s ENCODING 'UTF8'" % pgRepo)
                rdb.close()

                dbUser = cfg.reposDBPath.split('@')[0]
                util.execute('cat %s | psql -U %s %s'% (dumpPath, dbUser, pgRepo))
                rdb = dbstore.connect('%s' % (cfg.reposDBPath % 'postgres'),
                                      cfg.reposDBDriver)
                conary.server.schema.loadSchema(rdb, doMigrate=True)
                rdb.close()
        else:
            cu.execute("SELECT * FROM InboundMirrors WHERE targetProjectId=?", projectId)
            localMirror = cu.fetchone_dict()
            if localMirror:
                if not os.path.exists(reposPath):
                    # revert Labels table to pre-mirror settings
                    cu.execute( \
                            "UPDATE Labels SET url=?, username=?, password=?" \
                                " WHERE projectId=?",
                        localMirror['sourceUrl'],
                        localMirror['sourceUsername'],
                        localMirror['sourcePassword'], projectId)

                    cu.execute("DELETE FROM RepNameMap WHERE toName=?", repo)
                    cu.execute( \
                        "DELETE FROM InboundMirrors WHERE inboundMirrorId=?",
                        localMirror['inboundMirrorId'])

    # delete package index to ensure we don't reference troves until they're
    # restored.
    try:
        cu.execute('DELETE FROM PackageIndex')
        cu.execute('DELETE FROM PackageIndexMark')
    except:
        # this masks errors, since it does re-raise but we don't care.
        # impact and cost are negligible.
        db.rollback()
    else:
        db.commit()

def prerestore(cfg):
    util.execute("service httpd stop")
    for repo in os.listdir(cfg.reposPath):
        reposPath = os.path.join(cfg.reposPath, repo)
        util.rmtree(reposPath, ignore_errors = True)

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
        os.setgid(apacheGID)
        os.setuid(apacheUID)
    try:
        func(*args, **kwargs)
    except:
        exception, e, bt = sys.exc_info()
        if exception in (OSError, IOError):
            errno = e.errno
        else:
            errno = 1
        import traceback
        print >> sys.stderr, ''.join(traceback.format_tb(bt))
        print >> sys.stderr, exception, e
    sys.exit(errno)

def run():
    cfg = config.MintConfig()
    cfg.read(config.RBUILDER_CONFIG)
    migration = bool(os.getenv('RBA_MIGRATION'))
    mode = (len(sys.argv) > 1) and sys.argv[1] or ''
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

