#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

from mint import config
from mint import database
from mint import scriptlibrary
import time

from conary import dbstore
from conary.dbstore.sqllib import toDatabaseTimestamp

class RankedProjectListTable(database.DatabaseTable):
    name = None
    daysBack = 0
    fields = ['projectId', 'rank']

    def __init__(self, db):
        if self.name is None:
            raise NotImplementedError

        self.createSQL = """
            CREATE TABLE %s (
                projectId   INTEGER NOT NULL,
                rank        INT NOT NULL
            )""" % self.name

        return database.DatabaseTable.__init__(self, db)


    def setList(self, idList):
        cu = self.db.cursor()
        cu.execute("DELETE FROM %s" % self.name)
        cu.executemany("INSERT INTO %s (rank, projectId) VALUES (?, ?)" % self.name,
            enumerate(idList))
        self.db.commit()

    def getList(self):
        cu = self.db.cursor()
        cu.execute("SELECT projectId, hostname, name FROM %s JOIN Projects USING(projectId) ORDER BY rank LIMIT 10" % self.name)
        return cu.fetchall_dict()

    def calculate(self):
        if not self.daysBack:
            raise NotImplementedError

        l = calculateTopProjects(self.db, self.daysBack)
        self.setList(l)


# the following definitions are subject to change

# "Top Projects" to be based on the top 10 projects based on downloads for
# the year. Downloads can be of any image type and are counted based on the
# previous year's (365 days) download totals.
class TopProjectsTable(RankedProjectListTable):
    name = "TopProjects"
    daysBack = 365

# "Most Popular" projects list to be based on the top 10 projects based on
# downloads for the week. Downloads can be of any image type and are counted
# based on the previous week's (7 days) download totals.
class PopularProjectsTable(RankedProjectListTable):
    name = "PopularProjects"
    daysBack = 7


class FrontPageSelectionsTable(database.KeyedTable):
    name = 'FrontPageSelections'
    key = 'itemId'
    createSQL = """CREATE TABLE FrontPageSelections (
                    itemId          %(PRIMARYKEY)s,
                    name            CHAR(255),
                    link            CHAR(255),
                    rank            INT
                );
                """
    fields = ['itemId', 'name', 'link', 'rank' ] 

    def __init__(self, db, cfg):
        database.DatabaseTable.__init__(self, db)
        self.cfg = cfg

    def addItem(self, name, link, rank):
        cu = self.db.cursor()
        cu.execute("INSERT INTO %s VALUES (NULL, ?, ?, ?)" % \
                    self.name, name, link, rank)
        self.db.commit()
        return True

    def getAll(self):
        cu = self.db.cursor()
        cu.execute("SELECT * FROM %s ORDER BY rank" % self.name)
        return cu.fetchall_dict() or False

    def deleteItem(self, itemId):
        cu = self.db.cursor()
        cu.execute("DELETE FROM %s WHERE itemId=?" % self.name, itemId)
        self.db.commit()
        return True


def calculateTopProjects(db, daysBack = 7):
    cu = db.cursor()

    if db.driver == "sqlite":
        # brute-force method since sqlite doesn't
        # handle subselects the way MySQL can
        counts = {}
        cu.execute("SELECT urlId FROM UrlDownloads WHERE timeDownloaded > ?",
            toDatabaseTimestamp(time.time() - (daysBack * 86400)))
        for x in cu.fetchall():
            # fetch projectId
            cu.execute("""SELECT projectId FROM Builds
                            JOIN BuildFiles USING(buildId)
                            JOIN BuildFilesUrlsMap USING(fileId)
                            JOIN FilesUrls USING (urlId)
                          WHERE urlId = ?""", x[0])
            projectId = cu.fetchone()
            if not projectId:
                continue

            c = counts.setdefault(projectId[0], [0])
            c[0] += 1

        counts = counts.items()
        counts.sort(key = lambda x: x[1][0], reverse = True)

        return [x[0] for x in counts]
    else:
        cu.execute("""SELECT COUNT(urlId) AS downloads, urlId AS outerUrlId,
            (SELECT DISTINCT projectid From Builds
                JOIN Buildfiles USING(buildId)
                JOIN BuildFilesUrlsMap USING(fileId)
                JOIN FilesUrls USING (urlId) WHERE urlId=outerUrlId) AS projectId
                FROM UrlDownloads WHERE timeDownloaded > ?
                GROUP BY projectId
                ORDER BY downloads DESC""", toDatabaseTimestamp(time.time()-(daysBack * 86400)))
        import epdb
        epdb.st()
        return [int(x['projectId']) for x in cu.fetchall_dict()]

class UpdateProjectLists(scriptlibrary.SingletonScript):
    db = None
    cfg = None
    cfgPath = config.RBUILDER_CONFIG

    def __init__(self, aLockPath = scriptlibrary.DEFAULT_LOCKPATH):
        self.cfg = config.MintConfig()
        self.cfg.read(self.cfgPath)
        scriptlibrary.SingletonScript.__init__(self, aLockPath)

    def action(self):
        self.db = dbstore.connect(self.cfg.dbPath, self.cfg.dbDriver)
        self.db.loadSchema()
        topProjects = TopProjectsTable(self.db)
        popularProjects = PopularProjectsTable(self.db)

        topProjects.calculate()
        popularProjects.calculate()

        return 0

    def cleanup(self):
        if self.db:
            self.db.close()
