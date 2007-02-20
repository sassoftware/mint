#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_DOMAIN, MINT_PROJECT_DOMAIN

from mint import database
from mint import server
from mint import users
from mint.projects import LabelMissing
from mint import mint_error

import fixtures

class LabelsTest(fixtures.FixturedUnitTest):
    @testsuite.context("quick")
    @fixtures.fixture("Full")
    def testBasicAttributes(self, db, data):
        adminClient = self.getClient("admin")
        project = adminClient.getProject(data['projectId'])

        newLabelId = project.addLabel("bar.%s@rpl:devel" % MINT_PROJECT_DOMAIN,
            "http://%s/repos/bar/" % MINT_PROJECT_DOMAIN, "user1", "pass1")

        assert(project.getLabelIdMap() ==\
            {'bar.%s@rpl:devel' % MINT_PROJECT_DOMAIN: newLabelId,
             'foo.%s@rpl:devel' % MINT_PROJECT_DOMAIN: 1})

        project.editLabel(newLabelId, "bar.%s@rpl:testbranch" % MINT_PROJECT_DOMAIN,
            "http://bar.%s/conary/" % MINT_PROJECT_DOMAIN, "user1", "pass1")
        assert adminClient.server.getLabel(newLabelId) == \
            ('bar.%s@rpl:testbranch' % MINT_PROJECT_DOMAIN,
             'http://bar.%s/conary/' % MINT_PROJECT_DOMAIN,
             'user1', 'pass1')

        project.removeLabel(newLabelId)
        assert(project.getLabelIdMap() ==\
            {"foo.%s@rpl:devel" % MINT_PROJECT_DOMAIN: 1})

        try:
            adminClient.server.getLabel(newLabelId)
            self.fail("label should not exist")
        except LabelMissing:
            pass

    @fixtures.fixture("Full")
    def testSSL(self, db, data):
        adminClient = self.getClient("admin")
        project = adminClient.getProject(data['projectId'])

        ccfg = project.getConaryConfig()
        if adminClient.server._server.cfg.SSL:
            assert(ccfg.repositoryMap.values()[0].startswith("https://"))
        else:
            assert(ccfg.repositoryMap.values()[0].startswith("http://"))

        extProjectId = adminClient.newProject("External Project", "external",
                "localhost")

        cu = db.cursor()
        cu.execute("UPDATE Projects SET external=1 WHERE projectId=?",
                extProjectId)
        db.commit()

        extProject = adminClient.getProject(extProjectId)
        ccfg = extProject.getConaryConfig()
        assert(ccfg.repositoryMap.values()[0].startswith("http://"))

    @fixtures.fixture("Full")
    def testInboundMirrors(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        targetLabel = project.getLabel()
        mirrorId = adminClient.addInboundMirror(projectId, [targetLabel],
                "http://www.example.com/conary/",
                "mirror", "mirrorpass")

        labels = adminClient.getInboundMirrors()
        self.failUnlessEqual(labels,
                [[1, projectId, targetLabel, 'http://www.example.com/conary/',
                  'mirror', 'mirrorpass']])

        # test delete
        adminClient.delInboundMirror(mirrorId)
        labels = adminClient.getInboundMirrors()
        self.failUnlessEqual(labels, [])

    @fixtures.fixture("Full")
    def testOutboundMirror(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        adminClient.addOutboundMirror(projectId, [sourceLabel],
                "http://www.example.com/conary/",
                "mirror", "mirrorpass")

        labels = adminClient.getOutboundMirrors()
        assert(labels ==
                [[1, projectId, sourceLabel, 'http://www.example.com/conary/',
                  'mirror', 'mirrorpass', False, False, []]])

        adminClient.delOutboundMirror(1)
        labels = adminClient.getOutboundMirrors()
        assert(labels == [])

    @fixtures.fixture("Full")
    def testOutboundMirrorAllLabels(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        adminClient.addOutboundMirror(projectId, [sourceLabel],
                "http://www.example.com/conary/",
                "mirror", "mirrorpass")

        assert(adminClient.getOutboundMirrors()[0][6] is False)
        cu = db.cursor()
        cu.execute("UPDATE OutboundMirrors SET allLabels = 1")
        db.commit()
        assert(adminClient.getOutboundMirrors()[0][6] is True)

        cu.execute("DELETE FROM OutboundMirrors")
        db.commit()

        adminClient.addOutboundMirror(projectId, [sourceLabel],
                "http://www.example.com/conary/",
                "mirror", "mirrorpass", allLabels = True)
        assert(adminClient.getOutboundMirrors()[0][6] is True)

    @fixtures.fixture("Full")
    def testOutboundMirrorRecurse(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        adminClient.addOutboundMirror(projectId, [sourceLabel],
                "http://www.example.com/conary/",
                "mirror", "mirrorpass")
        assert(adminClient.getOutboundMirrors()[0][7] is False)
        cu = db.cursor()
        cu.execute("UPDATE OutboundMirrors SET recurse = 1")
        db.commit()
        assert(adminClient.getOutboundMirrors()[0][7] is True)

        cu.execute("DELETE FROM OutboundMirrors")
        db.commit()

        adminClient.addOutboundMirror(projectId, [sourceLabel],
                "http://www.example.com/conary/",
                "mirror", "mirrorpass", recurse = True)
        assert(adminClient.getOutboundMirrors()[0][7] is True)

    @fixtures.fixture("Full")
    def testOutboundMatchInitial(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        adminClient.addOutboundMirror(projectId, [sourceLabel],
                "http://www.example.com/conary/",
                "mirror", "mirrorpass")

        # ensure this doesn't raise ItemNotFound
        self.failUnlessEqual(adminClient.getOutboundMirrorMatchTroves(1), [],
                    "Listing empty matchTroves failed")

        # however, this should raise
        self.assertRaises(database.ItemNotFound, adminClient.getOutboundMirrorMatchTroves, 2)

    @fixtures.fixture("Full")
    def testOutboundMatchBasic(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        adminClient.addOutboundMirror(projectId, [sourceLabel],
                "http://www.example.com/conary/",
                "mirror", "mirrorpass")

        adminClient.setOutboundMirrorMatchTroves(1, ["-.*:source$"])
        self.failUnlessEqual(adminClient.getOutboundMirrorMatchTroves(1),
                ["-.*:source$"])

    @fixtures.fixture("Full")
    def testOutboundMatchComposite(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        adminClient.addOutboundMirror(projectId, [sourceLabel],
                "http://www.example.com/conary/",
                "mirror", "mirrorpass")

        adminClient.setOutboundMirrorMatchTroves(1, ['-.*:source$', '-.*:debuginfo$'])
        self.failUnlessEqual(adminClient.getOutboundMirrorMatchTroves(1),
               ['-.*:source$', '-.*:debuginfo$'])

    @fixtures.fixture("Full")
    def testOutboundMatchReordered(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        adminClient.addOutboundMirror(projectId, [sourceLabel],
                "http://www.example.com/conary/",
                "mirror", "mirrorpass")

        adminClient.setOutboundMirrorMatchTroves(1,
                                           ['-.*:source$', '-.*:debuginfo$'])
        assert(adminClient.getOutboundMirrorMatchTroves(1) == \
               ['-.*:source$', '-.*:debuginfo$'])

        adminClient.setOutboundMirrorMatchTroves(1,
                                           ['-.*:debuginfo$', '-.*:source$' ])
        assert(adminClient.getOutboundMirrorMatchTroves(1) == \
               ['-.*:debuginfo$', '-.*:source$'])


    @fixtures.fixture("Full")
    def testOutboundMatchParams(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        adminClient.addOutboundMirror(projectId, [sourceLabel],
                "http://www.example.com/conary/",
                "mirror", "mirrorpass")

        self.assertRaises(mint_error.ParameterError,
                          adminClient.setOutboundMirrorMatchTroves,
                          1, 'wrong')

        self.assertRaises(mint_error.ParameterError,
                          adminClient.setOutboundMirrorMatchTroves,
                          1, ['also_wrong'])

        for matchStr in ('+right', '-right'):
            # ensure no error is raised for properly formed params
            adminClient.setOutboundMirrorMatchTroves(1, [matchStr])


if __name__ == "__main__":
    testsuite.main()
