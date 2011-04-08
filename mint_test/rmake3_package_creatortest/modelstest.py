#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

import os
import tempfile

import testsetup
from testrunner import testcase

from conary import conarycfg

from mint.rmake3_package_creator import models

class ModelsTest(testcase.TestCaseWithWorkDir):
    def _getConaryConfig(self):
        cfg = conarycfg.ConaryConfiguration(False)
        cfg.configLine('repositoryMap foo http://foo/conary')
        cfg.configLine('user * foo bar')
        cfg.configLine('name bob')
        cfg.configLine('contact http://example')
        cfg.configLine('buildLabel foo@a:b')
        cfg.configLine('installLabelPath foo@a:b')
        cfg.configLine('searchPath foo@a:b')

        # define a value that is ignored by mincfg
        cfg.configLine('signatureKey badlabel bogusfingerprint')
        return cfg

    def testMinConfig(self):
        cfg = self._getConaryConfig()
        mincfg = models.MinimalConaryConfiguration.fromConaryConfig(cfg)
        cfg2 = mincfg.createConaryConfig()
        self.assertEquals(cfg2.name, cfg.name)
        self.assertEquals(cfg2.buildLabel, cfg.buildLabel)
        self.assertEquals(cfg2.contact, cfg.contact)
        self.assertEquals(cfg2.installLabelPath, cfg.installLabelPath)
        self.assertEquals(cfg2.repositoryMap, cfg.repositoryMap)
        self.assertEquals(cfg2.searchPath, cfg.searchPath)
        self.assertEquals(cfg2.user, cfg.user)
        self.assertEquals(cfg2.signatureKey, None)

        # Make sure we get the same on-disk representation
        tf1 = tempfile.NamedTemporaryFile()
        cfg.writeToFile(tf1.name)

        # Add signatureKey back to cfg2, so we can easily compare
        cfg2.configLine('signatureKey badlabel bogusfingerprint')

        tf2 = tempfile.NamedTemporaryFile()
        cfg2.writeToFile(tf2.name)

        tf1.seek(0)
        tf2.seek(0)
        self.failUnlessEqual(tf1.read(), tf2.read())

        f = mincfg.freeze()

    def testImmutableTypes(self):
        origList = [ 1, 2, 3]
        l = models.ImmutableList(origList)
        newl = l.freeze().thaw()
        self.failUnlessEqual([ x for x in newl ], origList)

    def testPackageSourceCommitParams(self):
        file1Name = 'file1.txt'
        file1 = models.File(name=file1Name, path=os.path.join(self.workDir,
            file1Name))

        label = 'wafer.rdu.rpath.com@rpath:wafer-1-devel'
        cfg = self._getConaryConfig()
        mincfg = models.MinimalConaryConfiguration.fromConaryConfig(cfg)
        sourceData = models.SourceData(name='testee',
            label=label, version='1.0',
            fileList=models.ImmutableList([ file1 ]),
            factory='capsule-rpm-pc=/centos.rpath.com@rpath:centos-5-common/1.0-1-1',
            stageLabel=label, commitMessage="Committing",
        )
        data = models.PackageSourceCommitParams(mincfg=mincfg,
            sourceData=sourceData)
        frozen = data.freeze()
        newdata = frozen.thaw()

    def testCreateChangeSet(self):
        # XXX this test should be in a different file
        label = 'wafer.rdu.rpath.com@rpath:wafer-1-devel'
        factory = 'capsule-rpm-pc=/centos.rpath.com@rpath:centos-5-common/1.0-1-1'
        commitMsg = 'Committing\n'

        file1Name = 'file1.txt'
        file2Name = 'file2.txt'
        file3Name = 'file3.txt'
        file1 = models.File(name=file1Name,
            path=os.path.join(self.workDir, file1Name))
        file(file1.path, "w").write("contents 1 from file")
        file2 = models.File(name=file2Name, contents="contents 2",
            isConfig=True)
        # file3 has both content and path, make sure only one is used
        file3 = models.File(name=file3Name, contents="contents 3",
            path=os.path.join(self.workDir, file3Name))
        cfg = self._getConaryConfig()
        mincfg = models.MinimalConaryConfiguration.fromConaryConfig(cfg)

        pdl = models.ProductDefinitionLocation(hostname='wafer.rdu.rpath.com',
            shortname='wafer', namespace='rpath', version='1')

        sourceData = models.SourceData(name='testee',
            label=label, version='1.0',
            productDefinitionLocation=pdl,
            fileList=models.ImmutableList([ file1, file2, file3 ]),
            factory=factory,
            stageLabel=label, commitMessage=commitMsg,
        )

        class MockClient(object):
            def createSourceTrove(self, name, label, upstreamVersion,
                                pathDict, changeLog, factory = None,
                                pkgCreatorData = None):
                self.name = name
                self.label = label
                self.upstreamVersion = upstreamVersion
                self.pathDict = pathDict
                self.changeLog = changeLog
                self.factory = factory
                self.pkgCreatorData = pkgCreatorData
                return "changeset"

        client = MockClient()

        from mint.rmake3_package_creator import task
        cs = task.TaskCommitSource.createChangeSet(client, cfg, sourceData)
        self.failUnlessEqual(cs, "changeset")

        self.failUnlessEqual(client.name, 'testee')
        self.failUnlessEqual(client.label, label)
        self.failUnlessEqual(client.upstreamVersion, '1.0')
        self.failUnlessEqual(client.factory, factory)
        self.failUnlessEqual(
            sorted([ (x, self._getContents(y.contents), y.config)
                for (x, y) in client.pathDict.items() ]),
            [
                ('file1.txt', 'contents 1 from file', False),
                ('file2.txt', 'contents 2', True),
                ('file3.txt', 'contents 3', False),
            ])
        self.failUnlessEqual(client.changeLog.name(), 'bob')
        self.failUnlessEqual(client.changeLog.contact(), 'http://example')
        self.failUnlessEqual(client.changeLog.message(), commitMsg)

    @classmethod
    def _getContents(cls, contents):
        if hasattr(contents, 'f'):
            return contents.f.read()
        return contents.str

if __name__ == '__main__':
    testsetup.testsuite.main()
