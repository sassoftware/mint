#
# Copyright 2005 rPath Inc.
# All Rights Reserved
#

import time
from reports import MintReport

class NewUsersReport(MintReport):
    title = 'New users in the last 7 days'
    headers = ('Username', 'Full Name', 'Email', 'Time Created')

    def getData(self, reportTime = time.time()):
        cu = self.db.cursor()

        cu.execute("SELECT username, fullName, email, timeCreated FROM Users WHERE timeCreated > ?", reportTime - 604800)
        data = []
        for row in cu.fetchall():
            data.append([row[0], row[1] or '(none)', row[2], time.ctime(row[3])])
        return data

if __name__ == "__main__":
    newUsers = NewUsersReport("sqldb", "new_users.pdf")
    newUsers.create()
