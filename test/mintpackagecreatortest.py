#!/usr/bin/python2.4
#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

import testsuite
testsuite.setup()
import unittest

import os
import shutil
import tempfile

import fixtures

from mint import packagecreator

from conary import conarycfg
from conary.lib import util

_envName = 'PACKAGE_CREATOR_SERVICE_PATH'
if _envName in os.environ:
    from pcreator import backend as pcreatorBackend
    from pcreator import factorydata as pcreatorFactoryData
    _havePcreatorSchemas = True
else:
    _havePcreatorSchemas = False

class TestPackageCreator(unittest.TestCase):
    @testsuite.context('more_cowbell')
    def testMinConfig(self):
        cfg = conarycfg.ConaryConfiguration(False)
        mincfg = packagecreator.MinimalConaryConfiguration(cfg)
        self.assertEquals(mincfg.lines, [])
        cfg.configLine('repositoryMap foo http://foo/conary')
        cfg.configLine('user * foo bar')
        cfg.configLine('name bob')
        cfg.configLine('contact http://example')
        cfg.configLine('buildLabel foo@a:b')
        cfg.configLine('installLabelPath foo@a:b')
        cfg.configLine('searchPath foo@a:b')

        # define a value that is ignored by mincfg
        cfg.configLine('signatureKey badlabel bogusfingerprint')
        mincfg = packagecreator.MinimalConaryConfiguration(cfg)
        self.assertEquals(sorted(mincfg.lines),
                ['buildLabel                foo@a:b',
                 'contact                   http://example',
                 'installLabelPath          foo@a:b',
                 'name                      bob',
                 'repositoryMap             foo                       ' \
                         'http://foo/conary',
                 'searchPath                foo@a:b',
                 'user                      * foo bar'])
        cfg2 = mincfg.createConaryConfig()
        self.assertEquals(cfg2.name, cfg.name)
        self.assertEquals(cfg2.buildLabel, cfg.buildLabel)
        self.assertEquals(cfg2.contact, cfg.contact)
        self.assertEquals(cfg2.installLabelPath, cfg.installLabelPath)
        self.assertEquals(cfg2.repositoryMap, cfg.repositoryMap)
        self.assertEquals(cfg2.searchPath, cfg.searchPath)
        self.assertEquals(cfg2.user, cfg.user)
        self.assertEquals(cfg2.signatureKey, None)

class XmlRpcTest(fixtures.FixturedUnitTest):
    def setUp(self):
        fixtures.FixturedUnitTest.setUp(self)
        factdatapath = os.environ.get(_envName)
        if not factdatapath:
            raise testsuite.SkipTestException( \
                    "Please set PACKAGE_CREATOR_SERVICE_PATH")
        self._savedSchemaDir = pcreatorFactoryData.defaultSchemaDir
        pcreatorFactoryData.defaultSchemaDir = \
                os.path.join(factdatapath, 'data')

    def tearDown(self):
        pcreatorFactoryData.defaultSchemaDir = self._savedSchemaDir


    @testsuite.context('more_cowbell')
    @fixtures.fixture('Full')
    def testSession(self, db, data):
        # this is a complete end-to-end test of package creation at the xml-rpc
        # level.
        client = self.getClient('owner')
        projectId = data['projectId']
        sessionHandle = client.createPackageTmpDir()
        path = os.path.join(self.cfg.dataPath,
                'tmp', 'rb-pc-upload-' + sessionHandle)
        self.assertEquals(os.path.isdir(path), True)
        project = client.getProject(projectId)

        # this step sidesteps the file-uploader
        fd, tmpFile = tempfile.mkstemp()
        try:
            os.close(fd)
            shutil.copyfile(os.path.join(self.archiveDir,
                'foo-0.1-1.i386.rpm'), tmpFile)

            uploadfile = os.path.join(self.cfg.dataPath, 'tmp',
                    'rb-pc-upload-' + sessionHandle, 'uploadfile-index')
            util.mkdirChain(os.path.dirname(uploadfile))
            open(uploadfile, 'w').write('\n'.join(('tempfile=%s' % tmpFile,
                    'filename=foo.rpm', 'content-type=/xmime-trash')))
            factories = client.getPackageFactories(projectId, sessionHandle, 0, '', '')
            data = {'license': 'BSD',
                    'name': 'foo',
                    'version': '0.1',
                    'summary': '',
                    'description': ''}
            factoryHandle = factories[0][0]
            client.savePackage(sessionHandle, factoryHandle, data)
        finally:
            util.rmtree(tmpFile, ignore_errors = True)

        
        import epdb; epdb.st()


if __name__ == '__main__':
    testsuite.main()
