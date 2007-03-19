#!/usr/bin/python2.4
#
# Copyright (c) 2007 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper

from mint.distro import installable_iso

class DummyTrove(object):
    pass

class DummyRepos(object):
    def findTrove(self, *args, **kwargs):
        raise NotImplementedError

    def getTrove(self, *args, **kwargs):
        return DummyTrove()

    def walkTroveSet(self):
        raise NotImplementedError

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
        self.troveName = 'group-dummy'
        self.troveVersion = '/dummy@rpl:devel/1-1-1'
        self.troveFlavor = ''

    def status(self, status):
        self.statusList.append(status)

    def getConaryClient(self, *args, **kwargs):
        return self.conaryClient

class KeyTest(MintRepositoryHelper):
    def testNoTroves(self):
        DummyRepos.findTrove = lambda *args, **kwargs: []
        d = DummyIso()
        try:
            d.extractPublicKeys('', '')
        except RuntimeError, e:
            assert e.args ==  ("no match for group-dummy",)

    def testMultiTroves(self):
        DummyRepos.findTrove = lambda *args, **kwargs: ['1', '2']
        d = DummyIso()
        try:
            d.extractPublicKeys('', '')
        except RuntimeError, e:
            assert e.args ==  ("multiple matches for group-dummy",)

    def testMissingKey(self):
        raise testsuite.SkipTestException, "Test Not Finished"
        DummyRepos.findTrove = lambda *args, **kwargs: (('', '', ''),)
        d = DummyIso()
        try:
            import epdb
            epdb.st()
            d.extractPublicKeys('', '')

        except RuntimeError, e:
            assert e.args ==  ("multiple matches for group-dummy",)


if __name__ == "__main__":
    testsuite.main()
