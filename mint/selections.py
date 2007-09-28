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
from mint.helperfuncs import toDatabaseTimestamp

# A convenience table with the latest timestamp of commit
# of each project in rBuilder's database:
class LatestCommitTable(database.DatabaseTable):
    name = "LatestCommit"
    fields = ['projectId', 'commitTime']

    createSQL = """
        CREATE TABLE LatestCommit (
            projectId   INTEGER NOT NULL,
            commitTime  INTEGER NOT NULL,
            CONSTRAINT LatestCommit_projectId_fk
                FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                    ON DELETE CASCADE
        )"""

    indexes = {'LatestCommitTimestamp':
        'CREATE INDEX LatestCommitTimestamp ON LatestCommit(projectId, commitTime)'}


    def calculate(self):
        cu = self.db.cursor()
        cu.execute("DELETE FROM LatestCommit")
        cu.execute("""INSERT INTO LatestCommit(projectId, commitTime)
                SELECT projectId as projectId, MAX(timestamp) AS commitTime FROM Commits
                GROUP BY projectId""")
        self.db.commit()


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
                rank        INTEGER NOT NULL,
                CONSTRAINT %s_projectId_fk
                    FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                        ON DELETE CASCADE
            )""" % (self.name, self.name)

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

    cu.execute("""SELECT COUNT(UrlDownloads.urlId) AS downloads,
          Builds.projectId AS projectId
          FROM UrlDownloads JOIN FilesUrls USING (urlId)
                            JOIN BuildFilesUrlsMap USING (urlId)
                            JOIN BuildFiles USING (fileId)
                            JOIN Builds USING (buildId)
          WHERE timeDownloaded > ?
          GROUP BY projectId
          ORDER BY downloads DESC""", toDatabaseTimestamp(time.time()-(daysBack * 86400)))
    return [int(x[1]) for x in cu.fetchall() if x[1] != None]

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
        latestCommits = LatestCommitTable(self.db)

        topProjects.calculate()
        popularProjects.calculate()
        latestCommits.calculate()

        return 0

    def cleanup(self):
        if self.db:
            self.db.close()
