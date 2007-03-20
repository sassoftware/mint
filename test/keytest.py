#!/usr/bin/python2.4
#
# Copyright (c) 2007 rPath, Inc.
#

import testsuite
testsuite.setup()

#from mint_rephelp import MintRepositoryHelper

from mint.distro import installable_iso

from conary import versions
from conary.deps import deps
from conary.lib import openpgpfile

TROVE_NAME = 'group-dummy'
TROVE_VERSION = versions.VersionFromString('/test.rpath.local@rpl:devel/1-1-1')
TROVE_FLAVOR = deps.parseFlavor('is: x86')

class DummyTroveInfo(object):
    def __init__(self):
        self.sigs = self
        self.digitalSigs = self

    def iter(self):
        for base in ('0123456789', '9876543210'):
            yield 4 * base

class DummyVersion(object):
    def __init__(self):
        self.v = self

    def trailingLabel(self):
        return 'test.rpath.local@rpl:devel'

class DummyTrove(object):
    def __init__(self):
        self.version = DummyVersion()
        self.troveInfo = DummyTroveInfo()

    def getName(self):
        return TROVE_NAME

    def getVersion(self):
        return TROVE_VERSION

    def getFlavor(self):
        return TROVE_FLAVOR

class DummyRepos(object):
    def findTrove(self, *args, **kwargs):
        raise NotImplementedError

    def getTrove(self, *args, **kwargs):
        return DummyTrove()

    def walkTroveSet(self, *args, **kwargs):
        yield DummyTrove()

    def getAsciiOpenPGPKey(self, label, fp):
        if fp == 4 * '0123456789':
            return ''
        raise openpgpfile.KeyNotFound(fp)

class DummyConfig(object):
    flavor = []

class DummyClient(object):
    def __init__(self):
        self.repos = DummyRepos()
        self.cfg = DummyConfig()

class DummyFlavor(object):
    def freeze(self):
        return '1#x86'

class DummyBuild(object):
    def getArchFlavor(self):
        return DummyFlavor()

class DummyIso(installable_iso.InstallableIso):
    def __init__(self):
        self.statusList = []
        self.conaryClient = DummyClient()
        self.build = DummyBuild()
        self.troveName = TROVE_NAME
        self.troveVersion = TROVE_VERSION
        self.troveFlavor = TROVE_FLAVOR

    def status(self, status):
        self.statusList.append(status)

    def getConaryClient(self, *args, **kwargs):
        return self.conaryClient

class KeyTest(testsuite.TestCase):
    def setUp(self):
        self._call = installable_iso.call
        installable_iso.call = lambda *args, **kwargs: None

    def tearDown(self):
        installable_iso.call = self._call

    def testNoTroves(self):
        DummyRepos.findTrove = lambda *args, **kwargs: []
        d = DummyIso()
        try:
            d.extractPublicKeys('', '')
        except RuntimeError, e:
            assert e.args ==  ("no match for group-dummy",)
        else:
            self.fail('expected RuntimeError')

    def testMultiTroves(self):
        DummyRepos.findTrove = lambda *args, **kwargs: ['1', '2']
        d = DummyIso()
        try:
            d.extractPublicKeys('', '')
        except RuntimeError, e:
            assert e.args ==  ("multiple matches for group-dummy",)
        else:
            self.fail('expected RuntimeError')

    def testMissingKey(self):
        DummyRepos.findTrove = lambda *args, **kwargs: (('', '', ''),)
        d = DummyIso()

        try:
            d.extractPublicKeys('', '')
        except RuntimeError, e:
            assert e.args == ('The following troves do not have keys in their '
                              'associated repositories:\ngroup-dummy='
                              '/test.rpath.local@rpl:devel/1-1-1[is: x86] '
                              'require 0\ngroup-dummy='
                              '/test.rpath.local@rpl:devel/1-1-1[is: x86] '
                              'require 9\n',)
        else:
            self.fail('expected RuntimeError')

    def testFoundAll(self):
        DummyRepos.findTrove = lambda *args, **kwargs: (('', '', ''),)
        d = DummyIso()

        getAsciiOpenPGPKey = DummyRepos.getAsciiOpenPGPKey
        try:
            DummyRepos.getAsciiOpenPGPKey = lambda *args : ''
            d.extractPublicKeys('', '')
        finally:
            DummyRepos.getAsciiOpenPGPKey = getAsciiOpenPGPKey

        assert d.statusList == ['Extracting Public Keys']


if __name__ == "__main__":
    testsuite.main()
