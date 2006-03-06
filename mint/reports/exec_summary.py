#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#

import time
from reports import MintReport
from mint import releasetypes

class ExecSummary(MintReport):
    title = 'Executive Summary'
    headers = ('Metric', 'Value')

    def getData(self, reportTime = time.time()):
        data = []

        cu = self.db.cursor()

        # count the site's active users
        cu.execute("SELECT COUNT(*) FROM Users WHERE active=1")
        numUsers = cu.fetchone()[0]
        data.append(('Confirmed users', numUsers))

        # count the users who accessed the site this week
        cu.execute("SELECT COUNT(*) FROM Users WHERE timeAccessed > ?",
                   reportTime - 604800)
        data.append(('Active users this week', cu.fetchone()[0]))

        # count the raw number of accounts created this week
        cu.execute("SELECT COUNT(*) FROM Users WHERE timeCreated > ?",
                   reportTime - 604800)
        data.append(('New users this week', cu.fetchone()[0]))

        # spacer
        data.append(('',''))

        # count total number of projects
        cu.execute("SELECT COUNT(*) FROM Projects")
        numProj = cu.fetchone()[0]
        data.append(('Total Projects', numProj))

        # count projects with releases
        cu.execute("""SELECT COUNT(*) FROM
                          (SELECT DISTINCT projectId
                            FROM Releases
                            WHERE troveName IS NOT NULL)
                          AS ProjectReleases""")
        data.append(('Projects with releases', cu.fetchone()[0]))

        # count projects with commits
        cu.execute("""SELECT COUNT(*) FROM
                          (SELECT DISTINCT projectId FROM Commits)
                          AS ProjectCommits""")
        data.append(('Projects with commits', cu.fetchone()[0]))

        # count projects with no users
        cu.execute("SELECT COUNT(*) FROM (SELECT DISTINCT projectId FROM ProjectUsers) AS DistinctProjects")
        data.append(('Orphaned Projects', numProj - cu.fetchone()[0]))

        # count projects with 5 or more users
        cu.execute("""SELECT COUNT(*) FROM
                              (SELECT DISTINCT projectId,
                                  COUNT(projectId) AS numUsers
                          FROM ProjectUsers
                          GROUP BY projectId) AS DistinctProjects
                          WHERE numUsers >= 5""")
        data.append(('Projects with 5 or more users', cu.fetchone()[0]))

        # spacer
        data.append(('',''))
        data.append(('Top Projects',' Users'))

        cu.execute("""SELECT Projects.name,
                             COUNT(Projects.projectId) AS numUsers
                          FROM ProjectUsers
                          LEFT JOIN Projects
                              ON ProjectUsers.projectId = Projects.projectId
                          GROUP BY Projects.projectId
                          ORDER BY numUsers DESC, name
                          LIMIT 5""")

        data.extend([(x[0], x[1]) for x in cu.fetchall()])

        return data
