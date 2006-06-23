#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#

import time

from mint.reports.mint_reports import MintReport

class NewUsersReport(MintReport):
    title = 'Users wishing to recieve Insider Information'
    headers = ('Username', 'Full Name', 'Email')

    def getData(self, reportTime = time.time()):
        cu = self.db.cursor()

        cu.execute("SELECT username, fullName, email FROM Users LEFT JOIN UserData ON UserData.userId=Users.userId WHERE name='insider' AND value=1")
        data = []
        for row in cu.fetchall():
            data.append([row[0], row[1] or '(none)', row[2]])
        return data
