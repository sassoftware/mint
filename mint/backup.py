#!/usr/bin/python
#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#

import os, sys
import pwd
from mint import config
from conary.lib import util
from conary import dbstore
import conary.server.schema

staticPaths = ['config', 'entitlements', 'logs', 'installable_iso.conf',
               'toolkit', 'iso_gen.conf', 'live_iso.conf',
               'bootable_image.conf']
# toolkit is linked to outgoing job server architecture.

def backup(cfg, out):
    reposContentsDir = cfg.reposContentsDir.split(' ')
    backupPath = os.path.join(cfg.dataPath, 'tmp', 'backup')
    print >> out, backupPath
    util.mkdirChain(backupPath)
    dumpPath = os.path.join(backupPath, 'db.dump')
    if cfg.dbDriver == 'sqlite':
        util.execute("echo '.dump' | sqlite3 %s > %s" % (cfg.dbPath, dumpPath))
    if cfg.reposDBDriver == 'sqlite':
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        cu = db.cursor()
        cu.execute("""SELECT hostname, domainname
                          FROM Projects WHERE NOT external""")
        for reposDir in ['.'.join(x) for x in cu.fetchall()]:
            reposDBPath = cfg.reposDBPath % reposDir
            dumpPath = os.path.join(backupPath, '%s.dump' % reposDir)
            if os.path.exists(reposDBPath):
                util.execute("echo '.dump' | sqlite3 %s > %s" % \
                              (reposDBPath, dumpPath))
                print >> out, reposContentsDir[0] % reposDir
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
    cu = db.cursor()
    cu.execute("SELECT hostname, domainname, projectId FROM Projects")
    for hostname, domainname, projectId in [x for x in cu.fetchall()]:
        repo = hostname + '.' + domainname
        cu.execute('SELECT toName FROM RepNameMap WHERE fromName=?', repo)
        r = cu.fetchone()
        if r:
            repo = r[0]
        dumpPath =  os.path.join(backupPath, repo + '.dump')
        reposPath = os.path.join(cfg.reposPath, repo)
        if os.path.exists(dumpPath):
            util.mkdirChain(os.path.join(reposPath, 'tmp'))
            if cfg.dbDriver == 'sqlite':
                dbPath = cfg.reposDBPath % repo
                if os.path.exists(dbPath):
                    os.unlink(dbPath)
                util.execute('sqlite3 %s < %s' % (dbPath, dumpPath))
        else:
            cu.execute("SELECT * FROM InboundMirrors WHERE targetProjectId=?", projectId)
            localMirror = cu.fetchone_dict()
            if localMirror:
                # convert back to external-only project for later mirroring
                util.rmtree(reposPath, ignore_errors = True)

                # revert Labels table to pre-mirror settings
                cu.execute("UPDATE Labels SET url=?, username=?, password=?",
                    localMirror['sourceUrl'], localMirror['sourceUsername'],
                    localMirror['sourcePassword'])

                cu.execute("DELETE FROM RepNameMap WHERE toName=?", repo)
                cu.execute("DELETE FROM InboundMirrors WHERE inboundMirrorId=?",
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

def clean(cfg):
    backupPath = os.path.join(cfg.dataPath, 'tmp', 'backup')
    util.rmtree(backupPath, ignore_errors = True)

def usage(out = sys.stderr):
    print >> out, sys.argv[0] + ":"
    print >> out, "    [b/backup]: back up databases and issue manifest."
    print >> out, "    [r/restore]: restore databases."
    print >> out, "    [c/clean]: clean up temporary files used during backup."

def handle(func, *args, **kwargs):
    errno = 0
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
    apacheUID, apacheGID = pwd.getpwnam('apache')[2:4]
    os.setgid(apacheGID)
    os.setuid(apacheUID)
    cfg = config.MintConfig()
    cfg.read(config.RBUILDER_CONFIG)
    mode = (len(sys.argv) > 1) and sys.argv[1] or ''
    if mode in ('r', 'restore'):
        sys.exit(handle(restore, cfg))
    elif mode in ('b', 'backup'):
        sys.exit(handle(backup, cfg, sys.stdout))
    elif mode in ('c', 'clean'):
        sys.exit(handle(clean, cfg))
    elif mode.upper() in ('?', 'H', 'HELP'):
        usage(out = sys.stdout)
    else:
        usage()

