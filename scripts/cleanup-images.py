#!/usr/bin/python

import os, sys
import pwd

if os.geteuid():
    print >> sys.stderr, "Script must be run as root to manipulate permissions"
    sys.exit(1)

from conary import dbstore
from mint import config

apacheGid = pwd.getpwnam('apache')[3]
isogenUid = pwd.getpwnam('isogen')[2]

cfg = config.MintConfig()
cfg.read('/srv/rbuilder/rbuilder.conf')
db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
cu = db.cursor()
cu.execute('SELECT filename FROM ImageFiles')
imageFiles = [x[0] for x in cu.fetchall()]

for baseDir, dirs, files in os.walk('/srv/rbuilder/finished-images'):
    if len(baseDir.split(os.path.sep)) == 6:
        os.chown(baseDir, isogenUid, apacheGid)
        os.chmod(baseDir, os.stat(baseDir)[0] & 0777 | 0020)
        for file in files:
            path = os.path.join(baseDir, file)
            if file not in imageFiles:
                os.unlink(path)
            else:
                os.chown(path, isogenUid, apacheGid)
