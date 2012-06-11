#!/usr/bin/python
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import testsuite
testsuite.setup()

import os
import shutil
import tempfile
import time

import fixtures
from mint import reports as mintreports
from mint.lib import maillib
from mint.mint_error import PermissionDenied
from mint.mint_error import InvalidReport
from testutils import mock

def needs_reportlab(func):
    if mintreports._reportlab_present:
        return func
    def fails(*args):
        raise testsuite.SkipTestException("reportlab not installed")
    fails.__name__ = func.__name__
    fails.__dict__.update(func.__dict__)
    return fails

class ReportTest(fixtures.FixturedUnitTest):
    @fixtures.fixture("Full")
    def testReportList(self, db, data):
        client = self.getClient("admin")
        reports = client.server.listAvailableReports()
        for rep in reports.keys():
            client.server.getReport(rep)
        self.assertRaises(InvalidReport, client.server.getReport, '')

    @fixtures.fixture("Full")
    @needs_reportlab
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
    @needs_reportlab
    def testNewUsersReport(self, db, data):
        mock.mock(maillib, 'sendMailWithChecks')
        self.cfg.sendNotificationEmails = True
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
    @needs_reportlab
    def testNewProjectsReport(self, db, data):
        client = self.getClient("admin")
        report = client.server.getReport('new_projects')
        if report['data'][0][:3] != ['foo', 'Foo', 'owner']:
            self.fail("New Projects report returned incorrect data")

    @fixtures.fixture("Full")
    @needs_reportlab
    def testSiteSummary(self, db, data):
        client = self.getClient("admin")
        report = client.server.getReport('site_summary')

    @fixtures.fixture("Full")
    @needs_reportlab
    def testExecSummary(self, db, data):
        client = self.getClient("admin")
        report = client.server.getReport('exec_summary')

    @fixtures.fixture("Full")
    @needs_reportlab
    def testNewsletterReport(self, db, data):
        adminClient = self.getClient("admin")
        report = adminClient.server.getReport('newsletter_users')
        assert report['data'] == [], 'bad initial state'
        client = self.getClient('owner')
        user = client.getUser(data['owner'])
        user.setDataValue('newsletter', True)
        report = adminClient.server.getReport('newsletter_users')
        self.failIf(report['data'] != \
                    [['owner', 'A User Named owner', 'owner@example.com']],
                    "newletter opt-in not reflected in report")

    @fixtures.fixture("Full")
    @needs_reportlab
    def testInsiderReport(self, db, data):
        adminClient = self.getClient("admin")
        report = adminClient.server.getReport('insider_users')
        assert report['data'] == [], 'bad initial state'
        client = self.getClient('owner')
        user = client.getUser(data['owner'])
        user.setDataValue('insider', True)
        report = adminClient.server.getReport('insider_users')
        self.failIf(report['data'] != \
                    [['owner', 'A User Named owner', 'owner@example.com']],
                    "insider opt-in not reflected in report")

    @fixtures.fixture("Full")
    @needs_reportlab
    def testActiveUsersReport(self, db, data):
        adminClient = self.getClient("admin")
        projectId = data['projectId']
        userId = data['owner']
        adminId = data['admin']
        report = adminClient.server.getReport('active_users')
        self.failUnlessEqual(report['data'], [])

        cu = db.cursor()
        for id_ in (userId, adminId, adminId):
            cu.execute("INSERT INTO Commits (projectId, timestamp, userId) "
                    "VALUES(?, ?,?)", projectId, time.time(), id_)
        db.commit()

        report = adminClient.server.getReport('active_users')

        self.failUnlessEqual(sorted(report['data']),
                    [['admin', 'A User Named admin', 'admin@example.com', 2],
                     ['owner', 'A User Named owner', 'owner@example.com', 1]])

    @fixtures.fixture('Full')
    def testGetRepObj(self, db, data):
        client = self.getClient('admin')

        self.assertRaises(InvalidReport,
                          client.server._server._getReportObject,
                          'not_a_valid_report')

    @fixtures.fixture('Full')
    def testListReportPerms(self, db, data):
        client = self.getClient('nobody')
        self.assertRaises(PermissionDenied, client.listAvailableReports)

    @fixtures.fixture('Full')
    def testReportDataPerms(self, db, data):
        client = self.getClient('nobody')
        self.assertRaises(PermissionDenied, client.getReport, 'new_users')

    @fixtures.fixture('Full')
    def testReportPdfPerms(self, db, data):
        client = self.getClient('nobody')
        self.assertRaises(PermissionDenied, client.getReportPdf, 'new_users')

    @fixtures.fixture("Full")
    def testPrecompiledReports(self, db, data):
        raise testsuite.SkipTestException('Modifying the codebase is not a valid test')
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
