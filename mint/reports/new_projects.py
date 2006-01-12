#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#

import time
from reports import MintReport

class NewProjectsReport(MintReport):
    title = 'New projects in the last 7 days'
    headers = ('Project Title', 'Project Name', 'Creator', 'Time Created')

    def getData(self, reportTime = time.time()):
        cu = self.db.cursor()

        cu.execute("SELECT hostname, name, username, Projects.timeCreated FROM Projects LEFT JOIN Users ON Users.userId = Projects.creatorId WHERE Projects.timeCreated > ?", reportTime - 604800)
        data = []
        for row in cu.fetchall():
            data.append([row[0], row[1] or '(none)', row[2], time.ctime(row[3])])
        return data
