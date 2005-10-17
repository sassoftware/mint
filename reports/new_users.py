#
# Copyright 2005 rPath Inc.
# All Rights Reserved
#

import time
from reports import MintReport

class NewUsersReport(MintReport):
    title = 'New users in the last 7 days'
    headers = ('Username', 'Full Name', 'Email', 'Time Created')

    def getData(self):
        cu = self.db.cursor()

        cu.execute(""""SELECT username, fullName, email, timeCreated
                        FROM Users 
                        WHERE timeCreated > ?""", time.time() - 604800)
        data = []
        for r in cu.fetchall():
            data.append( (r[0], r[1] and r[1] or "(none)", r[2], time.ctime(r[3])) )
        return data

if __name__ == "__main__":
    newUsers = NewUsersReport("sqldb", "new_users.pdf")
    newUsers.create()
