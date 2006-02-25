#!/usr/bin/python2.4
# -*- mode: python -*-
#
# Copyright (c) 2006 rPath, Inc.
# All rights reserved
#

import os, sys, tempfile
if '..' not in sys.path: sys.path.append('..')
import testsuite
testsuite.setup()

import rephelp, sigtest
import mint_rephelp

from conary import versions
from conary.conaryclient import ConaryClient
from conary.build import signtrove
from conary.lib import openpgpfile, openpgpkey

runTest = True 

class MintMirrorTest(mint_rephelp.MintRepositoryHelper):
    def createMirrorUser(self, repos):
        label = versions.Label("localhost.other.host@rpl:linux")
        repos.addUser(label, "mirror", "mirror")
        repos.addAcl(label, "mirror", None, None, True, False, False)
        repos.setUserGroupCanMirror(label, "mirror", True)

    def createTroves(self, repos, start, count):
        for i in range(start, start + 2):
            self.addComponent('test%d:runtime' % i, '1.0', filePrimer = i,
                              repos = repos)
            self.addCollection('test%d' % i, '1.0', [ "test%d:runtime" % i ],
                              repos = repos)

    def runMirror(self):
        url = "http://mintauth:mintpass@localhost:%d/xmlrpc-private/" % self.port
        self.hideOutput()
        try:
            os.system("../scripts/mirror %s" % url)
        finally:
            self.showOutput()

    def compareRepositories(self, repos1, repos2):

        def _flatten(d):
            l = []
            for name, versionD in d.iteritems():
                for version, flavorList in versionD.iteritems():
                    l += [ (name, version, flavor) for flavor in flavorList ]

            return l

        troveD1 = repos1.getTroveVersionList("localhost.other.host", { None : None })
        troveD2 = repos2.getTroveVersionList("localhost.other.host", { None : None })
        assert(troveD1 == troveD2)

        troves1 = repos1.getTroves(_flatten(troveD1))
        troves2 = repos2.getTroves(_flatten(troveD2))
        assert(troves1 == troves2)

        pgpKeys1 = repos1.getNewPGPKeys("localhost.other.host", -1)
        pgpKeys2 = repos2.getNewPGPKeys("localhost.other.host", -1)
        assert(pgpKeys1 == pgpKeys2)

    def testMirror(self):
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
            "http://mint.rpath.local:%d/repos/localhost/" % self.port, "mintauth", "mintpass")
        client.addMirroredLabel(projectId, labelId, "http://localhost:%s/conary/" % sourcePort, "mirror", "mirror")
        client.addRemappedRepository('localhost.rpath.local', 'localhost.other.host')

        cu = self.db.cursor()
        cu.execute("UPDATE Projects SET external=1 WHERE projectId=?", projectId)
        self.db.commit()

        # do the mirror
        self.runMirror()

        # compare
        targetRepos = ConaryClient(project.getConaryConfig()).getRepos()
        self.compareRepositories(sourceRepos, targetRepos)


if __name__ == "__main__":
    runTest = True
    testsuite.main()
