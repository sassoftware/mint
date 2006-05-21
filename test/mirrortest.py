#!/usr/bin/python2.4
# -*- mode: python -*-
#
# Copyright (c) 2006 rPath, Inc.
# All rights reserved
#

import os
import testsuite
testsuite.setup()

import rephelp, sigtest
import mint_rephelp

from conary import versions
from conary.conaryclient import ConaryClient
from conary.build import signtrove
from conary.lib import openpgpfile, openpgpkey

runTest = False
scriptPath = os.path.join(os.path.split(os.path.split(os.path.realpath(__file__))[0])[0], 'scripts')

class MintMirrorTest(mint_rephelp.MintRepositoryHelper):
    def createMirrorUser(self, repos,
                         labelStr = "localhost.other.host@rpl:linux"):
        label = versions.Label(labelStr)
        repos.addUser(label, "mirror", "mirror")
        repos.addAcl(label, "mirror", None, None, True, False, False)
        repos.setUserGroupCanMirror(label, "mirror", True)

    def createTroves(self, repos, start, count):
        for i in range(start, start + count):
            self.addComponent('test%d:runtime' % i, '1.0', filePrimer = i,
                              repos = repos)
            self.addCollection('test%d' % i, '1.0', [ "test%d:runtime" % i ],
                              repos = repos)

    def inboundMirror(self):
        url = "http://mintauth:mintpass@localhost:%d/xmlrpc-private/" % \
              self.port

        mirrorScript = os.path.join(scriptPath , 'mirror-inbound')
        assert(os.access(mirrorScript, os.X_OK))
        try:
            os.system("%s %s" % (mirrorScript, url))
        finally:
            self.showOutput()

    def outboundMirror(self):
        url = "http://mintauth:mintpass@localhost:%d/xmlrpc-private/" % \
              self.port

        mirrorScript = os.path.join(scriptPath , 'mirror-outbound')
        assert(os.access(mirrorScript, os.X_OK))
        self.hideOutput()
        try:
            os.system("%s %s" % (mirrorScript, url))
        finally:
            self.showOutput()

    def compareRepositories(self, repos1, repos2,
                            base = "localhost.other.host"):

        def _flatten(d):
            l = []
            for name, versionD in d.iteritems():
                for version, flavorList in versionD.iteritems():
                    l += [ (name, version, flavor) for flavor in flavorList ]

            return l

        self.cfg.user.remove(("*", "test", "foo"))
        troveD1 = repos1.getTroveVersionList(base, { None : None })
        troveD2 = repos2.getTroveVersionList(base, { None : None })

        assert(troveD1 == troveD2)

        troves1 = repos1.getTroves(_flatten(troveD1))
        troves2 = repos2.getTroves(_flatten(troveD2))
        assert(troves1 == troves2)

        assert(troveD1)

    def testInboundMirror(self):
        global runTest
        if not runTest:
            raise testsuite.SkipTestException

        client, userId = self.quickMintAdmin("testuser", "testpass")

        # set up the source repository
        sourceRepos = self.openRepository(1, serverName = "localhost.other.host")
        sourcePort = self.servers.getServer(1).port
        map = dict(self.cfg.repositoryMap)
        self.createMirrorUser(sourceRepos)
        self.cfg.buildLabel = versions.Label("localhost.other.host@rpl:linux")
        self.createTroves(sourceRepos, 0, 2)

        # set up the target repository
        projectId = self.newProject(client, "Mirrored Project", "localhost", domainname = "other.host")
        project = client.getProject(projectId)
        labelId = project.getLabelIdMap().values()[0]
        project.editLabel(labelId, "localhost.other.host@rpl:linux",
            "https://test.rpath.local2:%d/repos/localhost/" % self.securePort, "mintauth", "mintpass")
        client.addInboundLabel(projectId, labelId, "http://localhost:%s/conary/" % sourcePort, "mirror", "mirror")

        cu = self.db.cursor()
        cu.execute("UPDATE Projects SET external=1 WHERE projectId=?", projectId)
        self.db.commit()

        # do the mirror
        self.inboundMirror()

        # compare
        targetRepos = ConaryClient(project.getConaryConfig()).getRepos()
        self.compareRepositories(sourceRepos, targetRepos)
        self.stopRepository(1)

    def testOutboundMirror(self):
        global runTest
        if not runTest:
            raise testsuite.SkipTestException

        client, userId = self.quickMintAdmin("testuser", "testpass")

        # set up the target repository
        targetRepos = self.openRepository(1,
                                          serverName = "localhost.rpath.local2")
        targetPort = self.servers.getServer(1).port
        self.createMirrorUser(targetRepos, "localhost.rpath.local2@rpl:linux")
        self.cfg.buildLabel = versions.Label("localhost.rpath.local2@rpl:linux")

        # set up the source repository
        projectId = self.newProject(client, "Mirrored Project", "localhost")
        project = client.getProject(projectId)
        labelId = project.getLabelIdMap().values()[0]
        client.addOutboundLabel(projectId, labelId,
                                "http://localhost:%s/conary/" % targetPort,
                                "mirror", "mirror")

        sourceRepos = ConaryClient(project.getConaryConfig()).getRepos()
        self.createTroves(sourceRepos, 0, 2)

        # do the mirror
        self.outboundMirror()

        # compare
        self.compareRepositories(sourceRepos, targetRepos,
                                 base = "localhost.rpath.local2")
        self.stopRepository(1)


if __name__ == "__main__":
    runTest = True
    testsuite.main()
