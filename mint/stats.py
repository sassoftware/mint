#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import database
import versions

class CommitsTable(database.DatabaseTable):
    name = "Commits"
    fields = ['projectId', 'timestamp', 'troveName', 'version', 'userId']

    createSQL = """
        CREATE TABLE Commits (
            projectId   INT,
            timestamp   INT,
            troveName   STR,
            version     STR,
            userId      INT
        );"""

    def new(self, projectId, timestamp, troveName, troveVersion, userId):
        cu = self.db.cursor()

        cu.execute("INSERT INTO Commits VALUES (?, ?, ?, ?, ?)",
            projectId, timestamp, troveName, troveVersion, userId)
        self.db.commit()

    def getCommitsByProject(self, projectId, limit = 10):
        cu = self.db.cursor()

        r = cu.execute("""SELECT troveName, version 
                            FROM Commits 
                            WHERE projectId = ? 
                                    AND troveName like '%:source' 
                            ORDER BY timestamp DESC LIMIT ?""", (projectId, limit))
        return [(x[0], versions.VersionFromString(x[1]).trailingRevision().asString()) for x in r.fetchall()]
