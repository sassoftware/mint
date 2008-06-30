#
# Copyright (c) 2005-2007 rPath, Inc.
# All Rights Reserved
#

import time

from mint import buildtypes
from mint.reports.mint_reports import MintReport

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

        # count projects with builds
        cu.execute("""SELECT COUNT(*) FROM
                          (SELECT DISTINCT projectId
                            FROM Builds
                            WHERE troveName IS NOT NULL)
                          AS ProjectBuilds""")
        data.append(('Projects with builds', cu.fetchone()[0]))

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

        # count the total number of non-rpath projects
        cu.execute("""SELECT COUNT(projectList)
                          FROM (SELECT Projects.projectId AS projectList,
                                       COUNT(userId) AS numUsers
                                    FROM Projects
                                    LEFT JOIN ProjectUsers
                                        ON ProjectUsers.projectId =
                                               Projects.projectId
                                    WHERE level IN (0, 1)
                                    AND userId NOT IN %s
                                    GROUP BY Projects.projectId) AS A
                          WHERE numUsers > 5""" % str(self.employeeIds))

        data.append(('Projects with 5 or more non-rPath users',
                     cu.fetchone()[0]))

        # spacer
        data.append(('',''))
        data.append(('Top Projects',' Users'))

        cu.execute("""select p.name, coalesce(pu.numUsers, 0) as numUsers
                      from Projects as p
                      left join (select projectId, count(userId) as numUsers
                          from ProjectUsers group by projectId) as pu
                          using (projectId)
                     order by numUsers desc, name
                     limit 5""")

        data.extend([(x[0], x[1]) for x in cu.fetchall()])

        # spacer
        data.append(('',''))
        cu.execute("""SELECT COUNT(*)
                          FROM UserData
                          WHERE name='insider' AND value = '1'""")
        data.append(('Number of opt-ins for insider tips and tricks',
                     cu.fetchone()[0]))

        cu.execute("""SELECT COUNT(*)
                          FROM UserData
                          WHERE name='insider' AND value = '0'""")
        data.append(('Number of opt-outs for insider tips and tricks',
                     cu.fetchone()[0]))

        cu.execute("""SELECT COUNT(*)
                          FROM UserData
                          WHERE name='newsletter' AND value = '1'""")
        data.append(('Number of opt-ins for monthly newsletter',
                     cu.fetchone()[0]))

        cu.execute("""SELECT COUNT(*)
                          FROM UserData
                          WHERE name='newsletter' AND value = '0'""")
        data.append(('Number of opt-outs for monthly newsletter',
                     cu.fetchone()[0]))

        return data
