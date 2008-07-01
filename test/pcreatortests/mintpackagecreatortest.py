#!/usr/bin/python2.4
#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

import sys
if '..' not in sys.path: sys.path.append('..')
import testsuite
testsuite.setup()
import unittest

import mint_rephelp

from conary_test import resources

import os
import shutil
import tempfile

import fixtures

from mint import packagecreator
from mint import config

from conary import conarycfg
from conary import changelog
from conary.lib import util

from factory_test import packagecreatortest

_envName = 'PACKAGE_CREATOR_SERVICE_PATH'
if _envName in os.environ:
    from pcreator import backend as pcreatorBackend
    from pcreator import factorydata as pcreatorFactoryData
    from pcreator import client as pcreatorClient

class mockfield(object):
    default = None


class TestPackageCreatorHelperMethods(testsuite.TestCase):
    @testsuite.context('more_cowbell')
    def testMinConfig(self):
        cfg = conarycfg.ConaryConfiguration(False)
        mincfg = packagecreator.MinimalConaryConfiguration(cfg)
        self.assertNotEquals(mincfg.lines, [])
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

    def testIsSelected(self):
        field = mockfield()
        self.failIf(packagecreator.isSelected(field, 'asdf', None))
        self.failUnless(packagecreator.isSelected(field, 'asdf', 'asdf'))
        field.default = 'asdf'
        self.failUnless(packagecreator.isSelected(field, 'asdf', None))
        self.failUnless(packagecreator.isSelected(field, 'asdf', 'asdf'))

    def testMinCfgMarshalling(self):
        cfg = conarycfg.ConaryConfiguration()
        cfg.contact = None
        mincfg = packagecreator.MinimalConaryConfiguration(cfg)
        self.assertEquals([x.split()[0] for x in mincfg.lines], ['contact'])
        self.assertEquals(mincfg.createConaryConfig().contact, '')

        # repeat with ''
        cfg.configLine('contact')
        mincfg = packagecreator.MinimalConaryConfiguration(cfg)
        self.assertEquals([x.split()[0] for x in mincfg.lines], ['contact'])
        self.assertEquals(mincfg.createConaryConfig().contact, '')

        cfg = mincfg.createConaryConfig()
        # instantiate a changelog object to ensure it won't backtrace
        changelog.ChangeLog(name = cfg.name, contact = cfg.contact,
                message = "doesn't matter\n")

    def testGetClientSwitch(self):
        cfg = config.MintConfig()
        self.shimClient = False
        self.networkedClient = False
        class DummyClient(object):
            def __init__(x, *args, **kwargs):
                self.assertEquals(args,
                        ('localhost', {'passwd': 'bar', 'user': 'foo'}))
                self.networkedClient = True

        class DummyShimClient(object):
            def __init__(x, *args, **kwargs):
                tmpDir = os.path.join(cfg.dataPath, 'tmp')
                self.assertEquals(args[0].storagePath, tmpDir)
                self.assertEquals(args[0].tmpFileStorage, tmpDir)
                self.assertEquals(args[1], {'passwd': 'bar', 'user': 'foo'})
                self.shimClient = True

        self.mock(pcreatorClient, 'PackageCreatorClient', DummyClient)
        self.mock(packagecreator, 'ShimClient', DummyShimClient)
        cfg.packageCreatorURL = None
        packagecreator.getPackageCreatorClient(cfg, ('foo', 'bar'))
        self.assertEquals(self.shimClient, True)
        cfg.packageCreatorURL = 'localhost'
        packagecreator.getPackageCreatorClient(cfg, ('foo', 'bar'))
        self.assertEquals(self.networkedClient, True)

class testPackageCreatorManipulation(packagecreatortest.RepoTest):
    def setUp(self):
        mint_rephelp._servers.stopAllServers()
        packagecreatortest.RepoTest.setUp(self)

    def tearDown(self):
        self.stopRepository(0)
        self.stopRepository(1)
        packagecreatortest.RepoTest.tearDown(self)

    def testgetFactoryDataFromDataDict(self):
        #create a pcreator client object
        #set up enough client to call getFactoryDataDefinition
        pClient = self.getPackageCreatorClient()
        mincfg = self._getMinimalFactoryConfig()
        sesH = pClient.startSession(self.productDefinitionDict, mincfg)
        rpmFileName = 'tags-1.2-3.noarch.rpm'
        rpmf = os.path.join(resources.factoryArchivePath, 'rpms',
                            rpmFileName)
        fileH = pClient.uploadData(sesH, file(rpmf))
        pClient.writeMetaFile(sesH, rpmFileName, "application/x-rpm")

        #This is throwaway, but you have to call it to cache the factory data
        #definitions
        pClient.getCandidateBuildFactories(sesH)

        foo = packagecreator.getFactoryDataFromDataDict(pClient, sesH,
            'rpm-redhat=/localhost1@pc:factory/1.0-1-1',
            packagecreatortest.expectedFactories1[0][3])
        self.assertEquals(foo.getvalue(), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<factoryData xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.org/permanent/factorydata-1.0.xsd factorydata-1.0.xsd">\n  <field>\n    <name>description</name>\n    <type>str</type>\n    <value>Some Description</value>\n  </field>\n  <field>\n    <name>version</name>\n    <type>str</type>\n    <value>1.2</value>\n  </field>\n  <field>\n    <name>name</name>\n    <type>str</type>\n    <value>tags</value>\n  </field>\n  <field>\n    <name>license</name>\n    <type>str</type>\n    <value>Some License</value>\n  </field>\n  <field>\n    <name>summary</name>\n    <type>str</type>\n    <value>Some Summary</value>\n  </field>\n</factoryData>\n')

if __name__ == '__main__':
    testsuite.main()
