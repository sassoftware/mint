#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import testsuite
import time
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint.releasedata import RDT_STRING, RDT_BOOL, RDT_INT
from mint.releases import ReleaseDataNameError
from mint.mint_error import ReleasePublished, ReleaseMissing
from mint import releasetypes
from mint.database import ItemNotFound
from mint.mint_server import deriveBaseFunc

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

        desc = 'Just some random words'
        release.setDesc(desc)
        release.refresh()
        assert desc == release.getDesc()

    def testReleaseData(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")
        release = client.newRelease(projectId, "Test Release")

        release.setImageType(releasetypes.INSTALLABLE_ISO)

        rDict = release.getDataDict()
        tDict = release.getDataTemplate()
        for key in tDict:
            assert(tDict[key][1] == rDict[key])

        # test behavior of booleans
        for mediaCheck in (False, True):
            release.setDataValue('skipMediaCheck', mediaCheck)
            assert (mediaCheck == release.getDataValue('skipMediaCheck'))

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

    def testPublished(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")

        release.setImageType(releasetypes.STUB_IMAGE)
        release.setPublished(True)

        try:
            release.setDataValue('stringArg', 'bar')
            self.fail("Release allowed setting of release data after publish")
        except ReleasePublished:
            pass

        try:
            release.setImageType(releasetypes.STUB_IMAGE)
            self.fail("Release allowed setting of image type after publish")
        except ReleasePublished:
            pass

        try:
            release.setFiles(list())
            self.fail("Release allowed setting of files after publish")
        except ReleasePublished:
            pass

        try:
            release.setTrove('Some','Dummy','Args')
            self.fail("Release allowed setting of troves after publish")
        except ReleasePublished:
            pass

        try:
            release.setDesc('Not allowed')
            self.fail("Release allowed setting of troves after publish")
        except ReleasePublished:
            pass

        try:
            release.setPublished(True)
            self.fail("Release allowed altering published state after publish")
        except ReleasePublished:
            pass

        try:
            release.setPublished(False)
            self.fail("Release allowed altering published state after publish")
        except ReleasePublished:
            pass

        try:
            client.startImageJob(release.getId())
            self.fail("Allowed to start a job after release was published")
        except ReleasePublished:
            pass

    def testDeleteRelease(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")

        release.setImageType(releasetypes.STUB_IMAGE)
        release.setPublished(True)

        try:
            release.deleteRelease()
            self.fail("Release could be deleted after it was published")
        except ReleasePublished:
            pass

    def testMissingRelease(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        # make a release and delete it, to emulate a race condition
        # from the web UI
        release = client.newRelease(projectId, "Test Release")
        releaseId = release.getId()
        release.deleteRelease()
        
        # messing with that same release should now fail in a controlled
        # manner. no UnknownErrors allowed!
        try:
            release.setImageType(releasetypes.STUB_IMAGE)
            self.fail("Allowed to set imgage type of a deleted release")
        except ReleaseMissing:
            pass

        try:
            release.deleteRelease()
            self.fail("Allowed to delete a deleted release")
        except ReleaseMissing:
            pass

        # nasty hack. unwrap the release data value so that we can attack
        # codepaths not normally allowed by client code.
        setReleaseDataValue = deriveBaseFunc(self.mintServer.setReleaseDataValue)

        try:
            setReleaseDataValue(self.mintServer, releaseId, 'someKey', 'someVal', RDT_STRING)
            self.fail("Allowed to set data for a deleted release")
        except ReleaseMissing:
            pass

        try:
            release.setDesc('some string')
            self.fail("Allowed to set description for a deleted release")
        except ReleaseMissing:
            pass

        try:
            client.startImageJob(releaseId)
            self.fail("Allowed to start a job for a deleted release")
        except ReleaseMissing:
            pass

    def testDownloadIncrementing(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")

        assert(release.getDownloads() == 0)
        release.incDownloads()
        release.refresh()
        assert(release.getDownloads() == 1)

    def testUnfinishedRelease(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        brokenRelease = client.newRelease(projectId, "Test Release")
        brokenReleaseId = brokenRelease.getId()
        # because the first release is not yet finished, creating a new
        # release before finishing it should kill the first.
        release = client.newRelease(projectId, "Test Release")
        releaseId = brokenRelease.getId()

        # this if statement might look a little strange, but remember what's
        # actually happening: all unfinished releases are deleted THEN
        # the new one is made. because releaseId's are one-up the now-stale
        # brokenReleaseId should be re-used!

        if (releaseId != brokenReleaseId):
            self.fail("Previous unfinished releases should be removed!")

    def testReleaseStatus(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        release = client.newRelease(projectId, "Test Release")
        releaseId = release.getId()

        if client.server.getReleaseStatus(releaseId) != {'status': 5, 'message': 'No Job'}:
            self.fail("getReleaseStatus returned unknown values")

    def testReleaseList(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        adminClient, adminuserId = self.quickMintAdmin("adminauth", "adminpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")
        project2Id = client.newProject("Bar", "bar", "rpath.org")
        project3Id = adminClient.newProject("Hide", "hide", "rpath.org")
        adminClient.hideProject(project3Id)
        releasesToMake = [ (int(projectId), "foo", "Foo Unpublished"),
                           (int(project3Id), "hide", "Hide Release 1"),
                           (int(projectId), "foo", "Foo Release"),
                           (int(projectId), "foo", "Foo Release 2"),
                           (int(project2Id), "bar", "Bar Release"),
                           (int(project2Id), "bar", "Bar Release 2"),
                           (int(projectId), "foo", "Foo Release 3")]
        for projId, hostname, relName in releasesToMake:
            if "Hide" in relName:
                release = adminClient.newRelease(projId, relName)
            else:
                release = client.newRelease(projId, relName)
            release.setTrove("group-trove", "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
            if "Unpublished" not in relName:
                release.setPublished(True)
            time.sleep(1) # hack: let the timestamp increment since mysql doesn't do sub-second resolution 
        releaseList = client.server.getReleaseList(20, 0)
        releasesToMake.reverse()
        hostnames = [x[1] for x in releasesToMake]
        if len(releaseList) != 5:
            self.fail("getReleaseList returned the wrong number of results")
        for i in range(len(releaseList)):
            if tuple(releasesToMake[i]) != (releaseList[i][2].projectId, hostnames[i], releaseList[i][2].name):
                self.fail("Ordering of most recent releases is broken.")
            if releaseList[i][2].projectId == project3Id:
                self.fail("Should not have listed hidden release")

        for rel in client.server.getReleasesForProject(projectId):
            if rel.getId() not in (3, 4, 7):
                self.fail("getReleasesForProject returned incorrect results")

        try:
            client.server.getReleasesForProject(project3Id)
        except ItemNotFound, e:
            pass
        else:
            self.fail("getReleasesForProject returned hidden releases in non-admin context when it shouldn't have")

        rel = adminClient.server.getReleasesForProject(project3Id)
        if len(rel) != 1:
            self.fail("getReleasesForProject did not return hidden releases for admin")

if __name__ == "__main__":
    testsuite.main()
