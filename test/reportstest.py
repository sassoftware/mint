#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

import os
import shutil
import tempfile
import time

import fixtures
from mint.server import PermissionDenied

class ReportTest(fixtures.FixturedUnitTest):
    @fixtures.fixture("Full")
    def testReportList(self, db, data):
        client = self.getClient("admin")
        reports = client.server.listAvailableReports()
        for rep in reports.keys():
            client.server.getReport(rep)
        self.assertRaises(PermissionDenied, client.server.getReport, '')

    @fixtures.fixture("Full")
    def testReportPdf(self, db, data):
        client = self.getClient("admin")
        reportPdf = client.getReportPdf('new_users')
        if not reportPdf.startswith('%PDF-') or not reportPdf.endswith('%%EOF\r\n'):
            self.fail('resulting data format was not a PDF.')
        time.sleep(1)
        newReportPdf = client.getReportPdf('new_users')
        if reportPdf == newReportPdf:
            self.fail("Reports were not timestamped")

    @fixtures.fixture("Full")
    def testNewUsersReport(self, db, data):
        client = self.getClient("admin")
        for i in range(3):
            report = client.server.getReport('new_users')
            assert(len(report['data']) == i+5)
            client.registerNewUser("foouser%d" % i, "memberpass", "Test Member",
                                   "test@example.com", "test at example.com", "",
                                   active=False)

        client.registerNewUser("member", "memberpass", "Test Member",
                               "test@example.com", "test at example.com", "",
                               active=False)
        report = client.server.getReport('new_users')
        assert ([x[4] for x in report['data'] if x[0] == 'member'] \
                == [False]), "Confirmed column of new user report misfired"

    @fixtures.fixture("Full")
    def testNewProjectsReport(self, db, data):
        client = self.getClient("admin")
        report = client.server.getReport('new_projects')
        if report['data'][0][:3] != ['foo', 'Foo', 'owner']:
            self.fail("New Projects report returned incorrect data")

    @fixtures.fixture("Full")
    def testSiteSummary(self, db, data):
        client = self.getClient("admin")
        report = client.server.getReport('site_summary')

    @fixtures.fixture("Full")
    def testExecSummary(self, db, data):
        client = self.getClient("admin")
        report = client.server.getReport('exec_summary')

    @fixtures.fixture("Full")
    def testActiveUsersReport(self, db, data):
        adminClient = self.getClient("admin")
        userId = data['owner']
        adminId = data['admin']
        report = adminClient.server.getReport('active_users')
        self.failIf(report['data'] != [],
                    "active users report should have been empty")

        cu = db.cursor()
        cu.execute("INSERT INTO Commits (timestamp, userId) VALUES(?,?)",
                   time.time(), userId)
        cu.execute("INSERT INTO Commits (timestamp, userId) VALUES(?,?)",
                   time.time(), adminId)
        cu.execute("INSERT INTO Commits (timestamp, userId) VALUES(?,?)",
                   time.time(), adminId)

        db.commit()

        report = adminClient.server.getReport('active_users')

        self.failIf(report['data'] != \
                    [['admin', 'A User Named admin', 'admin@example.com', 2],
                     ['owner', 'A User Named owner', 'owner@example.com', 1]],
                    "user activity report wasn't properly computed")

    @fixtures.fixture("Full")
    def testPrecompiledReports(self, db, data):
        # compile a test report
        mintDir = os.path.sep.join(os.path.abspath(__file__).split(os.path.sep)[:-2])
        testDir = os.path.sep.join(os.path.abspath(__file__).split(os.path.sep)[:-1])
        reportScript = """
from mint.reports.mint_reports import MintReport

class RogueReport(MintReport):
    title = "Rogue report for testing. If this appears in mint.reports, delete it."
"""
        pyPath = os.path.join(testDir, "rogueReportForTesting.py") 
        pycPath = pyPath + "c"
        fh = os.open(pyPath, os.O_CREAT | os.O_WRONLY)
        os.write(fh, reportScript)
        os.close(fh)
        os.system("PYTHONPATH='%s' python -c 'import rogueReportForTesting'" % \
                mintDir)
        if os.path.exists(pycPath):
            os.unlink(pyPath)
            reportsPath = os.path.join(mintDir, 'mint', 'reports')
            rogueReport = os.path.join(reportsPath, 'rogueReportForTesting.pyc')
            shutil.move(pycPath, rogueReport)

            client = self.getClient("admin")
            try:
                from mint import reports
                reload(reports)
                reps = client.server.listAvailableReports()
                self.failIf('rogueReportForTesting' not in reps,
                            "precompiled report modules won't show up.")
            finally:
                try:
                    os.unlink(rogueReport)
                finally:
                    pass
                reload(reports)
            reps = client.server.listAvailableReports()
            self.failIf('rogueReportForTesting' in reps,
                        "rogue report module wasn't deleted after test.")
        else:
            os.unlink(pyPath)
            self.fail("problems compiling the script")


if __name__ == "__main__":
    testsuite.main()
