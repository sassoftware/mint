#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#

import time
from reports import MintReport

class ActiveUsersReport(MintReport):
    title = 'Active users in the last 30 days'
    headers = ('Username', 'Full Name', 'Email', 'Commits')

    def getData(self, reportTime = time.time()):
        cu = self.db.cursor()

        cu.execute("""SELECT username, fullName, email,
                             COUNT(Commits.userId) AS commits
                          FROM Users
                          LEFT JOIN Commits ON Users.userId=Commits.userId
                          WHERE Commits.timestamp > ?
                          GROUP BY username ORDER BY commits DESC""",
                   reportTime - 2592000)
        data = []
        for row in cu.fetchall():
            data.append([row[0], row[1] or '(none)', row[2], row[3]])
        return data
