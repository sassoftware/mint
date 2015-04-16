#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

from mint.lib import database


class CommitsTable(database.DatabaseTable):
    name = "Commits"
    fields = ['projectId', 'timestamp', 'troveName', 'version', 'userId']

    def new(self, projectId, timestamp, troveName, troveVersion, userId):
        cu = self.db.cursor()
        cu.execute("INSERT INTO Commits VALUES (?, ?, ?, ?, ?)",
            projectId, timestamp, troveName, troveVersion, userId)
        self.db.commit()
