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
from conary import changelog
from conary.lib import util

_envName = 'PACKAGE_CREATOR_SERVICE_PATH'
if _envName in os.environ:
    from pcreator import backend as pcreatorBackend
    from pcreator import factorydata as pcreatorFactoryData

class mockfield(object):
    default = None


class TestPackageCreatorHelperMethods(unittest.TestCase):
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


if __name__ == '__main__':
    testsuite.main()
