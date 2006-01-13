#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import database
from conary import versions

class CommitsTable(database.DatabaseTable):
    name = "Commits"
    fields = ['projectId', 'timestamp', 'troveName', 'version', 'userId']

    createSQL = """
        CREATE TABLE Commits (
            projectId   INT,
            timestamp   INT,
            troveName   CHAR(255),
            version     TEXT,
            userId      INT
        );"""

    indexes = {'CommitsProjectIdx' : """CREATE INDEX CommitsProjectIdx
                                            ON Commits(projectId)"""}

    def new(self, projectId, timestamp, troveName, troveVersion, userId):
        cu = self.db.cursor()
        cu.execute("INSERT INTO Commits VALUES (?, ?, ?, ?, ?)",
            projectId, timestamp, troveName, troveVersion, userId)
        self.db.commit()

    def getCommitsByProject(self, projectId, limit = 10):
        """ Returns a list of up to the limit (default 10) most recent commits.
        Each commit is represented by a 3-tuple (trove name, short trailing
        version string, full version string with timestamp. """
        commitList = []
        cu = self.db.cursor()
        like = "%:source"
        cu.execute("""SELECT troveName, version
                            FROM Commits
                            WHERE projectId = ? AND troveName LIKE ?
                            ORDER BY timestamp DESC LIMIT ?""", projectId, like, limit)
        for x in cu.fetchall():
            v = versions.VersionFromString(x[1])
            v.resetTimeStamps()
            commitList.append( (x[0], v.trailingRevision().asString(),
                v.freeze()) )
        return commitList
