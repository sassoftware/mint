#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import testsuite
testsuite.setup()

import time
from mint_rephelp import MintRepositoryHelper
from mint.mint_server import PermissionDenied

class ReportTest(MintRepositoryHelper):
    def testReportList(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        reports = client.server.listAvailableReports()
        for rep in reports.keys():
            client.server.getReport(rep)
        self.assertRaises(PermissionDenied, client.server.getReport, '')

    def testReportPdf(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        reportPdf = client.server.getReportPdf('new_users')
        if not reportPdf.startswith('%PDF-'):
            self.fail('resulting data format was not a PDF.')
        time.sleep(1)
        newReportPdf = client.server.getReportPdf('new_users')
        if reportPdf == newReportPdf:
            self.fail("Reports were not timestamped")

    def testNewUsersReport(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        for i in range(3):
            report = client.server.getReport('new_users')
            assert(len(report['data']) == i+1)
            self.quickMintUser('foouser%d' % i, 'foopass')
        client.registerNewUser("member", "memberpass", "Test Member",
                               "test@example.com", "test at example.com", "",
                               active=False)
        report = client.server.getReport('new_users')
        assert ([x[4] for x in report['data'] if x[0] == 'member'] \
                == [False]), "Confirmed column of new user report misfired"

    def testNewProjectsReport(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        projectId = client.newProject('Foo Project', 'foo', 'rpath.local')
        report = client.server.getReport('new_projects')
        if report['data'][0][:3] != ['foo', 'Foo Project', 'adminuser']:
            self.fail("New Projects report returned incorrect data")

    def testSiteSummary(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        projectId = client.newProject('Foo Project', 'foo', 'rpath.local')
        self.quickMintUser('foouser', 'foopass')
        report = client.server.getReport('site_summary')

    def testActiveUsersReport(self):
        adminClient, adminId = self.quickMintAdmin('adminuser', 'adminpass')
        projectId = adminClient.newProject('Foo Project', 'foo', 'rpath.local')
        client, userId = self.quickMintUser('foouser', 'foopass')
        report = adminClient.server.getReport('active_users')
        self.failIf(report['data'] != [],
                    "active users report should have been empty")

        cu = self.db.cursor()
        cu.execute("INSERT INTO Commits (timestamp, userId) VALUES(?,?)",
                   time.time(), userId)
        cu.execute("INSERT INTO Commits (timestamp, userId) VALUES(?,?)",
                   time.time(), adminId)
        cu.execute("INSERT INTO Commits (timestamp, userId) VALUES(?,?)",
                   time.time(), adminId)

        self.db.commit()

        report = adminClient.server.getReport('active_users')

        self.failIf(report['data'] != \
                    [['adminuser', 'Test User', 'test@example.com', 2],
                     ['foouser', 'Test User', 'test@example.com', 1]],
                    "user activity report wasn't properly computed")

if __name__ == "__main__":
    testsuite.main()
