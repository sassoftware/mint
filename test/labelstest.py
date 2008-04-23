#!/usr/bin/python2.4
#
# Copyright (c) 2005-2008 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MINT_DOMAIN, MINT_PROJECT_DOMAIN, PFQDN

from mint import database
from mint import server
from mint import users
from mint.projects import LabelMissing

import fixtures

class LabelsTest(fixtures.FixturedUnitTest):
    @testsuite.context("quick")
    @fixtures.fixture("Full")
    def testBasicAttributes(self, db, data):
        adminClient = self.getClient("admin")
        project = adminClient.getProject(data['projectId'])

        newLabelId = project.addLabel("bar.%s@rpl:devel" % MINT_PROJECT_DOMAIN,
            "http://%s/repos/bar/" % MINT_PROJECT_DOMAIN, "user1", "pass1")

        if self.cfg.rBuilderOnline:
            assert(project.getLabelIdMap() ==\
                {'bar.%s@rpl:devel' % MINT_PROJECT_DOMAIN: newLabelId,
                 'foo.%s@rpl:devel' % MINT_PROJECT_DOMAIN: 1})
        else:
            assert(project.getLabelIdMap() ==\
                 {'foo.' + MINT_PROJECT_DOMAIN + '@' +
                     adminClient.server._server.cfg.namespace + ':foo-1.0-devel': 1,
                 'bar.%s@rpl:devel' % MINT_PROJECT_DOMAIN: newLabelId})

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
        if self.cfg.rBuilderOnline:
            assert(project.getLabelIdMap() ==\
                {"foo.%s@rpl:devel" % MINT_PROJECT_DOMAIN: 1})
        else:
            assert(project.getLabelIdMap() ==\
                {'foo.' + MINT_PROJECT_DOMAIN + '@' +
                     adminClient.server._server.cfg.namespace + ':foo-1.0-devel': 1})

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
                "localhost", shortname="external", version="1.0", 
                prodtype="Component")

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

if __name__ == "__main__":
    testsuite.main()
