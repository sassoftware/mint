#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
from mint import database
from mint import searcher

from mint import config
from mint import scriptlibrary
from conary import dbstore
from conary import versions

import os
import os.path
import sys


class PackageIndexTable(database.KeyedTable):
    name = 'PackageIndex'
    key = 'pkgId'

    createSQL = """
        CREATE TABLE PackageIndex (
            pkgId       %(PRIMARYKEY)s,
            projectId   INT,
            name        CHAR(255),
            version     CHAR(255)
        )"""

    fields = ['pkgId', 'projectId', 'name', 'version']

    indexes = {"PackageNameIdx": """CREATE INDEX PackageNameIdx
                                        ON PackageIndex(name)""",
               "PackageIndexProjectIdx": """CREATE INDEX PackageIndexProjectIdx
                                                ON PackageIndex(projectId)"""}

    def search(self, terms, limit, offset):
        columns = ['name', 'version', 'projectId']
        searchcols = ['name']

        ids, count = database.KeyedTable.search(self, columns, 'PackageIndex',
            searcher.Searcher.where(terms, searchcols),
            searcher.Searcher.order(terms, searchcols, 'name'),
            None, limit, offset)

        for i, x in enumerate(ids[:]):
            ids[i] = list(x)

        return ids, count

    def __init__(self, db):
        database.KeyedTable.__init__(self, db)

        # create this table without an associated KeyedTable
        # or DatabaseTable object, since nobody uses this but
        # update-package-index.
        if "PackageIndexMark" not in db.tables:
            cu = db.cursor()
            cu.execute("CREATE TABLE PackageIndexMark (mark INT)")
            cu.execute("INSERT INTO PackageIndexMark VALUES(0)")
            self.db.commit()


class UpdatePackageIndex(scriptlibrary.SingletonScript):
    db = None
    cfgPath = config.RBUILDER_CONFIG

    def __init__(self, aLockPath = scriptlibrary.DEFAULT_LOCKPATH):
        self.cfg = config.MintConfig()
        self.cfg.read(self.cfgPath)
        self.logPath = os.path.join(self.cfg.dataPath, 'logs', 'package-index.log')
        scriptlibrary.SingletonScript.__init__(self, aLockPath)

    def action(self):
        self.log.info("Updating package index")

        self.db = dbstore.connect(self.cfg.dbPath, driver = self.cfg.dbDriver)
        self.db.loadSchema()
        cu = self.db.cursor()

        try:
            cu.execute('SELECT COUNT(*) FROM PackageIndexMark')
            if not cu.fetchone()[0]:
                cu.execute('INSERT INTO PackageIndexMark VALUES(0)')
            cu.execute("SELECT IFNULL(MAX(timestamp), 0) FROM Commits")
            newMark = cu.fetchone()[0]

            # Clear out Package index if the timestamp in PackageIndexMark == 0
            cu.execute("""DELETE FROM PackageIndex WHERE
                              (SELECT mark FROM PackageIndexMark) = 0""")

            cu.execute("""SELECT Projects.projectId, troveName, version,
                                 timestamp
                              FROM Commits
                              LEFT JOIN Projects
                                  ON Commits.projectId=Projects.projectId
                              WHERE troveName NOT LIKE '%:%'
                              AND hidden=0 AND disabled=0
                              AND timestamp >=
                                  (SELECT mark FROM PackageIndexMark)""")

            res = cu.fetchall()
            numPkgs = len(res) - 1
            if numPkgs > 0:
                self.log.info("Indexing %d packages" % numPkgs)
            else:
                self.log.info("Package index is up to date")
            packageDict = {}
            labelMap = {}
            for projectId, troveName, verStr, timeStamp in res:
                troveEntry = packageDict.setdefault(troveName, {})
                version = versions.VersionFromString(verStr)
                label = str(version.branch().label())
                versionList = troveEntry.setdefault(label, [])

                version.resetTimeStamps(timeStamp)
                versionList.append(version)
                labelMap[label] = projectId

            packageIndex = []
            for troveName in packageDict:
                for label in packageDict[troveName]:
                    packageIndex.append((labelMap[label], troveName,
                                         max(packageDict[troveName][label])))

            for projectId, troveName, version in packageIndex:
                cu.execute("""SELECT pkgId, version FROM PackageIndex
                                  WHERE projectId=? AND name=?""",
                           projectId, troveName)

                res = [x[0] for x in cu.fetchall() if \
                       versions.VersionFromString(x[1]).branch().label() == \
                       version.branch().label()]

                if not res:
                    cu.execute("""INSERT INTO PackageIndex
                                      (projectId, name, version)
                                      VALUES (?, ?, ?)""",
                               projectId, troveName, str(version))
                    pass
                else:
                    pkgId = res[0]
                    cu.execute("""UPDATE PackageIndex SET
                                          projectId=?, name=?, version=?
                                          WHERE pkgId=?""",
                               projectId, troveName, str(version), pkgId)

            cu.execute("UPDATE PackageIndexMark SET mark=?", newMark)
        except Exception, e:
            self.log.error("Error occured: %s" % str(e))
            self.db.rollback()
            exitcode = 1
            raise
        else:
            self.log.info("Completed successfully")
            exitcode = 0
            self.db.commit()
        return exitcode

    def cleanup(self):
        if self.db:
            self.db.close()

if __name__ == "__main__":
    upi = UpdatePackageIndex()
    os._exit(upi.run())

