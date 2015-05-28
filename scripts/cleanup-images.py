#!/usr/bin/python
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import optparse
import os
import sys

from conary import dbstore
from mint import config
from mint import urltypes


def main(args):
    parser = optparse.OptionParser()
    parser.add_option('-c', '--config-file', default=config.RBUILDER_CONFIG)
    parser.add_option('-n', '--dry-run', action='store_true')
    options, args = parser.parse_args(args)
    if args:
        parser.error("No arguments allowed")

    cfg = config.MintConfig()
    cfg.read(options.config_file)

    db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
    cu= db.cursor()

    print >> sys.stderr, "Cleaning up orphaned FilesUrls entries ..."
    db.transaction()
    cu.execute("""SELECT fileid, urlid, url FROM buildfilesurlsmap
            JOIN filesurls USING ( urlid ) WHERE urltype = ?""", urltypes.LOCAL)
    toDelete = []
    for fileId, urlId, path in cu:
        if not os.path.exists(path):
            toDelete.append(urlId)
    print >> sys.stderr, "Deleting %d dead FilesUrls entries" % len(toDelete)
    if toDelete:
        cu.execute("DELETE FROM filesurls WHERE urlid IN ( %s )" % (
                ', '.join('%d' % x for x in toDelete)))
    cu.execute("""DELETE FROM buildfiles a WHERE NOT EXISTS (
            SELECT * FROM buildfilesurlsmap b WHERE a.fileid = b.fileid )""")
    if options.dry_run:
        db.rollback()
    else:
        db.commit()

    print >> sys.stderr, "Cleaning up orphaned image files ..."
    trashedFiles = trashedDirs = trashedSize = 0
    for shortname in os.listdir(cfg.imagesPath):
        # list files on disk
        projpath = os.path.join(cfg.imagesPath, shortname)
        actualFiles = set()
        for dirpath, dirnames, filenames in os.walk(projpath):
            actualFiles.update(os.path.join(dirpath, x) for x in filenames)

        # list files in db
        cu.execute("""SELECT url FROM projects
                JOIN builds USING ( projectid )
                JOIN buildfiles USING ( buildid )
                JOIN buildfilesurlsmap USING ( fileid )
                JOIN filesurls USING ( urlid )
                WHERE shortname = ? AND urltype = ?
                """, shortname, urltypes.LOCAL)
        expectedFiles = set(x[0] for x in cu)

        # delete unmanaged files
        for path in actualFiles - expectedFiles:
            print >> sys.stderr, "Deleting", path
            trashedFiles += 1
            trashedSize += os.lstat(path).st_size
            if not options.dry_run:
                os.unlink(path)

        # clean up empty dirs
        if not options.dry_run:
            for dirpath, dirnames, filenames in os.walk(projpath,
                    topdown=False):
                if not dirnames and not filenames:
                    os.rmdir(dirpath)
                    trashedDirs += 1

    print >> sys.stderr, ("Deleted %d files and %d directories "
            "containing %d MiB" % (trashedFiles, trashedDirs,
                    trashedSize / 1048576.0))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
