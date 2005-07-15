#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import database

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
