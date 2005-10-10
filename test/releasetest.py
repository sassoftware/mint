#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint.releasedata import RDT_STRING, RDT_BOOL, RDT_INT
from mint.releases import ReleaseDataNameError
from mint import releasetypes

class ReleaseTest(MintRepositoryHelper):
    def testBasicAttributes(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")
        assert(release.getName() == "Test Release")
        release.setTrove("group-trove", "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        assert(release.getTrove() ==\
            ('group-trove', '/conary.rpath.com@rpl:devel/0.0:1.0-1-1', '1#x86'))
        assert(release.getTroveName() == 'group-trove')
        assert(release.getTroveVersion().asString() == '/conary.rpath.com@rpl:devel/1.0-1-1')
        assert(release.getTroveFlavor().freeze() == '1#x86')
        assert(release.getArch() == "x86")

        release.setFiles([("file1", "File Title 1"), ("file2", "File Title 2")])
        assert(release.getFiles() ==\
            [(1, 'file1', 'File Title 1'), (2, 'file2', 'File Title 2')])


    def testReleaseData(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")
        release = client.newRelease(projectId, "Test Release")

        release.setImageType(releasetypes.INSTALLABLE_ISO)

        #print repr(release.getDataDict())
        assert(release.getDataDict() == {'skipMediaCheck': False, 'betaNag': False})

        # test behavior of booleans
        for mediaCheck in (False, True):
            release.setDataValue('skipMediaCheck', mediaCheck)
            assert (mediaCheck == release.getDataValue('skipMediaCheck'))

        assert(release.getDataDict() ==
               {'skipMediaCheck': True, 'betaNag': False})

        # test bad name lockdown
        try:
            release.getDataValue('undefinedName')
            self.fail("release allowed releaseData name not in template to be set: undefinedName")
        except ReleaseDataNameError:
            pass

        release.setImageType(releasetypes.STUB_IMAGE)

        # test string behavior
        release.setDataValue('stringArg', 'foo')
        assert('foo' == release.getDataValue('stringArg'))
        release.setDataValue('stringArg', 'bar')
        assert('bar' == release.getDataValue('stringArg'))

        # test int behavior
        for intArg in range(0,3):
            release.setDataValue('intArg', intArg)
            assert(intArg == release.getDataValue('intArg'))

    def testDownloadIncrementing(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")

        assert(release.getDownloads() == 0)
        release.incDownloads()
        release.refresh()
        assert(release.getDownloads() == 1)


if __name__ == "__main__":
    testsuite.main()
