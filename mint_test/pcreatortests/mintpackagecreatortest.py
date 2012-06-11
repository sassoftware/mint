#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

import testsetup

from testrunner import pathManager

import os
import shutil
import tempfile

from mint_test import fixtures

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
    from pcreator import errors as pcreatorErrors

class mockfield(object):
    name='foo'
    default = None


class TestPackageCreatorHelperMethods(testsetup.testsuite.TestCase):
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
        self.failIf(packagecreator.isSelected(field, 'asdf', None, {}))
        self.failUnless(packagecreator.isSelected(field, 'asdf', 'asdf', {}))
        field.default = 'asdf'
        self.failUnless(packagecreator.isSelected(field, 'asdf', None, {}))
        self.failUnless(packagecreator.isSelected(field, 'asdf', 'asdf', {}))

        #Now for preexisting values
        field.default = None
        self.failIf(packagecreator.isSelected(field, 'asdf', None, {field.name: ('asdf', False)}))
        self.failUnless(packagecreator.isSelected(field, 'asdf1', 'asdf1', {field.name: ('asdf', False)}))
        self.failUnless(packagecreator.isSelected(field, 'asdf', None, {field.name: ('asdf', True)}))
        self.failIf(packagecreator.isSelected(field, 'asdf', 'asdf', {field.name: ('asdf1', True)}))

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
        cfg.namespace = 'yournamespace'
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

#This may need to be reordered if the factory definition changes
generatedXML = """<?xml version='1.0' encoding='UTF-8'?>
<factoryData xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.org/permanent/factorydata-1.0.xsd factorydata-1.0.xsd">
  <field>
    <name>name</name>
    <type>str</type>
    <value>tags</value>
    <modified>true</modified>
  </field>
  <field>
    <name>version</name>
    <type>str</type>
    <value>1.2</value>
    <modified>true</modified>
  </field>
  <field>
    <name>license</name>
    <type>str</type>
    <value>Some License</value>
    <modified>true</modified>
  </field>
  <field>
    <name>summary</name>
    <type>str</type>
    <value>Some Summary</value>
    <modified>true</modified>
  </field>
  <field>
    <name>description</name>
    <type>str</type>
    <value>Some Description</value>
    <modified>true</modified>
  </field>
</factoryData>
"""

# this data set is for attempting to upload a trove with an empty name
xmlDataEmptyName = """<?xml version='1.0' encoding='UTF-8'?>
<factoryData xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.rpath.org/permanent/factorydata-1.0.xsd factorydata-1.0.xsd">
  <field>
    <name>name</name>
    <type>str</type>
    <value />
    <modified>true</modified>
  </field>
  <field>
    <name>version</name>
    <type>str</type>
    <value>1.2</value>
    <modified>true</modified>
  </field>
  <field>
    <name>license</name>
    <type>str</type>
    <value>Some License</value>
    <modified>true</modified>
  </field>
  <field>
    <name>summary</name>
    <type>str</type>
    <value>Some Summary</value>
    <modified>true</modified>
  </field>
  <field>
    <name>description</name>
    <type>str</type>
    <value>Some Description</value>
    <modified>true</modified>
  </field>
</factoryData>
"""

class testPackageCreatorManipulation(packagecreatortest.RepoTest):
    def testgetFactoryDataFromDataDict(self):
        #create a pcreator client object
        #set up enough client to call getFactoryDataDefinition
        pClient = self.getPackageCreatorClient()
        mincfg = self._getMinimalFactoryConfig()
        sesH = pClient.startSession(self.productDefinitionDict, mincfg)
        rpmFileName = 'tags-1.2-3.noarch.rpm'
        rpmf = os.path.join(pathManager.getPath('PACKAGE_CREATOR_SERVICE_ARCHIVE_PATH'), 'rpms',
                            rpmFileName)
        pClient.uploadData(sesH, rpmFileName, file(rpmf), "application/x-rpm")

        #This is throwaway, but you have to call it to cache the factory data
        #definitions
        pClient.getCandidateBuildFactories(sesH)

        foo = packagecreator.getFactoryDataFromDataDict(pClient, sesH,
            'rpm-redhat=/localhost1@pc:factory/1.0-1-1',
            packagecreatortest.expectedFactories1[0][3])
        self.assertEquals(foo.getvalue(), generatedXML)

        rpmFileName = 'foo-0.3-1.noarch.rpm'
        rpmf = os.path.join(pathManager.getPath('PACKAGE_CREATOR_SERVICE_ARCHIVE_PATH'), 'rpms',
                            rpmFileName)
        pClient.uploadData(sesH, rpmFileName, file(rpmf), "application/x-rpm")
        self.assertEquals(sorted(pClient.server._server._getSessionValue( \
                sesH, 'currentFiles').keys()),
                ['foo-0.3-1.noarch.rpm', 'tags-1.2-3.noarch.rpm'])

    def testEmptyName(self):
        #create a pcreator client object
        #set up enough client to call getFactoryDataDefinition
        pClient = self.getPackageCreatorClient()
        mincfg = self._getMinimalFactoryConfig()
        sesH = pClient.startSession(self.productDefinitionDict, mincfg)
        rpmFileName = 'tags-1.2-3.noarch.rpm'
        rpmf = os.path.join(pathManager.getPath('PACKAGE_CREATOR_SERVICE_ARCHIVE_PATH'), 'rpms',
                            rpmFileName)
        pClient.uploadData(sesH, rpmFileName, file(rpmf), "application/x-rpm")

        #This is throwaway, but you have to call it to cache the factory data
        #definitions
        res = pClient.getCandidateBuildFactories(sesH)

        self.failUnless(res, "no results from repo")
        # fatory-rpm validates the empty name, factory-rpm-suse does not.
        # both cases should trigger an error
        for factFingerprint, refData in (('rpm=',
                (["'Package name': '' fails regexp check '^[\\w\\.\\-]+$'"],)),
                ('rpm-suse=', (['Package name cannot be empty'],))):
            # attempt to make the trove, but leave the name field empty
            factH = [x[0] for x in res if x[0].startswith(factFingerprint)][0]

            err = self.assertRaises(pcreatorErrors.ConstraintsValidationError,
                    pClient.makeSourceTrove, sesH, factH, xmlDataEmptyName)
            self.assertEquals(err.args, refData)


if __name__ == '__main__':
    testsetup.testsuite.main()
