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
from mint import urltypes

apacheGid = pwd.getpwnam('apache')[3]
isogenUid = pwd.getpwnam('isogen')[2]

cfg = config.MintConfig()
cfg.read(config.RBUILDER_CONFIG)
db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
cu = db.cursor()
cu.execute('SELECT url FROM FilesUrls WHERE urlType = ?', urltypes.LOCAL)
imageFiles = [x[0] for x in cu.fetchall()]

deleteCount = bytesDeletedCount = long(0)
for baseDir, dirs, files in os.walk(cfg.imagesPath):
    if len(baseDir.split(os.path.sep)) == 6:
        if dryRun:
            print "# ++ UPDATING PERMISSIONS/OWNERSHIP ON %s" % baseDir
            print "chown %d.%d %s" % (isogenUid, apacheGid, baseDir)
            print "chmod %0o %s" % (os.stat(baseDir)[0] & 0777 | 0020, baseDir)
        else:
            os.chown(baseDir, isogenUid, apacheGid)
            os.chmod(baseDir, os.stat(baseDir)[0] & 0777 | 0020)
        for file in files:
            path = os.path.join(baseDir, file)
            if path not in imageFiles:
                if dryRun:
                    print "# -- DELETING IMAGE %s" % path
                    print "rm -f %s" % path
                else:
                    os.unlink(path)
                deleteCount += 1
                bytesDeletedCount += os.stat(path)[6]
            else:
                if dryRun:
                    print "chown %d.%d %s" % (isogenUid, apacheGid, path)
                else:
                    os.chown(path, isogenUid, apacheGid)

sys.stdout.flush()
if dryRun:
    print >> sys.stderr, "# -- %d images would have been deleted (%ld MBytes)" % (deleteCount, (bytesDeletedCount / (1024 * 1024)))
else:
    print >> sys.stderr, "%d images deleted (%ld MBytes)" % (deleteCount, (bytesDeletedCount / (1024 * 1024)))
sys.stderr.flush()
