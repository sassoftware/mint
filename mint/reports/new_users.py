#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#

import time

from mint.reports.mint_reports import MintReport

class NewUsersReport(MintReport):
    title = 'New users in the last 7 days'
    headers = ('Username', 'Full Name', 'Email', 'Time Created', 'Confirmed')

    def getData(self, reportTime = time.time()):
        cu = self.db.cursor()

        cu.execute("SELECT username, fullName, email, timeCreated, Confirmations.userId FROM Users LEFT JOIN Confirmations ON Users.userId=Confirmations.userId WHERE timeCreated > ?", reportTime - 604800)
        data = []
        for row in cu.fetchall():
            data.append([row[0], row[1] or '(none)', row[2], time.ctime(row[3]), not bool(row[4])])
        return data
