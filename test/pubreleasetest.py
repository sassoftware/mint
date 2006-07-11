#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

import time

import fixtures
from mint_rephelp import MINT_HOST, MINT_DOMAIN, MINT_PROJECT_DOMAIN

from mint import buildtypes
from mint import pubreleases
from mint.mint_error import PermissionDenied, BuildPublished, BuildMissing, BuildEmpty
from mint.database import ItemNotFound

class PublishedReleaseTest(fixtures.FixturedUnitTest):

    @fixtures.fixture("Full")
    def testPublishedReleaseCreation(self, db, data):

        # The full fixture actually creates a published release; we'll
        # use this already created object as a starting point.
        client = self.getClient("owner")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        pubReleaseId = pubRelease.id
        self.failUnless(pubRelease.id == pubRelease.pubReleaseId,
                "id and pubReleaseId should be identical")

        # check the timeCreated and createdBy fields
        # fixture creates the published release using the owner's id
        self.failUnless(pubRelease.timeCreated > 0, "timeCreated not set")
        self.failUnless(pubRelease.createdBy == data['owner'])

    @fixtures.fixture("Full")
    def testAddBuildToPublishedRelease(self, db, data):

        client = self.getClient("owner")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        project = client.getProject(data['projectId'])
        build = client.getBuild(data['buildId'])
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setFiles([["file", "file title 1"]])

        # sanity checks
        self.failIf(data['buildId'] in pubRelease.getBuilds(),
                "Build is not published yet")
        self.failUnless(data['buildId'] in project.getUnpublishedBuilds(),
                "Build should be in the unpublished list")

        # publish it now
        pubRelease.addBuild(build.id)

        # check the state of the world after publishing
        self.failUnless(data['buildId'] in pubRelease.getBuilds(),
                "Build was not properly added to published releases")
        self.failIf(data['buildId'] in project.getUnpublishedBuilds(),
                "Build should no longer be considered unpublished")

    @fixtures.fixture("Full")
    def testRemoveBuildFromPublishedRelease(self, db, data):
        client = self.getClient("owner")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        project = client.getProject(data['projectId'])

        # sanity checks
        self.failUnless(data['pubBuildId'] in pubRelease.getBuilds(),
                "Build should be published before beginning")
        self.failIf(data['pubBuildId'] in project.getUnpublishedBuilds(),
                "Build should not be in the unpublished list")

        # unpublish it now
        pubRelease.removeBuild(data['pubBuildId'])

        # check the state of the world after publishing
        self.failIf(data['buildId'] in pubRelease.getBuilds(),
                "Build was not removed from published releases")
        self.failUnless(data['buildId'] in project.getUnpublishedBuilds(),
                "Build should be considered unpublished")

    @fixtures.fixture("Full")
    def testUpdatePublishedRelease(self, db, data):

        releaseName = "My new release"
        releaseDescription = "My pithy description"

        client = self.getClient("owner")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])

        # set some things
        pubRelease.name = releaseName
        pubRelease.description = releaseDescription
        self.failUnless(pubRelease.name == releaseName)
        self.failUnless(pubRelease.description == releaseDescription)
        self.failIf(pubRelease.timeUpdated, "timeUpdated should not be set")
        self.failIf(pubRelease.updatedBy, "updatedBy should not be set")

        # now save to the database
        pubRelease.save()

        # forget about it
        del pubRelease

        # retrieve it from the database, again
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])

        # check to make sure things are still set
        self.failUnless(pubRelease.name == releaseName)
        self.failUnless(pubRelease.description == releaseDescription)

        # check update fields
        self.failUnless(pubRelease.timeUpdated > 0, "timeUpdated not set")
        self.failUnless(pubRelease.updatedBy == data['owner'], "updatedBy should be set, now")

    @fixtures.fixture("Full")
    def testIsBuildPublished(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])
        pubBuild = client.getBuild(data['pubBuildId'])

        self.failIf(build.getPublished(), "Release should be published")
        self.failUnless(pubBuild.getPublished(), "Release should not be published")

    @fixtures.fixture("Full")
    def testGetPublishedReleasesByProject(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        self.failUnlessEqual(project.getPublishedReleases(), [ data['pubReleaseId'] ])

    @fixtures.fixture("Full")
    def testGetUnpublishedBuildsByProject(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        self.failUnlessEqual(project.getUnpublishedBuilds(), [ data['buildId'] ])

    @fixtures.fixture("Full")
    def testDeletePublishedRelease(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        client.deletePublishedRelease(data['pubReleaseId'])

        self.failUnlessEqual(project.getPublishedReleases(), [],
                "There should be no published releases in the project")

        self.failUnless(data['pubBuildId'] in project.getUnpublishedBuilds(),
                "Previously published builds should now be unpublished")

        build = client.getBuild(data['pubBuildId'])

        self.failIf(build.getPublished(), "Build still shows up as published")

    @fixtures.fixture("Full")
    def testFinalizePublishedRelease(self, db, data):
        client = self.getClient("owner")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])

        self.failIf(pubRelease.timePublished,
                "Release should not be published yet")
        self.failIf(pubRelease.publishedBy,
                "Release should not be published yet")

        pubRelease.finalize()
        pubRelease.refresh()

        self.assertAlmostEqual(pubRelease.timePublished, time.time(), 1,
                "Release should be published now")
        self.failUnlessEqual(pubRelease.publishedBy, data['owner'],
                "Release wasn't marked with the appropriate publisher")
        self.failUnless(pubRelease.isFinalized())

    @fixtures.fixture("Full")
    def testPublishEmptyBuild(self, db, data):
        client = self.getClient("owner")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        self.assertRaises(BuildEmpty,
                pubRelease.addBuild, data['buildId'])

    @fixtures.fixture("Full")
    def testDeleteBuildFromPublishedRelease(self, db, data):
        client = self.getClient("owner")
        pubBuild = client.getBuild(data['pubBuildId'])
        pubBuild.deleteBuild()

    @fixtures.fixture("Full")
    def testDeleteBuildFromFinalizedPublishedRelease(self, db, data):
        client = self.getClient("owner")
        pubBuild = client.getBuild(data['pubBuildId'])
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        pubRelease.finalize()
        self.assertRaises(BuildPublished, pubBuild.deleteBuild)

    @fixtures.fixture("Full")
    def testPublishedReleaseAccessCreate(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (True, None),
                 'developer': (False, PermissionDenied),
                 'user': (False, PermissionDenied),
                 'nobody': (False, PermissionDenied),
                 'anonymous': (False, PermissionDenied) }

        for (user, (allowed, exc)) in acls.items():
            client = self.getClient(user)

            if allowed:
                newPublishedRelease = client.newPublishedRelease(data['projectId'])
                self.failUnlessEqual(newPublishedRelease.createdBy,
                        data[user])
            else:
                self.assertRaises(exc,
                        client.newPublishedRelease, data['projectId'])

    @fixtures.fixture("Full")
    def testPublishedReleaseAccessCreateInHidden(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (True, None),
                 'developer': (False, PermissionDenied),
                 'user': (False, ItemNotFound),
                 'nobody': (False, ItemNotFound),
                 'anonymous': (False, PermissionDenied) }

        # make a project hidden
        adminClient = self.getClient("admin")
        adminClient.hideProject(data['projectId'])

        for (user, (allowed, exc)) in acls.items():
            client = self.getClient(user)

            if allowed:
                newPublishedRelease = client.newPublishedRelease(data['projectId'])
                self.failUnlessEqual(newPublishedRelease.createdBy,
                        data[user])
            else:
                self.assertRaises(exc,
                        client.newPublishedRelease, data['projectId'])

    @fixtures.fixture("Full")
    def testPublishedReleaseAccessGetNonPublic(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (True, None),
                 'developer': (True, None),
                 'user': (False, ItemNotFound),
                 'nobody': (False, ItemNotFound),
                 'anonymous': (False, ItemNotFound) }

        for (user, (allowed, exc)) in acls.items():
            client = self.getClient(user)

            if allowed:
                pubRelease = client.getPublishedRelease(data['pubReleaseId'])
                self.failUnlessEqual(pubRelease.id, data['pubReleaseId'])
            else:
                self.assertRaises(exc,
                        client.getPublishedRelease, data['pubReleaseId'])

    @fixtures.fixture("Full")
    def testPublishedReleaseAccessGetPublic(self, db, data):

        # this function should allow all users
        users = [ "admin", "owner", "developer",
                  "user", "nobody", "anonymous"]

        for user in users:
            # finalize the release before testing
            adminClient = self.getClient("admin")
            newBuild = adminClient.newBuild(data['projectId'],
                    "Test Published Build")
            newBuild.setBuildType(buildtypes.STUB_IMAGE)
            newBuild.setFiles([["file", "file title 1"]])
            newBuild.setTrove("group-dist", "/testproject." + \
                    MINT_PROJECT_DOMAIN + "@rpl:devel/1.0-2-1", "1#x86")
            newPubRelease = adminClient.newPublishedRelease(data['projectId'])
            newPubRelease.addBuild(newBuild.id)
            newPubRelease.finalize()

            client = self.getClient(user)
            userPubRelease = client.getPublishedRelease(newPubRelease.id)
            self.failUnlessEqual(newPubRelease.id, userPubRelease.id)

    @fixtures.fixture("Full")
    def testPublishedReleaseAccessCreateWithinOtherProject(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (False, PermissionDenied),
                 'developer': (False, PermissionDenied),
                 'user': (False, PermissionDenied),
                 'nobody': (False, PermissionDenied),
                 'anonymous': (False, PermissionDenied)}

        # create an unrelated project using a seperate admin client
        adminClient = self.getClient("admin")
        otherProjectId = adminClient.newProject('Quux', 'quux', 'rpath.org')

        for (user, (allowed, exc)) in acls.items():
            client = self.getClient(user)

            if allowed:
                newPublishedRelease = \
                    client.newPublishedRelease(otherProjectId)
                self.failUnlessEqual(newPublishedRelease.createdBy,
                        data[user])
            else:
                self.assertRaises(exc,
                        client.newPublishedRelease, otherProjectId)


    @fixtures.fixture("Full")
    def testPublishedReleaseAccessAddBuild(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (True, None),
                 'developer': (False, PermissionDenied) }

        for (user, (allowed, exc)) in acls.items():
            adminClient = self.getClient("admin")
            newBuild = adminClient.newBuild(data['projectId'],
                    "Test Published Build")
            newBuild.setBuildType(buildtypes.STUB_IMAGE)
            newBuild.setFiles([["file", "file title 1"]])
            newBuild.setTrove("group-dist", "/testproject." + \
                    MINT_PROJECT_DOMAIN + "@rpl:devel/1.0-2-1", "1#x86")
            newPubRelease = adminClient.newPublishedRelease(data['projectId'])

            client = self.getClient(user)
            userPubRelease = client.getPublishedRelease(newPubRelease.id)

            if allowed:
                userPubRelease.addBuild(newBuild.id)
            else:
                self.assertRaises(exc,
                        userPubRelease.addBuild, newBuild.id)


    @fixtures.fixture("Full")
    def testPublishedReleaseAccessRemoveBuild(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (True, None),
                 'developer': (False, PermissionDenied) }

        for (user, (allowed, exc)) in acls.items():
            adminClient = self.getClient("admin")
            newBuild = adminClient.newBuild(data['projectId'],
                    "Test Published Build")
            newBuild.setBuildType(buildtypes.STUB_IMAGE)
            newBuild.setFiles([["file", "file title 1"]])
            newBuild.setTrove("group-dist", "/testproject." + \
                    MINT_PROJECT_DOMAIN + "@rpl:devel/1.0-2-1", "1#x86")
            newPubRelease = adminClient.newPublishedRelease(data['projectId'])
            newPubRelease.addBuild(newBuild.id)

            client = self.getClient(user)
            userPubRelease = client.getPublishedRelease(newPubRelease.id)

            if allowed:
                userPubRelease.removeBuild(newBuild.id)
            else:
                self.assertRaises(exc,
                        userPubRelease.removeBuild, newBuild.id)


    @fixtures.fixture("Full")
    def testPublishedReleaseAccessDelete(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (True, None),
                 'developer': (False, PermissionDenied),
                 'user': (False, ItemNotFound),
                 'nobody': (False, ItemNotFound),
                 'anonymous': (False, PermissionDenied) }

        for (user, (allowed, exc)) in acls.items():

            adminClient = self.getClient("admin")
            newPubRelease = adminClient.newPublishedRelease(data['projectId'])

            client = self.getClient(user)

            if allowed:
                client.deletePublishedRelease(newPubRelease.id)
            else:
                self.assertRaises(exc,
                        client.deletePublishedRelease, newPubRelease.id)

    @fixtures.fixture("Full")
    def testPublishedReleaseAccessDeleteFinalized(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (True, None),
                 'developer': (False, PermissionDenied),
                 'user': (False, PermissionDenied),
                 'nobody': (False, PermissionDenied),
                 'anonymous': (False, PermissionDenied)}

        for (user, (allowed, exc)) in acls.items():
            adminClient = self.getClient("admin")
            newPubRelease = adminClient.newPublishedRelease(data['projectId'])
            newBuild = adminClient.newBuild(data['projectId'],
                    "Test Published Build")
            newBuild.setBuildType(buildtypes.STUB_IMAGE)
            newBuild.setFiles([["file", "file title 1"]])
            newBuild.setTrove("group-dist", "/testproject." + \
                    MINT_PROJECT_DOMAIN + "@rpl:devel/1.0-2-1", "1#x86")
            newPubRelease.addBuild(newBuild.id)
            newPubRelease.finalize()

            client = self.getClient(user)
            userPubRelease = client.getPublishedRelease(newPubRelease.id)

            if allowed:
                client.deletePublishedRelease(newPubRelease.id)
            else:
                self.assertRaises(exc,
                        client.deletePublishedRelease, newPubRelease.id)


    # XXX this probably needs to be getPublishedReleases, now
    # TODO rework me completely
    @fixtures.fixture("Full")
    def testPublishedReleasesList(self, db, data):
        #client, userId = self.quickMintUser("testuser", "testpass")
        #adminClient, adminuserId = self.quickMintAdmin("adminauth", "adminpass")
        raise testsuite.SkipTestException

        client = self.getClient("owner")
        adminClient = self.getClient("admin")
        projectId = client.newProject("Foo", "foo", "rpath.org")
        project2Id = client.newProject("Bar", "bar", "rpath.org")
        project3Id = adminClient.newProject("Hide", "hide", "rpath.org")
        adminClient.hideProject(project3Id)
        buildsToMake = [ (int(projectId), "foo", "Foo Unpublished"),
                           (int(project3Id), "hide", "Hide Build 1"),
                           (int(projectId), "foo", "Foo Build"),
                           (int(projectId), "foo", "Foo Build 2"),
                           (int(project2Id), "bar", "Bar Build"),
                           (int(project2Id), "bar", "Bar Build 2"),
                           (int(projectId), "foo", "Foo Build 3")]
        for projId, hostname, relName in buildsToMake:
            if "Hide" in relName:
                build = adminClient.newBuild(projId, relName)
            else:
                build = client.newBuild(projId, relName)
            build.setTrove("group-trove", "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
            if "Unpublished" not in relName:
                build.setFiles([["file1", "File Title 1"]])
                build.setPublished(True)
                pubRelease = client.newPublishedRelease()
                pubRelease.addBuild(build.id)
                pubRelease.save()
            time.sleep(1) # hack: let the timestamp increment since mysql doesn't do sub-second resolution
        buildList = client.getBuildList(20, 0)
        buildsToMake.reverse()
        hostnames = [x[1] for x in buildsToMake]
        if len(buildList) != 5:
            self.fail("getBuildList returned the wrong number of results")
        for i in range(len(buildList)):
            if tuple(buildsToMake[i]) != (buildList[i][2].projectId, hostnames[i], buildList[i][2].name):
                self.fail("Ordering of most recent builds is broken.")
            if buildList[i][2].projectId == project3Id:
                self.fail("Should not have listed hidden build")

        project = client.getProject(projectId)
        for rel in project.getBuilds():
            if rel.getId() not in (3, 4, 7):
                self.fail("getBuildsForProject returned incorrect results")

        try:
            client.server.getBuildsForProject(project3Id)
        except ItemNotFound, e:
            pass
        else:
            self.fail("getBuildsForProject returned hidden builds in non-admin context when it shouldn't have")

        project = adminClient.getProject(project3Id)
        rel = project.getBuilds()
        if len(rel) != 1:
            self.fail("getBuildsForProject did not return hidden builds for admin")


if __name__ == "__main__":
    testsuite.main()
