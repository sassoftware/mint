#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MINT_DOMAIN, MINT_PROJECT_DOMAIN, PFQDN

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
            "http://bar.%s/conary/" % MINT_PROJECT_DOMAIN, "userpass",
            "user1", "pass1", "")
        assert adminClient.server.getLabel(newLabelId) == \
            dict(   label='bar.%s@rpl:testbranch' % MINT_PROJECT_DOMAIN,
                    url='http://bar.%s/conary/' % MINT_PROJECT_DOMAIN,
                    authType='userpass',
                    username='user1',
                    password='pass1',
                    entitlement='',
                    )

        project.removeLabel(newLabelId)
        assert(project.getLabelIdMap() ==\
            {"foo.%s@rpl:devel" % MINT_PROJECT_DOMAIN: 1})

        try:
            adminClient.server.getLabel(newLabelId)
            self.fail("label should not exist")
        except LabelMissing:
            pass

    @fixtures.fixture("Full")
    def testFullRepositoryMap(self, db, data):
        adminClient = self.getClient("admin")
        project = adminClient.getProject(data['projectId'])

        x = adminClient.getFullRepositoryMap()
        self.failUnlessEqual({'foo.%s' % MINT_PROJECT_DOMAIN: 'http://%s/repos/foo/' % PFQDN}, x)

        labelId = project.getLabelIdMap().values()[0]
        project.editLabel(labelId, "foo.%s@rpl:testbranch" % MINT_PROJECT_DOMAIN,
            "http://bar.%s/conary/" % MINT_PROJECT_DOMAIN, "userpass",
            "user1", "pass1", "")

        x = adminClient.getFullRepositoryMap()
        self.failUnlessEqual({'foo.%s' % MINT_PROJECT_DOMAIN: 'http://bar.%s/conary/' % MINT_PROJECT_DOMAIN}, x)

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
                "http://www.example.com/conary/", "userpass",
                "mirror", "mirrorpass", "")

        labels = adminClient.getInboundMirrors()
        self.failUnlessEqual(labels,
                [[1, projectId, targetLabel, 'http://www.example.com/conary/',
                  'userpass', 'mirror', 'mirrorpass', '', 0]])

        # test delete
        adminClient.delInboundMirror(mirrorId)
        labels = adminClient.getInboundMirrors()
        self.failUnlessEqual(labels, [])

        mirrorId = adminClient.addInboundMirror(projectId, [targetLabel],
                "http://www.example.com/conary/",
                "userpass", "mirror", "mirrorpass", "")
        mirrorId = adminClient.addInboundMirror(projectId, [targetLabel],
                "http://www.example.com/conary/",
                "userpass", "mirror", "mirrorpass", "")
        cu = db.cursor()
        cu.execute("SELECT mirrorOrder FROM InboundMirrors")
        self.failUnlessEqual([0, 1], [x[0] for x in cu.fetchall()])

    @fixtures.fixture("Full")
    def testOutboundMirror(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])
        adminClient.addOutboundMirrorTarget(omid, "http://www.example.com/conary/",
                "mirror", "mirrorpass")

        labels = adminClient.getOutboundMirrors()
        assert(labels ==
                [[1, projectId, sourceLabel, False, False, [], 0, True]])

        adminClient.delOutboundMirror(1)
        labels = adminClient.getOutboundMirrors()
        assert(labels == [])

    @fixtures.fixture("Full")
    def testOutboundMirrorAllLabels(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])
        adminClient.addOutboundMirrorTarget(omid, "http://www.example.com/conary/",
                "mirror", "mirrorpass")

        assert(adminClient.getOutboundMirrors()[0][3] is False)
        cu = db.cursor()
        cu.execute("UPDATE OutboundMirrors SET allLabels = 1")
        db.commit()
        assert(adminClient.getOutboundMirrors()[0][3] is True)

        cu.execute("DELETE FROM OutboundMirrors")
        db.commit()

        omid = adminClient.addOutboundMirror(projectId, [sourceLabel], allLabels = True)
        assert(adminClient.getOutboundMirrors()[0][3] is True)

    @fixtures.fixture("Full")
    def testOutboundMirrorRecurse(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])
        adminClient.addOutboundMirrorTarget(omid, "http://www.example.com/conary/",
                "mirror", "mirrorpass")
        assert(adminClient.getOutboundMirrors()[0][4] is False)
        cu = db.cursor()
        cu.execute("UPDATE OutboundMirrors SET recurse = 1")
        db.commit()
        assert(adminClient.getOutboundMirrors()[0][4] is True)

        cu.execute("DELETE FROM OutboundMirrors")
        db.commit()

        omid = adminClient.addOutboundMirror(projectId, [sourceLabel], recurse = True)
        assert(adminClient.getOutboundMirrors()[0][4] is True)

    @fixtures.fixture("Full")
    def testOutboundMatchInitial(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])

        # ensure this doesn't raise ItemNotFound
        self.failUnlessEqual(adminClient.getOutboundMirrorMatchTroves(omid), [],
                    "Listing empty matchTroves failed")

        # however, this should raise
        self.assertRaises(database.ItemNotFound, adminClient.getOutboundMirrorMatchTroves, 2)

    @fixtures.fixture("Full")
    def testOutboundMatchBasic(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])
        adminClient.setOutboundMirrorMatchTroves(omid, ["-.*:source$"])
        self.failUnlessEqual(adminClient.getOutboundMirrorMatchTroves(1),
                ["-.*:source$"])

    @fixtures.fixture("Full")
    def testOutboundMatchComposite(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])
        adminClient.addOutboundMirrorTarget(omid, "http://www.example.com/conary/",
                "mirror", "mirrorpass")
        adminClient.setOutboundMirrorMatchTroves(omid, ['-.*:source$', '-.*:debuginfo$'])
        self.failUnlessEqual(adminClient.getOutboundMirrorMatchTroves(omid),
               ['-.*:source$', '-.*:debuginfo$'])

    @fixtures.fixture("Full")
    def testOutboundMatchReordered(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])
        adminClient.addOutboundMirrorTarget(omid, "http://www.example.com/conary/",
                "mirror", "mirrorpass")

        adminClient.setOutboundMirrorMatchTroves(omid,
                                           ['-.*:source$', '-.*:debuginfo$'])
        assert(adminClient.getOutboundMirrorMatchTroves(omid) == \
               ['-.*:source$', '-.*:debuginfo$'])

        adminClient.setOutboundMirrorMatchTroves(omid,
                                           ['-.*:debuginfo$', '-.*:source$' ])
        assert(adminClient.getOutboundMirrorMatchTroves(1) == \
               ['-.*:debuginfo$', '-.*:source$'])


    @fixtures.fixture("Full")
    def testOutboundMatchParams(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])
        adminClient.addOutboundMirrorTarget(omid, "http://www.example.com/conary/",
                "mirror", "mirrorpass")

        self.assertRaises(mint_error.ParameterError,
                          adminClient.setOutboundMirrorMatchTroves,
                          omid, 'wrong')

        self.assertRaises(mint_error.ParameterError,
                          adminClient.setOutboundMirrorMatchTroves,
                          omid, ['also_wrong'])

        for matchStr in ('+right', '-right'):
            # ensure no error is raised for properly formed params
            adminClient.setOutboundMirrorMatchTroves(omid, [matchStr])

    @fixtures.fixture("Full")
    def testOutboundMirrorOrdering(self, db, data):
        adminClient = self.getClient("admin")

        def _build(idList, orderList):
            cu = db.cursor()
            cu.execute("DELETE FROM OutboundMirrors")

            for id, order in zip(idList, orderList):
                cu.execute("""INSERT INTO OutboundMirrors
                    (outboundMirrorId, mirrorOrder, sourceProjectId, targetLabels)
                    VALUES(?, ?, ?, "abcd")""", id, order, data['projectId'])
            db.commit()

        def _getOrder():
            cu = db.cursor()
            cu.execute("SELECT outboundMirrorId, mirrorOrder FROM OutboundMirrors ORDER BY mirrorOrder")
            return [(x[0], x[1]) for x in cu.fetchall()]

        _build([0, 1, 2, 3], [0, 1, 2, 3])

        adminClient.delOutboundMirror(1)
        self.failUnlessEqual(_getOrder(), [(0, 0), (2, 1), (3, 2)])

        adminClient.server._server.setOutboundMirrorOrder(2, 0)
        self.failUnlessEqual(_getOrder(), [(2, 0), (0, 1), (3, 2)])

        adminClient.server._server.setOutboundMirrorOrder(3, 3)
        self.failUnlessEqual(_getOrder(), [(2, 0), (0, 1), (3, 2)])

        newId = adminClient.addOutboundMirror(data['projectId'], ['frob'])

        self.failUnlessEqual(_getOrder(), [(2, 0), (0, 1), (3, 2), (newId, 3)])

    @fixtures.fixture("Full")
    def testOutboundMirrorTargets(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])

        target1 = ['http://target1.example.com/conary/', 'mirroruser', 'mirrorpass']
        target2 = ['http://target2.exmample.com/conary/', 'mirroruser2', 'mirrorpass2']

        # add a target
        target1Id = adminClient.addOutboundMirrorTarget(omid, *target1)

        # verify it got put in
        self.failUnlessEqual(adminClient.getOutboundMirrorTargets(omid),
                [ [ target1Id ] + target1 ])

        # add another target
        target2Id = adminClient.addOutboundMirrorTarget(omid, *target2)

        # verify it got put in, also
        self.failUnlessEqual(adminClient.getOutboundMirrorTargets(omid),
                [ [ target1Id ] + target1, [ target2Id ] + target2 ])

        # delete the first target
        adminClient.delOutboundMirrorTarget(target1Id)

        # verify it got deleted
        self.failUnlessEqual(adminClient.getOutboundMirrorTargets(omid),
                [ [ target2Id ] + target2 ])

        # now delete the whole mirror
        adminClient.delOutboundMirror(omid)

        self.assertRaises(database.ItemNotFound,
                adminClient.getOutboundMirror, omid)

        self.failIf(adminClient.getOutboundMirrorTargets(omid),
                "Didn't delete all the mirror targets")



if __name__ == "__main__":
    testsuite.main()
