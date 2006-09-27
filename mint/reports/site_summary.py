#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#

import time

from mint import buildtypes
from mint.reports.mint_reports import MintReport

class SiteSummary(MintReport):
    title = 'Site Summary'
    headers = ('Metric', 'Answer')

    def getData(self, reportTime = time.time()):
        data = []

        cu = self.db.cursor()

        # count the site's total users
        cu.execute("SELECT COUNT(*) FROM Users")
        data.append(('Total users', cu.fetchone()[0]))

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

        # count users with no projects
        cu.execute("""SELECT COUNT(*) FROM
                          (SELECT DISTINCT userId FROM ProjectUsers)
                           AS DistinctUsers""")
        numProjUsers = cu.fetchone()[0]
        data.append(('Users with no projects', numUsers - numProjUsers))

        # count users with exactly n projects
        for i in range(1, 5):
            cu.execute("""SELECT COUNT(*) FROM
                          (SELECT DISTINCT userId,
                                      COUNT(userId) AS projectCount
                           FROM ProjectUsers GROUP BY userId) AS DistinctUsers
                           WHERE projectCount = ?""", i)
            if i == 1:
                data.append(('Users with 1 project', cu.fetchone()[0]))
            else:
                data.append(('Users with %d projects' % i, cu.fetchone()[0]))

        cu.execute("""SELECT COUNT(*) FROM
                          (SELECT DISTINCT userId,
                                      COUNT(userId) AS ProjectCount
                           FROM ProjectUsers GROUP BY userId) AS DistinctUsers
                           WHERE ProjectCount >= 5""")
        data.append(('Users with 5 or more projects', cu.fetchone()[0]))

        # count unconfirmed users older than a week
        cu.execute("SELECT COUNT(*) FROM Confirmations WHERE timeRequested<?",
                   reportTime - 604800)
        data.append(('Unconfirmed users older than a week', cu.fetchone()[0]))

        # spacer
        data.append(('',''))

        # count total number of projects
        cu.execute("SELECT COUNT(*) FROM Projects")
        numProj = cu.fetchone()[0]
        data.append(('Total Projects', numProj))

        # count new projects this week
        cu.execute("SELECT COUNT(*) FROM Projects WHERE timeCreated > ?",
                   reportTime - 604800)
        data.append(('New Projects this week', cu.fetchone()[0]))

        # count projects with builds
        cu.execute("""SELECT COUNT(*) FROM
                          (SELECT DISTINCT projectId
                            FROM Builds
                            WHERE troveName IS NOT NULL)
                          AS ProjectBuilds""")
        data.append(('Projects with builds', cu.fetchone()[0]))

        # count projects with builds this week
        cu.execute("""SELECT COUNT(*) FROM
                          (SELECT DISTINCT projectId FROM Builds
                              WHERE timeCreated > ?)
                          AS ProjectBuilds""",
                   reportTime - 604800)
        data.append(('Projects with new builds this week', cu.fetchone()[0]))

        # count projects with public (published) published releases
        cu.execute("""SELECT COUNT(*) FROM
                          (SELECT DISTINCT projectId
                            FROM PublishedReleases
                            WHERE timePublished IS NOT NULL)
                          AS PublicPublishedReleases""")
        data.append(('Projects with published releases', cu.fetchone()[0]))

        # count projects with public (published) published releases this week
        cu.execute("""SELECT COUNT(*) FROM
                          (SELECT DISTINCT projectId
                            FROM PublishedReleases
                            WHERE timePublished > ?)
                          AS PublicPublishedReleases""",
                   reportTime - 604800)
        data.append(('Projects with new published releases this week', cu.fetchone()[0]))

        # count projects with commits
        cu.execute("""SELECT COUNT(*) FROM
                          (SELECT DISTINCT projectId FROM Commits)
                          AS ProjectCommits""")
        data.append(('Projects with commits', cu.fetchone()[0]))

        # count projects with commits this week
        cu.execute("""SELECT COUNT(*) FROM
                          (SELECT DISTINCT projectId FROM Commits
                              WHERE timestamp > ?)
                          AS ProjectCommits""",
                   reportTime - 604800)
        data.append(('Projects with commits this week', cu.fetchone()[0]))

        # count projects with no users
        cu.execute("SELECT COUNT(*) FROM (SELECT DISTINCT projectId FROM ProjectUsers) AS DistinctProjects")
        data.append(('Orphaned Projects', numProj - cu.fetchone()[0]))

        # count proejcts with n users
        for i in range(1, 5):
            cu.execute("""SELECT COUNT(*) FROM
                              (SELECT DISTINCT projectId,
                                  COUNT(projectId) AS numUsers
                          FROM ProjectUsers
                          GROUP BY projectId) AS DistinctProjects
                          WHERE numUsers = ?""", i)
            if i == 1:
                data.append(('Projects with 1 user', cu.fetchone()[0]))
            else:
                data.append(('Projects with %d users' % i, cu.fetchone()[0]))

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

        countedBuilds = (buildtypes.INSTALLABLE_ISO,
                         buildtypes.RAW_HD_IMAGE,
                         buildtypes.RAW_FS_IMAGE,
                         buildtypes.TARBALL,
                         buildtypes.LIVE_ISO,
                         buildtypes.VMWARE_IMAGE)

        # count the total builds
        cu.execute("""SELECT COUNT(*) FROM Builds
                          WHERE buildType IN %s""" % str(countedBuilds))

        data.append(('Images Present', cu.fetchone()[0]))

        # count builds for each image type
        for buildType in countedBuilds:
            cu.execute("""SELECT COUNT(*) FROM Builds
                              WHERE buildType=?""",
                       buildType)
            data.append((buildtypes.typeNames[buildType],
                         cu.fetchone()[0]))

        # spacer
        data.append(('',''))
        # count the total builds this week
        cu.execute("""SELECT COUNT(*) FROM Builds
                          WHERE buildType IN %s AND timeCreated > ?""" % \
                   str(countedBuilds), reportTime - 604800)
        data.append(('Images Built This Week', cu.fetchone()[0]))

        # count builds for each image type per this week
        for buildType in countedBuilds:
            cu.execute("""SELECT COUNT(*) FROM Builds
                              WHERE buildType=? AND timeCreated > ?""",
                       buildType, reportTime - 604800)
            data.append((buildtypes.typeNames[buildType] + " This Week",
                         cu.fetchone()[0]))

        # spacer
        data.append(('',''))

        # count group-builder source commits
        cu.execute("""SELECT COUNT(*) FROM Commits
                          WHERE troveName LIKE '%:source' AND userId=0""")
        data.append(('Group Builder commits', cu.fetchone()[0]))

        # count non-group-builder source commits
        cu.execute("""SELECT COUNT(*) FROM Commits
                          WHERE troveName LIKE '%:source' AND userId<>0""")
        data.append(('Command line commits', cu.fetchone()[0]))

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
