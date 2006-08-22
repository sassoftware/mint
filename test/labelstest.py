#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
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
    def testExternalVersions(self, db, data):
        def addLabel(projectId, label, url = 'http://none'):
            cu.execute("""INSERT INTO Labels
                              (projectId, label, url, username, password)
                              VALUES(?, ?, ?, 'none', 'none')""",
                       projectId, label, url)

        adminClient = self.getClient("admin")

        # foo project is given to us by the fixture
        projectId = data['projectId']
        project = adminClient.getProject(data['projectId'])

        projectId2 = adminClient.newProject("Bar Project", "bar", "localhost")
        project2 = adminClient.getProject(projectId2)

        cu = db.cursor()

        cu.execute("UPDATE Projects SET external=1 WHERE projectId=?",
                   projectId2)

        addLabel(projectId, 'foo.rpath.org@rpl:devel')
        addLabel(projectId, 'bar.rpath.org@rpl:devel')
        addLabel(projectId2, 'baz.rpath.org@rpl:devel')
        addLabel(projectId, 'foo.rpath.org@diff:label')
        db.commit()

        # a local project returns False
        self.failIf(adminClient.versionIsExternal( \
            '/foo.rpath.org@rpl:devel//1/1.0.0-1-0.1'),
                    "internal version appeared external")

        # an external project returns True
        self.failIf(not adminClient.versionIsExternal( \
            '/baz.rpath.org@rpl:devel//1/1.0.0-1-0.1'),
                    "external version appeared internal")

        # missing item raises ItemNotFound
        # FIXME: re-enable once versionIsExternal raises an exception
        #self.assertRaises(database.ItemNotFound, adminClient.versionIsExternal,
        #                  '/just.not.there@rpl:devel//1/1.0.0-1-0.1')


        cu.execute("UPDATE Projects SET hidden=1 WHERE projectId=?",
                   projectId2)

        # legal reference to local hidden project returns False
        self.failIf(adminClient.versionIsExternal( \
            '/foo.rpath.org@rpl:devel//1/1.0.0-1-0.1'),
                    "internal version appeared external")

        # illegal reference to local hidden project raises ItemNotFound
        # FIXME: re-enable once versionIsExternal raises an exception
        #self.assertRaises(database.ItemNotFound, adminClient2.versionIsExternal,
        #                  '/just.not.there@rpl:devel//1/1.0.0-1-0.1')

    @fixtures.fixture("Full")
    def testInboundLabel(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        adminClient.addInboundLabel(projectId, projectId,
                "http://www.example.com/conary/",
                "mirror", "mirrorpass")

        labels = adminClient.getInboundLabels()
        assert(labels ==
                [[projectId, projectId, 'http://www.example.com/conary/',
                  'mirror', 'mirrorpass']])

    @fixtures.fixture("Full")
    def testOutboundLabel(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        adminClient.addOutboundLabel(projectId, projectId, 
                "http://www.example.com/conary/",
                "mirror", "mirrorpass")

        labels = adminClient.getOutboundLabels()
        assert(labels ==
                [[projectId, projectId, 'http://www.example.com/conary/',
                  'mirror', 'mirrorpass', False, False]])

        adminClient.delOutboundLabel(projectId,
                'http://www.example.com/conary/')
        labels = adminClient.getOutboundLabels()
        assert(labels == [])

    @fixtures.fixture("Full")
    def testOutboundLabelAllLabels(self, db, data):
        projectId = data['projectId']
        labelId = projectId
        adminClient = self.getClient("admin")
        adminClient.addOutboundLabel(projectId, labelId,
                "http://www.example.com/conary/",
                "mirror", "mirrorpass")
        assert(adminClient.getOutboundLabels()[0][5] is False)
        cu = db.cursor()
        cu.execute("UPDATE OutboundLabels SET allLabels = 1")
        db.commit()
        assert(adminClient.getOutboundLabels()[0][5] is True)

        cu.execute("DELETE FROM OutboundLabels")
        db.commit()

        adminClient.addOutboundLabel(projectId, labelId,
                "http://www.example.com/conary/",
                "mirror", "mirrorpass", allLabels = True)
        assert(adminClient.getOutboundLabels()[0][5] is True)

    @fixtures.fixture("Full")
    def testOutboundLabelRecurse(self, db, data):
        projectId = data['projectId']
        labelId = projectId
        adminClient = self.getClient("admin")
        adminClient.addOutboundLabel(projectId, labelId,
                "http://www.example.com/conary/",
                "mirror", "mirrorpass")
        assert(adminClient.getOutboundLabels()[0][6] is False)
        cu = db.cursor()
        cu.execute("UPDATE OutboundLabels SET recurse = 1")
        db.commit()
        assert(adminClient.getOutboundLabels()[0][6] is True)

        cu.execute("DELETE FROM OutboundLabels")
        db.commit()

        adminClient.addOutboundLabel(projectId, labelId,
                "http://www.example.com/conary/",
                "mirror", "mirrorpass", recurse = True)
        assert(adminClient.getOutboundLabels()[0][6] is True)

    @fixtures.fixture("Full")
    def testOutboundMatchInitial(self, db, data):
        projectId = data['projectId']
        labelId = projectId
        adminClient = self.getClient("admin")

        # ensure this doesn't raise ItemNotFound
        self.failIf(adminClient.getOutboundMatchTroves(labelId) != [],
                    "Listing empty matchTroves failed")

    @fixtures.fixture("Full")
    def testOutboundMatchBasic(self, db, data):
        projectId = data['projectId']
        labelId = projectId
        adminClient = self.getClient("admin")

        adminClient.setOutboundMatchTroves(projectId, labelId, ["-.*:source$"])
        assert(adminClient.getOutboundMatchTroves(labelId) == ["-.*:source$"])

    @fixtures.fixture("Full")
    def testOutboundMatchComposite(self, db, data):
        projectId = data['projectId']
        labelId = projectId
        adminClient = self.getClient("admin")

        adminClient.setOutboundMatchTroves(projectId, labelId,
                                           ['-.*:source$', '-.*:debuginfo$'])
        assert(adminClient.getOutboundMatchTroves(labelId) == \
               ['-.*:source$', '-.*:debuginfo$'])

    @fixtures.fixture("Full")
    def testOutboundMatchReordered(self, db, data):
        projectId = data['projectId']
        labelId = projectId
        adminClient = self.getClient("admin")

        adminClient.setOutboundMatchTroves(projectId, labelId,
                                           ['-.*:source$', '-.*:debuginfo$'])
        assert(adminClient.getOutboundMatchTroves(labelId) == \
               ['-.*:source$', '-.*:debuginfo$'])

        adminClient.setOutboundMatchTroves(projectId, labelId,
                                           ['-.*:source$', '-.*:debuginfo$'])
        assert(adminClient.getOutboundMatchTroves(labelId) == \
               ['-.*:source$', '-.*:debuginfo$'])


    @fixtures.fixture("Full")
    def testOutboundMatchEnumerate(self, db, data):
        projectId = data['projectId']
        labelId = projectId
        adminClient = self.getClient("admin")

        cu = db.cursor()
        for order in ['-a', '-b', '+c', '-d'], ['+d', '-a'], ['+c']:

            adminClient.setOutboundMatchTroves(projectId, labelId, order)

            cu.execute("SELECT idx, matchStr FROM OutboundMatchTroves ORDER BY idx")
            self.failIf([x for x in cu.fetchall()] != \
                        [x for x in enumerate(order)],
                        "order of troves was mangled")

    @fixtures.fixture("Full")
    def testOutboundMatchParams(self, db, data):
        projectId = data['projectId']
        labelId = projectId
        adminClient = self.getClient("admin")

        self.assertRaises(mint_error.ParameterError,
                          adminClient.setOutboundMatchTroves,
                          projectId, labelId, 'wrong')

        for matchStr in ('+right', '-right'):
            # ensure no error is raised for properly formed params
            adminClient.setOutboundMatchTroves(projectId, labelId, [matchStr])


if __name__ == "__main__":
    testsuite.main()
