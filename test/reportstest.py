#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint.mint_server import PermissionDenied

class ProjectTest(MintRepositoryHelper):
    def testReportList(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        reports = client.server.listAvailableReports()
        for rep in reports.keys():
            client.server.getReport(rep)

        try:
            client.server.getReport('')
            self.fail("Illegal report request didn't fail")
        except PermissionDenied:
            pass

    def testReportPdf(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        reportPdf = client.server.getReportPdf('new_users')
        if not reportPdf.startswith('%PDF-'):
            self.fail('resulting data format was not a PDF.')

    def testNewUserReport(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        for i in range(3):
            report = client.server.getReport('new_users')
            assert(len(report['data']) == i+1)
            self.quickMintUser('foouser%d' % i, 'foopass')

if __name__ == "__main__":
    testsuite.main()
