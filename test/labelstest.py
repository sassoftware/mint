#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_DOMAIN, MINT_PROJECT_DOMAIN
from mint import mint_server
from mint import users
from mint.projects import LabelMissing
from mint import database

class LabelsTest(MintRepositoryHelper):
    def testBasicAttributes(self):
        client, userId = self.quickMintUser("testuser", "testpass")

        projectId = client.newProject("Foo", "foo", "rpath.org")
        project = client.getProject(projectId)

        newLabelId = project.addLabel("bar.rpath.org@rpl:devel",
            "http://rpath.org/repos/bar/", "user1", "pass1")

        assert(project.getLabelIdMap() ==\
            {'bar.rpath.org@rpl:devel': newLabelId,
             'foo.rpath.org@rpl:devel': 1})

        project.editLabel(newLabelId, "bar.rpath.org@rpl:testbranch",
            "http://bar.rpath.org/conary/", "user1", "pass1")
        assert client.server.getLabel(newLabelId) == ('bar.rpath.org@rpl:testbranch', 'http://bar.rpath.org/conary/', 'user1', 'pass1')

        project.removeLabel(newLabelId)
        assert(project.getLabelIdMap() ==\
            {"foo.rpath.org@rpl:devel": 1})

        try:
            client.server.getLabel(newLabelId)
            self.fail("label should not exist")
        except LabelMissing:
            pass

    def testSSL(self):
        client, userId = self.quickMintUser("testuser", "testpass")

        projectId = client.newProject("Test Project", "test", "localhost")
        project = client.getProject(projectId)

        ccfg = project.getConaryConfig()
        if self.mintCfg.SSL:
            assert(ccfg.repositoryMap.values()[0].startswith("https://"))
        else:
            assert(ccfg.repositoryMap.values()[0].startswith("http://"))

        extProjectId = client.newProject("External Project", "external",
                "localhost")

        cu = self.db.cursor()
        cu.execute("UPDATE Projects SET external=1 WHERE projectId=?",
                extProjectId)
        self.db.commit()

        extProject = client.getProject(extProjectId)
        ccfg = extProject.getConaryConfig()
        assert(ccfg.repositoryMap.values()[0].startswith("http://"))


    def testExternalVersions(self):
        def addLabel(projectId, label, url = 'http://none'):
            cu.execute("""INSERT INTO Labels
                              (projectId, label, url, username, password)
                              VALUES(?, ?, ?, 'none', 'none')""",
                       projectId, label, url)

        client, userId = self.quickMintUser("testuser", "testpass")
        client2, userId = self.quickMintUser("foouser", "foopass")

        projectId = client.newProject("Test Project", "test", "localhost")
        project = client.getProject(projectId)

        projectId2 = client.newProject("Foo Project", "foo", "localhost")
        project = client.getProject(projectId2)

        cu = self.db.cursor()

        cu.execute("UPDATE Projects SET external=1 WHERE projectId=?",
                   projectId2)

        addLabel(projectId, '/foo.rpath.org@rpl:devel')
        addLabel(projectId, '/bar.rpath.org@rpl:devel')
        addLabel(projectId2, '/baz.rpath.org@rpl:devel')
        addLabel(projectId, '/foo.rpath.org@diff:label')
        self.db.commit()

        # a local project returns False
        self.failIf(client.versionIsExternal( \
            '/foo.rpath.org@rpl:devel//1/1.0.0-1-0.1'),
                    "internal version appeared external")

        # an external project returns True
        self.failIf(not client.versionIsExternal( \
            '/baz.rpath.org@rpl:devel//1/1.0.0-1-0.1'),
                    "external version appeared internal")

        # missing item raises ItemNotFound
        # FIXME: re-enable once versionIsExternal raises an exception
        #self.assertRaises(database.ItemNotFound, client.versionIsExternal,
        #                  '/just.not.there@rpl:devel//1/1.0.0-1-0.1')


        cu.execute("UPDATE Projects SET hidden=1 WHERE projectId=?",
                   projectId2)

        # legal reference to local hidden project returns False
        self.failIf(client.versionIsExternal( \
            '/foo.rpath.org@rpl:devel//1/1.0.0-1-0.1'),
                    "internal version appeared external")

        # illegal reference to local hidden project raises ItemNotFound
        # FIXME: re-enable once versionIsExternal raises an exception
        #self.assertRaises(database.ItemNotFound, client2.versionIsExternal,
        #                  '/just.not.there@rpl:devel//1/1.0.0-1-0.1')

    def testInboundLabel(self):
        client, userId = self.quickMintAdmin("testuser", "testpass")
        client.addInboundLabel(0, 0, "http://www.example.com/conary/",
                               "mirror", "mirrorpass")

        labels = client.getInboundLabels()
        assert(labels == [[0, 0, 'http://www.example.com/conary/',
                           'mirror', 'mirrorpass']])

    def testOutboundLabel(self):
        client, userId = self.quickMintAdmin("testuser", "testpass")
        client.addOutboundLabel(0, 0, "http://www.example.com/conary/",
                                "mirror", "mirrorpass")

        labels = client.getOutboundLabels()
        assert(labels == [[0, 0, 'http://www.example.com/conary/',
                           'mirror', 'mirrorpass']])

        client.delOutboundLabel(0, 'http://www.example.com/conary/')
        labels = client.getOutboundLabels()
        assert(labels == [])


if __name__ == "__main__":
    testsuite.main()
