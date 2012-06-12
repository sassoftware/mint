#!/usr/bin/python
# -*- mode: python -*-
#
# Copyright (c) 2005-2008 rPath, Inc.
# All rights reserved
#

import re
import os
import testsuite
testsuite.setup()

import tempfile

from mint_test import mint_rephelp

from mint import helperfuncs
from conary import versions
from conary import deps
from conary.conaryclient import ConaryClient
from conary.build import signtrove
from conary.lib import openpgpfile, openpgpkey

from testutils import mock

runTest = False
debug = False
scriptPath = os.path.join(os.path.split(os.path.split(os.path.realpath(__file__))[0])[0], 'scripts')

class MintMirrorTest(mint_rephelp.MintRepositoryHelper):
    def createMirrorUser(self, repos,
                         labelStr = "localhost.other.host@rpl:devel"):
        label = versions.Label(labelStr)
        repos.addRole(label, "mirror")
        repos.addUser(label, "mirror", "mirror")
        repos.addRoleMember(label, "mirror", "mirror")
        repos.addAcl(label, "mirror", None, None, write=True, remove=False)
        repos.setRoleCanMirror(label, "mirror", True)

    def createTroves(self, repos, start, count):
        for i in range(start, start + count):
            self.addComponent('test%d:runtime' % i, '1.0', filePrimer = i,
                              repos = repos)
            self.addCollection('test%d' % i, '1.0', [ "test%d:runtime" % i ],
                              repos = repos)

    def outboundMirror(self):
        import xmlrpclib
        oldxmlrpclib = xmlrpclib
        xmlrpclib = mock.MockInstance(xmlrpclib)
        try:
            url = "http://mintauth:mintpass@localhost:%d/xmlrpc-private/" % \
                  self.port
            cfg = self.servers.getServer(0).serverRoot + '/rbuilder.conf'
            mirrorScript = os.path.join(scriptPath , 'mirror-outbound')
            assert(os.access(mirrorScript, os.X_OK))
            cmd = "%s %s -c %s" % (mirrorScript, url, cfg)
            if debug:
                os.system(cmd + ' --show-mirror-cfg')
            else:
                self.captureAllOutput( os.system, cmd)
        finally:
            xmlrpclib = oldxmlrpclib

    def mirrorOffline(self):
        if self.mintCfg.SSL:
            url = "https://test.rpath.local:%d/repos/localhost/" % \
                  self.securePort
        else:
            url = "http://test.rpath.local:%d/repos/localhost/" % self.port
        branchName = "localhost.rpath.local2@rpl:devel"
        mirrorScript = os.path.join(scriptPath , 'mirror-offline')
        assert(os.access(mirrorScript, os.X_OK))
        mirrorWorkDir = tempfile.mkdtemp()
        curDir = os.getcwd()
        try:
            os.chdir(mirrorWorkDir)
            if debug:
                os.system("%s %s %s %s %s %s" % \
                                      (mirrorScript, url, branchName, 'mirror',
                                       self.mintCfg.authUser,
                                       self.mintCfg.authPass))
            else:
                self.captureAllOutput(os.system, "%s %s %s %s %s %s" % \
                               (mirrorScript, url, branchName, 'mirror',
                               self.mintCfg.authUser,
                               self.mintCfg.authPass))
        finally:
            os.chdir(curDir)
        return mirrorWorkDir

    def compareRepositories(self, repos1, repos2,
                            base = "localhost.other.host",
                            exclude = None,
                            onlyLabel = None):

        def _flatten(d):
            l = []
            for name, versionD in d.iteritems():
                for version, flavorList in versionD.iteritems():
                    l += [ (name, version, flavor) for flavor in flavorList ]

            return l

        try:
            self.cfg.user.remove(("*", "test", "foo"))
        except ValueError:
            pass

        troveD1 = repos1.getTroveVersionList(base, { None : None })

        troveD2 = repos2.getTroveVersionList(base, { None : None })

        if exclude:
            troveD1 = dict(x for x in troveD1.items() if not exclude.match(x[0]))
        if onlyLabel:
            troveD1 = dict(x for x in troveD1.items() if str(x[1].keys()[0].branch().label()) == 'localhost.rpath.local2@rpl:devel')

        assert(troveD1 == troveD2)

        troves1 = repos1.getTroves(_flatten(troveD1))
        troves2 = repos2.getTroves(_flatten(troveD2))

        if exclude:
            troves1 = [x for x in troves1 if not exclude.match(x.getName())]
        assert(troves1 == troves2)

        assert(troveD1)

    def testInboundMirror(self):
        global runTest
        if not runTest:
            raise testsuite.SkipTestException

        client, userId = self.quickMintAdmin("testuser", "testpass")

        # set up the source repository
        sourceRepos = self.startMintServer(1, serverName = "localhost.other.host")
        sourcePort = self.servers.getServer(1).port
        map = dict(self.cfg.repositoryMap)
        self.createMirrorUser(sourceRepos)
        self.cfg.buildLabel = versions.Label("localhost.other.host@rpl:devel")
        self.createTroves(sourceRepos, 0, 2)

        self.cfg.buildLabel = versions.Label("localhost.other.host@rpl:notforyou")
        self.createTroves(sourceRepos, 3, 5)

        # set up the target repository
        projectId = self.newProject(client, "Mirrored Project", "localhost", domainname = "other.host")
        project = client.getProject(projectId)
        labelId = project.getLabelIdMap().values()[0]
        project.editLabel(labelId, "localhost.other.host@rpl:devel",
            "https://test.rpath.local2:%d/repos/localhost/" % self.securePort,
            "userpass", "mintauth", "mintpass", "")
        client.addInboundMirror(projectId, ["localhost.other.host@rpl:devel"],
            "http://localhost:%s/conary/" % sourcePort, "userpass", "mirror",
            "mirror", "", False)

        cu = self.db.cursor()
        cu.execute("UPDATE Projects SET external=1 WHERE projectId=?", projectId)
        self.db.commit()

        try:
            # do the mirror
            self.inboundMirror()

            exclude = re.compile("test[34567]")

            # compare
            targetRepos = ConaryClient(project.getConaryConfig()).getRepos()
            self.compareRepositories(sourceRepos, targetRepos, exclude = exclude)
        finally:
            self.stopRepository(1)

    def testInboundMirrorMultipleLabels(self):
        global runTest
        if not runTest:
            raise testsuite.SkipTestException

        client, userId = self.quickMintAdmin("testuser", "testpass")

        # set up the source repository
        sourceRepos = self.startMintServer(1, serverName = "localhost.other.host")
        sourcePort = self.servers.getServer(1).port
        map = dict(self.cfg.repositoryMap)
        self.createMirrorUser(sourceRepos)
        self.cfg.buildLabel = versions.Label("localhost.other.host@rpl:devel")
        self.createTroves(sourceRepos, 0, 2)

        self.cfg.buildLabel = versions.Label("localhost.other.host@rpl:alsothese")
        self.createTroves(sourceRepos, 3, 5)

        # set up the target repository
        projectId = self.newProject(client, "Mirrored Project", "localhost", domainname = "other.host")
        project = client.getProject(projectId)
        labelId = project.getLabelIdMap().values()[0]
        project.editLabel(labelId, "localhost.other.host@rpl:devel",
            "https://test.rpath.local2:%d/repos/localhost/" % self.securePort,
            "userpass", "mintauth", "mintpass", "")
        client.addInboundMirror(projectId, ["localhost.other.host@rpl:devel",
            "localhost.other.host@rpl:alsothese"],
            "http://localhost:%s/conary/" % sourcePort, "userpass", "mirror",
            "mirror", "", False)

        cu = self.db.cursor()
        cu.execute("UPDATE Projects SET external=1 WHERE projectId=?", projectId)
        self.db.commit()

        # do the mirror

        # compare
        try:
            self.inboundMirror()
            targetRepos = ConaryClient(project.getConaryConfig()).getRepos()
            self.compareRepositories(sourceRepos, targetRepos)
        finally:
            self.stopRepository(1)

    def testOutboundMirror(self):
        global runTest
        if not runTest:
            raise testsuite.SkipTestException

        client, userId = self.quickMintAdmin("testuser", "testpass")

        # set up the target repository
        targetRepos = self.startMintServer(1,
                                          serverName = "localhost.rpath.local2")
        targetPort = self.servers.getServer(1).port
        self.createMirrorUser(targetRepos, "localhost.rpath.local2@rpl:devel")
        self.cfg.buildLabel = versions.Label("localhost.rpath.local2@rpl:devel")

        # set up the source repository
        projectId = self.newProject(client, "Mirrored Project", "localhost")
        project = client.getProject(projectId)
        outboundMirrorId = client.addOutboundMirror(projectId,
                ["localhost.rpath.local2@rpl:devel"], allLabels = True)
        outboundMirrorTargetId = client.addOutboundMirrorTarget(outboundMirrorId,
                "http://localhost:%s/conary/" % targetPort, "mirror", "mirror")

        # create troves on rpl:devel
        sourceRepos = ConaryClient(project.getConaryConfig()).getRepos()
        self.createTroves(sourceRepos, 0, 2)

        # create some troves on a different label
        self.cfg.buildLabel = versions.Label("localhost.rpath.local2@rpl:other")
        self.createTroves(sourceRepos, 3, 5)

        client.setOutboundMirrorMatchTroves(outboundMirrorId,
                ["-test0", '+.*'])
        exclude = re.compile("test0")

        try:
            # do the mirror
            self.outboundMirror()

            # compare
            self.compareRepositories(sourceRepos, targetRepos,
                                     base = "localhost.rpath.local2",
                                     exclude = exclude)
        finally:
            self.stopRepository(1)

    def testOutboundMirrorMultipleTargets(self):
        global runTest
        if not runTest:
            raise testsuite.SkipTestException

        client, userId = self.quickMintAdmin("testuser", "testpass")

        # set up the target repositories
        targetRepos1 = self.startMintServer(1,
                                          serverName = "localhost.rpath.local2")
        targetPort1 = self.servers.getServer(1).port

        targetRepos2 = self.startMintServer(2,
                                          serverName = "localhost.rpath.local2")
        targetPort2 = self.servers.getServer(2).port

        self.createMirrorUser(targetRepos1, "localhost.rpath.local2@rpl:devel")
        self.createMirrorUser(targetRepos2, "localhost.rpath.local2@rpl:devel")
        self.cfg.buildLabel = versions.Label("localhost.rpath.local2@rpl:devel")

        # set up the source repository
        projectId = self.newProject(client, "Mirrored Project", "localhost")
        project = client.getProject(projectId)
        outboundMirrorId = client.addOutboundMirror(projectId,
                ["localhost.rpath.local2@rpl:devel"],
                allLabels = True)
        outboundMirrorTargetId = client.addOutboundMirrorTarget(outboundMirrorId,
                "http://localhost:%s/conary/" % targetPort1, "mirror", "mirror")
        outboundMirrorTargetId = client.addOutboundMirrorTarget(outboundMirrorId,
                "http://localhost:%s/conary/" % targetPort2, "mirror", "mirror")

        # create troves on rpl:devel
        sourceRepos = ConaryClient(project.getConaryConfig()).getRepos()
        self.createTroves(sourceRepos, 0, 2)

        # create some troves on a different label
        self.cfg.buildLabel = versions.Label("localhost.rpath.local2@rpl:other")
        self.createTroves(sourceRepos, 3, 5)

        client.setOutboundMirrorMatchTroves(outboundMirrorId,
                ["-test0", '+.*'])
        exclude = re.compile("test0")

        try:
            # do the mirror
            self.outboundMirror()

            # compare
            self.compareRepositories(sourceRepos, targetRepos1,
                                     base = "localhost.rpath.local2",
                                     exclude = exclude)
            self.compareRepositories(sourceRepos, targetRepos2,
                                     base = "localhost.rpath.local2",
                                     exclude = exclude)
        finally:
            self.stopRepository(1)
            self.stopRepository(2)

    def testOutboundMirrorAllLabels(self):
        global runTest
        if not runTest:
            raise testsuite.SkipTestException

        client, userId = self.quickMintAdmin("testuser", "testpass")

        # set up the target repository
        targetRepos = self.startMintServer(1,
                                          serverName = "localhost.rpath.local2")
        targetPort = self.servers.getServer(1).port
        self.createMirrorUser(targetRepos, "localhost.rpath.local2@rpl:devel")
        self.cfg.buildLabel = versions.Label("localhost.rpath.local2@rpl:devel")

        # set up the source repository
        projectId = self.newProject(client, "Mirrored Project", "localhost")
        project = client.getProject(projectId)
        outboundMirrorId = client.addOutboundMirror(projectId,
                ["localhost.rpath.local2@rpl:devel"], allLabels = False)
        outboundMirrorTargetId = client.addOutboundMirrorTarget(outboundMirrorId,
                "http://localhost:%s/conary/" % targetPort, "mirror", "mirror")

        # create troves on rpl:devel
        sourceRepos = ConaryClient(project.getConaryConfig()).getRepos()
        self.createTroves(sourceRepos, 0, 2)

        # create some troves on a different label
        self.cfg.buildLabel = versions.Label("localhost.rpath.local2@rpl:other")
        self.createTroves(sourceRepos, 3, 5)

        try:
            # do the mirror
            self.outboundMirror()

            # compare -- only troves from rpl:devel should exist on the target
            self.compareRepositories(sourceRepos, targetRepos,
                                     base = "localhost.rpath.local2",
                                     onlyLabel = "localhost.rpath.local2@rpl:devel")
        finally:
            self.stopRepository(1)

    def testOutboundMirrorSomeLabels(self):
        global runTest
        if not runTest:
            raise testsuite.SkipTestException

        client, userId = self.quickMintAdmin("testuser", "testpass")

        # set up the target repository
        targetRepos = self.startMintServer(1,
                                          serverName = "localhost.rpath.local2")
        targetPort = self.servers.getServer(1).port
        self.createMirrorUser(targetRepos, "localhost.rpath.local2@rpl:devel")
        self.cfg.buildLabel = versions.Label("localhost.rpath.local2@rpl:devel")

        # set up the source repository
        projectId = self.newProject(client, "Mirrored Project", "localhost")
        project = client.getProject(projectId)
        outboundMirrorId = client.addOutboundMirror(projectId,
                ["localhost.rpath.local2@rpl:devel",
                    "localhost.rpath.local2@rpl:other"],
                allLabels = False)
        outboundMirrorTargetId = client.addOutboundMirrorTarget(outboundMirrorId,
                "http://localhost:%s/conary/" % targetPort, "mirror", "mirror")

        # create troves on rpl:devel
        sourceRepos = ConaryClient(project.getConaryConfig()).getRepos()
        self.createTroves(sourceRepos, 0, 2)

        # create some troves on a different label
        self.cfg.buildLabel = versions.Label("localhost.rpath.local2@rpl:other")
        self.createTroves(sourceRepos, 3, 5)

        try:
            # do the mirror
            self.outboundMirror()

            # compare
            self.compareRepositories(sourceRepos, targetRepos,
                                     base = "localhost.rpath.local2")
        finally:
            self.stopRepository(1)


    def testMirrorOffline(self):
        global runTest
        if not runTest:
            raise testsuite.SkipTestException

        client, userId = self.quickMintAdmin("testuser", "testpass")
        # set up the source repository
        projectId = self.newProject(client, "Mirrored Project", "localhost")
        project = client.getProject(projectId)
        labelId = project.getLabelIdMap().values()[0]

        # create troves on rpl:devel
        sourceRepos = ConaryClient(project.getConaryConfig()).getRepos()
        self.createTroves(sourceRepos, 0, 3)

        try:
            workDir = self.mirrorOffline()
            assert (sorted(os.listdir(workDir)) == \
                    ['mirror', 'mirror-localhost.rpath.local2000.iso']), \
                    "mirror-offline script failed to run"
            assert (sorted(os.listdir(os.path.join(workDir, 'mirror'))) == \
                    ['contents', 'sqldb', 'tmp'])
            f = open(os.path.join(workDir, 'mirror-localhost.rpath.local2000.iso'))
            f.seek(51200)

            d = f.read(30)
            self.failUnlessEqual(d, 'localhost.rpath.local2\n1/1\n2\n\x00')
        finally:
            try:
                util.rmtree(workDir)
            except:
                pass
            try:
                f.close()
            except:
                pass

    def testMirrorByGroup(self):
        global runTest
        if not runTest:
            raise testsuite.SkipTestException

        client, userId = self.quickMintAdmin("testuser", "testpass")

        # set up the target repositories
        targetRepos1 = self.startMintServer(1,
                                          serverName = "localhost.rpath.local2")
        targetRepos2 = self.startMintServer(2,
                                          serverName = "localhost.rpath.local2")
        targetPort1 = self.servers.getServer(1).port
        targetPort2 = self.servers.getServer(2).port

        self.createMirrorUser(targetRepos1, "localhost.rpath.local2@rpl:devel")
        self.createMirrorUser(targetRepos2, "localhost.rpath.local2@rpl:devel")
        self.cfg.buildLabel = versions.Label("localhost.rpath.local2@rpl:devel")

        # set up the source repository
        projectId = self.newProject(client, "Mirrored Project", "localhost")
        project = client.getProject(projectId)
        outboundMirrorId = client.addOutboundMirror(projectId,
                ["localhost.rpath.local2@rpl:devel"],
                recurse = True)
        outboundMirrorId2 = client.addOutboundMirror(projectId,
                ["localhost.rpath.local2@rpl:devel"],
                recurse = True)
        client.setOutboundMirrorMatchTroves(outboundMirrorId,
                               ['+group-test'])
        client.setOutboundMirrorMatchTroves(outboundMirrorId2,
                               ['+group-test2'])
        outboundMirrorTargetId = client.addOutboundMirrorTarget(outboundMirrorId,
                "http://localhost:%s/conary/" % targetPort1, "mirror", "mirror")
        outboundMirrorTargetId = client.addOutboundMirrorTarget(outboundMirrorId,
                "http://localhost:%s/conary/" % targetPort2, "mirror", "mirror")

        outboundMirrorTargetId = client.addOutboundMirrorTarget(outboundMirrorId2,
                "http://localhost:%s/conary/" % targetPort1, "mirror", "mirror")
        outboundMirrorTargetId = client.addOutboundMirrorTarget(outboundMirrorId2,
                "http://localhost:%s/conary/" % targetPort2, "mirror", "mirror")

        # create troves on rpl:devel
        sourceRepos = ConaryClient(project.getConaryConfig()).getRepos()
        self.createTroves(sourceRepos, 0, 3)

        # create some troves on a different label
        self.cfg.buildLabel = versions.Label("localhost.rpath.local2@rpl:other")
        self.createTroves(sourceRepos, 3, 5)
        self.addQuickTestCollection("group-test", "/localhost.rpath.local2@rpl:devel/1.0-1-1",
                                    [ ("test1:runtime", "/localhost.rpath.local2@rpl:devel/1.0-1-1"),
                                      ("test2:runtime", "/localhost.rpath.local2@rpl:devel/1.0-1-1"),
                                      ("test3:runtime", "/localhost.rpath.local2@rpl:other/1.0-1-1"),
                                      ("test4:runtime", "/localhost.rpath.local2@rpl:other/1.0-1-1"),
                                    ], repos=sourceRepos)


        self.addQuickTestCollection("group-test2", "/localhost.rpath.local2@rpl:devel/1.0-1-1",
                                    [ ("test3:runtime", "/localhost.rpath.local2@rpl:devel/1.0-1-1"),
                                      ("test4:runtime", "/localhost.rpath.local2@rpl:devel/1.0-1-1"),
                                      ("test5:runtime", "/localhost.rpath.local2@rpl:other/1.0-1-1"),
                                      ("test6:runtime", "/localhost.rpath.local2@rpl:other/1.0-1-1"),
                                    ], repos=sourceRepos)

        try:
            # do the mirror
            self.outboundMirror()
            # compare
            self.compareRepositories(targetRepos1, targetRepos2,
                                     base='localhost.rpath.local2')

            troves = targetRepos1.getTroveVersionList('localhost.rpath.local2', {None:None})
            expectedTroves = {'group-test2': {versions.VersionFromString('/localhost.rpath.local2@rpl:devel/1.0-1-1'): [deps.deps.parseFlavor('')]}, 'test1:runtime': {versions.VersionFromString('/localhost.rpath.local2@rpl:devel/1.0-1-1'): [deps.deps.parseFlavor('')]}, 'test2:runtime': {versions.VersionFromString('/localhost.rpath.local2@rpl:devel/1.0-1-1'): [deps.deps.parseFlavor('')]}, 'test3:runtime': {versions.VersionFromString('/localhost.rpath.local2@rpl:other/1.0-1-1'): [deps.deps.parseFlavor('')]}, 'test5:runtime': {versions.VersionFromString('/localhost.rpath.local2@rpl:other/1.0-1-1'): [deps.deps.parseFlavor('')]}, 'group-test': {versions.VersionFromString('/localhost.rpath.local2@rpl:devel/1.0-1-1'): [deps.deps.parseFlavor('')]}, 'test6:runtime': {versions.VersionFromString('/localhost.rpath.local2@rpl:other/1.0-1-1'): [deps.deps.parseFlavor('')]}, 'test4:runtime': {versions.VersionFromString('/localhost.rpath.local2@rpl:other/1.0-1-1'): [deps.deps.parseFlavor('')]}}
            assert(troves == expectedTroves)

        finally:
            self.stopRepository(1)
            self.stopRepository(2)

if __name__ == "__main__":
    runTest = True
    testsuite.main()
