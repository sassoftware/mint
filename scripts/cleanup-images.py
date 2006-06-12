#!/usr/bin/python

import os, sys
import pwd

dryRun = False
if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
    dryRun = True
elif len(sys.argv) > 1:
    print "usage: cleanup-images.py [--dry-run]"
    sys.exit(1)

if not dryRun and os.geteuid():
    print >> sys.stderr, "Script not run as root: forcing --dry-run"
    dryRun = True

from conary import dbstore
from mint import config

apacheGid = pwd.getpwnam('apache')[3]
isogenUid = pwd.getpwnam('isogen')[2]

cfg = config.MintConfig()
cfg.read(config.RBUILDER_CONFIG)
db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
cu = db.cursor()
cu.execute('SELECT filename FROM ImageFiles')
imageFiles = [x[0] for x in cu.fetchall()]

for baseDir, dirs, files in os.walk(cfg.imagesPath):
    if len(baseDir.split(os.path.sep)) == 6:
        if dryRun:
            print "chown %d.%d %s" % (isogenUid, apacheGid, baseDir)
            print "chmod %0o %s" % (os.stat(baseDir)[0] & 0777 | 0020, baseDir)
        else:
            os.chown(baseDir, isogenUid, apacheGid)
            os.chmod(baseDir, os.stat(baseDir)[0] & 0777 | 0020)
        for file in files:
            path = os.path.join(baseDir, file)
            if file not in imageFiles:
                if dryRun:
                    print "rm -f %s" % path
                else:
                    os.unlink(path)
            else:
                if dryRun:
                    print "chown %d.%d %s" % (isogenUid, apacheGid, path)
                else:
                    os.chown(path, isogenUid, apacheGid)
