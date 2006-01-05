#
# Copyright (c) 2005 rPath, Inc.
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
        cu = self.db.cursor()

        like = "%:source"
        cu.execute("""SELECT troveName, version 
                            FROM Commits 
                            WHERE projectId = ? AND troveName LIKE ?
                            ORDER BY timestamp DESC LIMIT ?""", projectId, like, limit)
        return [(x[0], versions.VersionFromString(x[1]).trailingRevision().asString()) for x in cu.fetchall()]
