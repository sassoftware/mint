#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#


from mint_rephelp import MINT_DOMAIN, MINT_PROJECT_DOMAIN, FQDN

from mint.lib import database
from mint import server
from mint.projects import LabelMissing

import fixtures

class LabelsTest(fixtures.FixturedUnitTest):

    def _getHostMap(self, labelMap):
        hostMap = {}
        for label, labelId in labelMap.items():
            host = label.split('@', 1)[0]
            hostMap[host] = labelId
        return hostMap


    @testsuite.context("quick")
    @fixtures.fixture("Full")
    def testBasicAttributes(self, db, data):
        adminClient = self.getClient("admin")
        project = adminClient.getProject(data['projectId'])

        newLabelId = project.addLabel("bar.%s@rpl:devel" % MINT_PROJECT_DOMAIN,
            "http://%s/repos/bar/" % MINT_PROJECT_DOMAIN, "user1", "pass1")

        assert(self._getHostMap(project.getLabelIdMap()) ==\
             {'foo.%s' % MINT_PROJECT_DOMAIN : 1,
              'bar.%s' % MINT_PROJECT_DOMAIN : newLabelId})

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
        assert(self._getHostMap(project.getLabelIdMap()) ==\
              {'foo.%s' % MINT_PROJECT_DOMAIN : 1 })
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
        self.failUnlessEqual({'foo.%s' % MINT_PROJECT_DOMAIN: 'http://%s/repos/foo/' % FQDN}, x)

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
                  'userpass', 'mirror', 'mirrorpass', '', '',  0]])

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

