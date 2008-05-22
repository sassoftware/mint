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

class XmlRpcTest(mint_rephelp.WebRepositoryHelper, packagecreatortest.BaseTest):
    def setUp(self):
        factdatapath = os.environ.get(_envName)
        if not factdatapath:
            raise testsuite.SkipTestException( \
                    "Please set PACKAGE_CREATOR_SERVICE_PATH")

#        #Set up two products
#        self.client, userID = self.quickMintUser('testuser', 'testpass')
#
#        self.prodId1 = self.newProject(self.client, 'Factories', 'factories',
#            mint_rephelp.MINT_PROJECT_DOMAIN)
#        self.prodId1 = self.newProject(self.client, 'Product', 'product',
#            mint_rephelp.MINT_PROJECT_DOMAIN)
#
#        #Add factories and a factory group to the factories repository
#
#        #Add a version to the product repository

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
            factories = client.getPackageFactories(projectId, sessionHandle, 1, '')
            factoryHandle = factories[0][0]
            factoryPrefilledData = factories[0][2]
            client.savePackage(sessionHandle, factoryHandle, factoryPrefilledData)
        finally:
            util.rmtree(tmpFile, ignore_errors = True)

        
if __name__ == '__main__':
    testsuite.main()
