#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#


import time

import fixtures
from mint_rephelp import MINT_PROJECT_DOMAIN

from mint import buildtypes
from mint.mint_error import *

from conary import versions
from conary.conaryclient import ConaryClient

class PublishedReleaseTest(fixtures.FixturedUnitTest):
    @testsuite.context("quick")
    @fixtures.fixture("Full")
    def testPublishedReleaseCreation(self, db, data):

        # The full fixture actually creates a published release; we'll
        # use this already created object as a starting point.
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
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
        build = client.getBuild(data['anotherBuildId'])

        # sanity checks
        self.failIf(data['anotherBuildId'] in pubRelease.getBuilds(),
                "Build is not published yet")
        self.failUnless(data['anotherBuildId'] in \
                project.getUnpublishedBuilds(),
                "Build should be in the unpublished list")

        # publish it now
        pubRelease.addBuild(build.id)

        # check the state of the world after publishing
        self.failUnless(data['anotherBuildId'] in pubRelease.getBuilds(),
                "Build was not properly added to published releases")
        self.failIf(data['anotherBuildId'] in \
                project.getUnpublishedBuilds(),
                "Build should no longer be considered unpublished")

    @fixtures.fixture("Full")
    def testRemoveBuildFromPublishedRelease(self, db, data):
        client = self.getClient("owner")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        project = client.getProject(data['projectId'])

        # sanity checks
        self.failUnless(data['buildId'] in pubRelease.getBuilds(),
                "Build should be published before beginning")
        self.failIf(data['buildId'] in project.getUnpublishedBuilds(),
                "Build should not be in the unpublished list")

        # unpublish it now
        pubRelease.removeBuild(data['buildId'])

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
        pubRelease = client.newPublishedRelease(data['projectId'])

        # set some things
        pubRelease.name = releaseName
        pubRelease.description = releaseDescription
        self.failUnless(pubRelease.name == releaseName)
        self.failUnless(pubRelease.description == releaseDescription)
        self.failIf(pubRelease.timeUpdated, "timeUpdated should not be set")
        self.failIf(pubRelease.updatedBy, "updatedBy should not be set")

        # now save to the database
        pubRelease.save()
        pubReleaseId = pubRelease.id

        # forget about it
        del pubRelease

        # retrieve it from the database, again
        pubRelease = client.getPublishedRelease(pubReleaseId)

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
        anotherBuild = client.getBuild(data['anotherBuildId'])

        self.failIf(build.getPublished(), "Build should not be published")
        self.failIf(anotherBuild.getPublished(), "Build should not be published")
        self.failUnless(pubBuild.getPublished(), "Build should be published")

    @fixtures.fixture("Full")
    def testGetPublishedReleasesByProject(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        self.failUnlessEqual(project.getPublishedReleases(), 
            [ data['pubReleaseFinalId'], data['imagelessReleaseId'], 
            data['pubReleaseId'] ])

    @fixtures.fixture("Full")
    def testGetUnpublishedBuildsByProject(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        self.failUnlessEqual(project.getUnpublishedBuilds(), 
            [ data['anotherBuildId']])

    @fixtures.fixture("Full")
    def testDeletePublishedRelease(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        client.deletePublishedRelease(data['pubReleaseId'])

        self.failUnlessEqual(len(project.getPublishedReleases()), 2,
                "There should be only two published releases in the project")

        self.failUnless(data['buildId'] in project.getUnpublishedBuilds(),
                "Previously published builds should now be unpublished")

        build = client.getBuild(data['buildId'])

        self.failIf(build.getPublished(), "Build still shows up as published")

    @fixtures.fixture("Full")
    def testPublishPublishedRelease(self, db, data):
        client = self.getClient("owner")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])

        self.failIf(pubRelease.timePublished,
                "Release should not be published yet")
        self.failIf(pubRelease.publishedBy,
                "Release should not be published yet")

        pubRelease.publish()
        pubRelease.refresh()

        self.assertNotEqual(pubRelease.timePublished, 0,
                "Release should be published now")
        self.failUnlessEqual(pubRelease.publishedBy, data['owner'],
                "Release wasn't marked with the appropriate publisher")
        self.failUnless(pubRelease.isPublished())

    @fixtures.fixture("Full")
    def testGetMirrorableReleases(self, db, data):
        '''
        Check that publishing and unpublishing sets the mirrorability
        of the associated releases and that
        I{getMirrorableReleasesByProject} reflects this.

        @tests: RBL-2546
        '''
        client = self.getClient("owner")

        # Check that there is nothing mirrorable initially
        mirrorableReleases = client.server.getMirrorableReleasesByProject(
            data['projectId'])
        self.failUnlessEqual(mirrorableReleases, [])

        # Publish a release
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        pubRelease.publish(shouldMirror=True)

        # Now check that it shows up in the mirrorable list
        mirrorableReleases = client.server.getMirrorableReleasesByProject(
            data['projectId'])
        self.failUnlessEqual(mirrorableReleases, [data['pubReleaseId']])

        # Unpublish it
        pubRelease.unpublish()

        # And check that it's not mirrorable anymore
        mirrorableReleases = client.server.getMirrorableReleasesByProject(
            data['projectId'])
        self.failUnlessEqual(mirrorableReleases, [])

    @fixtures.fixture("Full")
    def testDeleteBuildFromPublishedRelease(self, db, data):
        client = self.getClient("owner")
        pubBuild = client.getBuild(data['buildId'])
        pubBuild.deleteBuild()

    @fixtures.fixture("Full")
    def testDeleteBuildFromPublishedPublishedRelease(self, db, data):
        client = self.getClient("owner")
        pubBuild = client.getBuild(data['pubBuildId'])
        self.assertRaises(BuildPublished, pubBuild.deleteBuild)

    @fixtures.fixture("Full")
    def testPublishedReleaseAccessCreate(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (True, None),
                 'developer': (True, None),
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
                 'developer': (True, None),
                 'user': (False, PermissionDenied),
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
            # publish the release before testing
            adminClient = self.getClient("admin")
            newBuild = adminClient.newBuild(data['projectId'],
                    "Test Published Build")
            newBuild.setBuildType(buildtypes.STUB_IMAGE)
            newBuild.setFiles([["file", "file title 1"]])
            newBuild.setTrove("group-dist", "/testproject." + \
                    MINT_PROJECT_DOMAIN + "@rpl:devel/1.0-2-1", "1#x86")
            newPubRelease = adminClient.newPublishedRelease(data['projectId'])
            newPubRelease.addBuild(newBuild.id)
            newPubRelease.publish()

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
        hostname = "quux"
        otherProjectId = adminClient.newProject('Quux', hostname, 'rpath.org',
                       shortname=hostname, version="1.0", prodtype="Component")

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
        for user in ('admin', 'owner', 'developer'):
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
            userPubRelease.addBuild(newBuild.id)


    @fixtures.fixture("Full")
    def testPublishedReleaseAccessRemoveBuild(self, db, data):
        for user in ('admin', 'owner', 'developer'):
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
            userPubRelease.removeBuild(newBuild.id)


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
    def testPublishedReleaseAccessDeletePublished(self, db, data):
        acls = { 'admin': (False, PublishedReleasePublished),
                 'owner': (False, PublishedReleasePublished),
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
            newPubRelease.publish()

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
        raise testsuite.SkipTestException("rework me completely")

        client = self.getClient("owner")
        adminClient = self.getClient("admin")
        projectId = client.newProject("Foo", "foo", "rpath.org",
                        shortname="foo", version="1.0", prodtype="Component")
        project2Id = client.newProject("Bar", "bar", "rpath.org",
                        shortname="bar", version="1.0", prodtype="Component")
        project3Id = adminClient.newProject("Hide", "hide", "rpath.org",
                         shortname="hide", version="1.0", prodtype="Component")
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

    @fixtures.fixture('Full')
    def testAccessMissingPubRel(self, db, data):
        client = self.getClient('nobody')
        self.assertRaises(ItemNotFound, client.getPublishedRelease, 99)

    @fixtures.fixture('Full')
    def testModPubRel(self, db, data):
        client = self.getClient('owner')
        pubRel = client.getPublishedRelease(data['pubReleaseId'])
        pubRel.publish()

        self.assertRaises(PublishedReleasePublished, pubRel.save)

        client = self.getClient('developer')
        pubRel = client.getPublishedRelease(data['pubReleaseId'])
        self.assertRaises(PublishedReleasePublished, pubRel.save)

    @fixtures.fixture('Full')
    def testPubPubRelPerm(self, db, data):
        client = self.getClient('developer')
        pubRel = client.getPublishedRelease(data['pubReleaseId'])
        self.assertRaises(PermissionDenied, pubRel.publish)

    @fixtures.fixture('Full')
    def testPubEmptyPubRel(self, db, data):
        client = self.getClient('owner')
        pubRel = client.getPublishedRelease(data['pubReleaseId'])
        for buildId in pubRel.getBuilds():
            pubRel.removeBuild(buildId)
        self.assertRaises(PublishedReleaseEmpty, pubRel.publish)

    @fixtures.fixture('Full')
    def testPubPublishedPubRel(self, db, data):
        client = self.getClient('owner')
        pubRel = client.getPublishedRelease(data['pubReleaseId'])
        pubRel.publish()
        self.assertRaises(PublishedReleasePublished, pubRel.publish)

    @fixtures.fixture('Full')
    def testUnpubPublishedPubRel(self, db, data):
        client = self.getClient('owner')
        pubRel = client.getPublishedRelease(data['pubReleaseId'])
        pubRel.publish()
        pubRel.unpublish()
        try:
            pubRel.unpublish()
            self.fail("Should have failed with PublishedReleaseNotPublished")
        except PublishedReleaseNotPublished:
            # do nothing, expected
            pass
#        self.assertRaises(PublishedReleaseNotPublished, pubRel.unpublish)

    @fixtures.fixture('Full')
    def testUnpubPubRelPerm(self, db, data):
        client = self.getClient('owner')
        pubRel = client.getPublishedRelease(data['pubReleaseId'])
        pubRel.publish()

        client = self.getClient('developer')
        pubRel = client.getPublishedRelease(data['pubReleaseId'])
        self.assertRaises(PermissionDenied, pubRel.unpublish)

    @fixtures.fixture('Full')
    def testGetUniqueBuilds(self, db, data):
        client = self.getClient('owner')
        pubRel = client.getPublishedRelease(data['pubReleaseId'])
        assert(pubRel.getUniqueBuildTypes() == [(2, 'x86_64', [])])

    @fixtures.fixture('Full')
    def testUpdateRelease(self, db, data):
        client = self.getClient('owner')
        pubRel = client.getPublishedRelease(data['pubReleaseId'])
        client.server.updatePublishedRelease(pubRel.id,
                {'description': 'I like turtles.'})
        self.assertRaises(ParameterError,
                client.server.updatePublishedRelease, pubRel.id, {'projectId': 42})


