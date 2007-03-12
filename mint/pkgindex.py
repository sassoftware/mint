#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

from conary import versions

from mint import database
from mint import searcher


termMap = {
    'branch': 'branchName',
    'server': 'serverName',
}


class PackageIndexTable(database.KeyedTable):
    name = 'PackageIndex'
    key = 'pkgId'

    createSQL = """
        CREATE TABLE PackageIndex (
            pkgId       %(PRIMARYKEY)s,
            projectId   INT,
            name        CHAR(255),
            version     CHAR(255),
            serverName  VARCHAR(254) NOT NULL,
            branchName  VARCHAR(254) NOT NULL,
            isSource    INT DEFAULT '0'
        )"""

    fields = ['pkgId', 'projectId', 'name', 'version']

    indexes = {
        "PackageNameIdx":
            """CREATE INDEX PackageNameIdx ON PackageIndex(name, version)""",
        "PackageIndexProjectIdx":
            """CREATE INDEX PackageIndexProjectIdx ON PackageIndex(projectId)""",
        "PackageIndexServerBranchName":
            """CREATE INDEX PackageIndexServerBranchName ON PackageIndex(serverName, branchName)"""
    }

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            if dbversion == 26 and not self.initialCreation:
                self.db.dropIndex("PackageIndex", "PackageNameIdx")
                cu = self.db.cursor()
                cu.execute("CREATE INDEX PackageNameIdx ON PackageIndex(name, version)")
                self.db.commit()
            if dbversion == 28 and not self.initialCreation:
                cu = self.db.cursor()
                cu.execute("ALTER TABLE PackageIndex ADD COLUMN serverName CHAR(255)")
                cu.execute("ALTER TABLE PackageIndex ADD COLUMN branchName CHAR(255)")
                cu.execute("ALTER TABLE PackageIndex ADD COLUMN isSource CHAR(255) DEFAULT '0'")

                cu.execute("SELECT pkgId, version FROM PackageIndex")
                updates = []
                for x in cu.fetchall():
                    pkgId = x[0]
                    label = versions.VersionFromString(x[1]).branch().label()
                    serverName = label.getHost()
                    branchName = label.getNamespace() + ":" + label.getLabel()
                    updates.append((serverName, branchName, pkgId))
                cu.executemany("UPDATE PackageIndex SET serverName=?, branchName=? WHERE pkgId=?", updates)

            return dbversion >= 28
        return True

    def search(self, terms, limit, offset):
        columns = ['name', 'version', 'projectId']
        searchcols = ['name']

        terms, limiters = searcher.parseTerms(terms)
        extras, extraSubs = searcher.limitersToSQL(limiters, termMap)

        # with any kind of branch/server limiters, assume we want
        # to filter out sources too.
        if limiters:
            extras += " AND isSource=0"

        terms = " ".join(terms)

        ids, count = database.KeyedTable.search(self, columns, 'PackageIndex',
            searcher.Searcher.where(terms, searchcols, extras, extraSubs),
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


