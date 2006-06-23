#!/usr/bin/python2.4
#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import testsuite
testsuite.setup()

import mint_rephelp
from mint_rephelp import MINT_PROJECT_DOMAIN

from repostest import testRecipe
from conary import versions

testDirRecipe = """
class TestCase(PackageRecipe):
    name = "testcase"
    version = "1.0"

    def setup(r):
        r.Create("/temp/foo")
        r.MakeDirs("/temp/directory", mode = 0775)
"""


class WebProjectTest(mint_rephelp.WebRepositoryHelper):
    def testConaryCfg(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        #Anonymous
        page = self.assertContent('/project/testproject/conaryUserCfg',
                                  code=[200],
                                  content='Which option should I choose?',
                                  server=self.getProjectServerHostname())
        page = self.assertContent('/project/testproject/conaryDevelCfg',
                        code=[200],
                        content='Build Label: <strong><tt>%s</tt></strong>' %\
                                 self.cfg.buildLabel.asString(),
                        server=self.getProjectServerHostname())

        #User
        self.webLogin('testuser', 'testpass')
        page = self.assertContent('/project/testproject/conaryUserCfg',
                                  code=[200],
                                  content='Which option should I choose?',
                                  server=self.getProjectServerHostname())
        page = self.assertContent('/project/testproject/conaryDevelCfg',
                        code=[200],
                        content='Build Label: <strong><tt>%s</tt></strong>' %\
                                 self.cfg.buildLabel.asString(),
                        server=self.getProjectServerHostname())

if __name__ == "__main__":
    testsuite.main()
