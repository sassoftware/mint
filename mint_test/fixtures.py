#
# Copyright (c) 2005-2008 rPath, Inc.
# All Rights Reserved
#
import copy
import inspect
from testrunner import testhelp
import tempfile
import random
import string
import subprocess
import os
import sys
import time
import pwd
import StringIO

from testrunner import testhelp
from testrunner import resources


from mint_rephelp import MINT_HOST, MINT_DOMAIN, MINT_PROJECT_DOMAIN, FQDN, PFQDN

from mint import shimclient
from mint import config
from mint import buildtypes
from mint import helperfuncs
from mint.flavors import stockFlavors
from mint import server
from mint import userlevels
from mint.data import RDT_STRING

from conary import dbstore
from conary.deps import deps
from conary.lib import util
from conary.dbstore import sqlerrors
import sqlharness

import mcp_helper
from mcp import queue
from mcp_helper import MCPTestMixin

from rpath_common.proddef import api1 as proddef

# Mock out the queues
queue.Queue = mcp_helper.DummyQueue
queue.Topic = mcp_helper.DummyQueue
queue.MultiplexedQueue = mcp_helper.DummyMultiplexedQueue
queue.MultiplexedTopic = mcp_helper.DummyMultiplexedQueue



def stockBuildFlavor(db, buildId, arch = "x86_64"):
    cu = db.cursor()
    flavor = deps.parseFlavor(stockFlavors['1#' + arch]).freeze()
    cu.execute("UPDATE Builds set troveFlavor=? WHERE buildId=?", flavor, buildId)
    db.commit()


class FixtureCache(object):
    _fixtures = {}

    def list(self):
        fixtureNames = [x for x in self.__class__.__base__.__dict__ \
                        if x.startswith('fixture')]
        return dict([(x.replace('fixture', ''),
                      self.__getattribute__(x).__doc__) for x in fixtureNames])

    def loadFixture(self, key):
        name = 'fixture' + key
        if key not in self._fixtures:
            fixture = self.__getattribute__(name)
            self._fixtures[key] = fixture(self.newMintCfg(key))
        return self._fixtures[key]

    def load(self, name):
        raise NotImplementedError

    def newMintCfg(self, name):
        cfg = config.MintConfig()
        cfg.authUser = 'mintauth'
        cfg.authPass = 'mintpass'
        cfg.debugMode = True
        cfg.hostName = MINT_HOST
        cfg.projectDomainName = MINT_PROJECT_DOMAIN
        cfg.externalDomainName = MINT_DOMAIN
        cfg.siteDomainName = MINT_DOMAIN
        cfg.secureHostName = "%s.%s" % (MINT_HOST, MINT_PROJECT_DOMAIN)
        cfg.dataPath = tempfile.mkdtemp(prefix = "fixture%s" % name)
        cfg.reposPath = os.path.join(cfg.dataPath, 'repos')
        cfg.reposContentsDir = "%s %s" % (os.path.join(cfg.dataPath, 'contents1', '%s'), os.path.join(cfg.dataPath, 'contents2', '%s'))
        cfg.imagesPath = os.path.join(cfg.dataPath, 'images')
        util.mkdirChain(cfg.imagesPath)
        cfg.sendNotificationEmails = False
        cfg.conaryRcFile = os.path.join(cfg.dataPath, 'run', 'conaryrc')
        util.mkdirChain(os.path.join(cfg.dataPath, 'run'))
        util.mkdirChain(os.path.join(cfg.dataPath, 'tmp'))
        cfg.newsRssFeed = 'file://' + resources.mintArchivePath + '/news.xml'
        cfg.ec2AccountId = '012345678901'
        cfg.ec2PublicKey = 'publicKey'
        cfg.ec2PrivateKey = 'secretKey'

        cfg.reposLog = False
        f = open(cfg.conaryRcFile, 'w')
        f.close()
        cfg.postCfg()

        util.mkdirChain(cfg.dataPath + "/config/")
        f = open(cfg.dataPath + "/config/mcp-client.conf", "w")
        f.close()

        return cfg

    def delRepos(self):
        raise NotImplementedError

    def createUser(self, cfg, db, username, isAdmin = False):
        """
        Creates a user named "username" filled with the following data:
        password -> "<username>pass"
        fullname -> "A User Named <username>"
        email    -> "<username>@example.com"
        contactInfo -> "<username> at example.com"

        If isAdmin is True, then the user will be given admin privileges.

        Returns the user id of the user.
        """

        client = shimclient.ShimMintClient(cfg, (cfg.authUser, cfg.authPass))

        assert(username)
        password = "%spass" % username
        fullname = "A User Named %s" % username
        email = "%s@example.com" % username
        contactInfo = "%s at example.com" % username

        cu = db.cursor()

        # create the public group
        try:
            cu.execute("INSERT INTO UserGroups (userGroup) VALUES('public')")
            db.commit()
        except sqlerrors.ColumnNotUnique:
            db.rollback()

        userId = client.registerNewUser(username, password, fullname,
            email, contactInfo, "", active=True)

        if isAdmin:
            cu.execute("""SELECT COUNT(*) FROM UserGroups
                              WHERE UserGroup = 'MintAdmin'""")
            if cu.fetchone()[0] == 0:
                cu.execute("""SELECT COALESCE(MAX(userGroupId) + 1, 1)
                                 FROM UserGroups""")
                groupId = cu.fetchone()[0]
                cu.execute("INSERT INTO UserGroups VALUES(?, 'MintAdmin')",
                           groupId)
                db.commit()
            else:
                cu.execute("""SELECT userGroupId FROM UserGroups
                                  WHERE UserGroup = 'MintAdmin'""")
                groupId = cu.fetchone()[0]

            cu.execute("INSERT INTO UserGroupMembers VALUES(?, ?)",
                       groupId, userId)
            db.commit()

        return userId

    def fixtureEmpty(self, cfg):
        """
        Empty fixture. Should be used when you want a (mostly) blank setup
        for testing.

        Creates the following setup:
            - Two users:
                - test (a basic user with no special privileges)
                - admin (a user wih admin privileges)

        @param cfg: The current effective Mint configuration.
        @return: A 2-tuple consisting of the current Mint configuration and a
            a dictionary containing the following:
                - C{test} - the id of the user "test"
                - C{admin} - the id of the user "admin"
        """
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)

        testId = self.createUser(cfg, db, "test")
        adminId = self.createUser(cfg, db, "admin", isAdmin=True)

        return cfg, { 'test': testId, 'admin': adminId }

    def fixtureFull(self, cfg):
        """
        Full (featured) fixture. This fixture should be good enough for
        90% of the tests written and should be used UNLESS the absence of
        data provided by this fixture is needed.

        Creates the following setup:
            - One project called "foo"
            - Six users
                - admin (a user with admin privileges)
                - owner (who owns the "foo" project)
                - developer (who is a developer in the "foo" project)
                - user (a user or watcher of the "foo" project
                - nobody (a user with no allegiance to any project)
            - Two Versions
                - 'FooV1', 'FooV1Description'
                - 'FooV2', 'FooV2Description'
            - Two published release objects
                - One publishd, or published, containing one build
                - One not publishd, containing another build
            - Three builds inside the "foo" project:
                - one published (i.e. belongs to the published release)
                - one unpublished (belongs to a release not yet published)
                - one available (not belonging to any release)
        @param cfg: The current effective Mint configuration.
        @return: A 2-tuple consisting of the current Mint configuration and a
            a dictionary containing the following:
                - C{test} - the id of the user "test"
                - C{user} - the id of the user "user"
                - C{admin} - the id of the user "admin"
                - C{owner} - the id of the user "owner"
                - C{developer} - the id of the user "developer"
                - C{nobody} - the id of the user "nobody"
                - C{projectId} - the id of the "Foo" project
                - C{buildId} - the id of the build in the "Foo" project
        """

        # connect to the database and open a MintServer instance
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)

        # create the users
        adminId = self.createUser(cfg, db, username = "admin", isAdmin = True)
        ownerId = self.createUser(cfg, db, username = "owner")
        developerId = self.createUser(cfg, db, username = "developer")
        userId = self.createUser(cfg, db, username = "user")
        nobodyId = self.createUser(cfg, db, username = "nobody")

        # create the project
        client = shimclient.ShimMintClient(cfg, ("owner", "ownerpass"))
        hostname = shortname = "foo"
        projectId = client.newProject("Foo", hostname, MINT_PROJECT_DOMAIN,
                                      shortname=shortname, 
                                      version="1.0", prodtype="Component")
        project = client.getProject(projectId)

        # add the developer
        project.addMemberById(developerId, userlevels.DEVELOPER)

        # add the watcher
        # (note: you have to use a separate client with the watcher's
        # credentials to add the watcher)
        userClient = shimclient.ShimMintClient(cfg, ("user", "userpass"))
        userProject = userClient.getProject(projectId)
        userProject.addMemberById(userId, userlevels.USER)

        # create a build for the "foo" project called "Test Build"
        # and add it to an unpublished (not final) release
        build = client.newBuild(projectId, "Test Build")
        build.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.1-1-1", "1#x86")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setFiles([["file", "file title 1"]])
        stockBuildFlavor(db, build.id)
        pubRelease = client.newPublishedRelease(projectId)
        pubRelease.name = "(Not final) Release"
        pubRelease.version = "1.1"
        pubRelease.addBuild(build.id)
        pubRelease.save()

        # create another build for the "foo" project and publish it
        # i.e. make it a part of a published release
        pubBuild = client.newBuild(projectId, "Test Published Build")
        pubBuild.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.0-1-1", "1#x86")
        pubBuild.setBuildType(buildtypes.STUB_IMAGE)
        pubBuild.setFiles([["file", "file title 1"]])
        stockBuildFlavor(db, pubBuild.id)
        pubReleaseFinal = client.newPublishedRelease(projectId)
        pubReleaseFinal.name = "Published Release"
        pubReleaseFinal.version = "1.0"
        pubReleaseFinal.addBuild(pubBuild.id)
        pubReleaseFinal.save()
        pubReleaseFinal.publish()

        # Create another build that just lies around somewhere
        # unattached to any published releases
        anotherBuild = client.newBuild(projectId, "Test Extra Build")
        anotherBuild.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.0-1-2", "1#x86")
        anotherBuild.setBuildType(buildtypes.STUB_IMAGE)
        anotherBuild.setFiles([["file", "file title 1"]])
        stockBuildFlavor(db, anotherBuild.id, "x86")

        # create an imageless group trove build and release
        imagelessBuild = client.newBuild(projectId, "Test Imageless Build")
        imagelessBuild.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.0-1-2", "1#x86")
        imagelessBuild.setBuildType(buildtypes.IMAGELESS)
        imagelessBuild.setFiles([["file", "file title 1"]])
        imagelessRelease = client.newPublishedRelease(projectId)
        imagelessRelease.name = "Published Imageless Release"
        imagelessRelease.version = "1.0"
        imagelessRelease.addBuild(imagelessBuild.id)
        imagelessRelease.save()

        # create 2 product versions in the project
        versionId = client.addProductVersion(projectId, 'ns', 'FooV1',
                'FooV1Description')
        versionId2 = client.addProductVersion(projectId, 'ns2', 'FooV2',
                'FooV2Description')

        # create a group trove for the "foo" project
        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
            'No Description', False)

        return cfg, { 'projectId':      projectId,
                      'admin':          adminId,
                      'owner':          ownerId,
                      'developer':      developerId,
                      'user':           userId,
                      'nobody':         nobodyId,
                      'buildId':        build.id,
                      'pubBuildId':     pubBuild.id,
                      'pubReleaseId':   pubRelease.id,
                      'pubReleaseFinalId':   pubReleaseFinal.id,
                      'anotherBuildId': anotherBuild.id,
                      'imagelessBuildId': imagelessBuild.id,
                      'imagelessReleaseId':   imagelessRelease.id,
                      'versionId' : versionId,
                      'versionId2' : versionId2,
                      'groupTroveId':   groupTrove.id }
    
    def fixtureCookJob(self, cfg):
        """
        CookJob fixture.

        Creates the following setup:
            - One user:
                - test (a basic user with no special privileges)
            - A project called "foo"
                - "test" is a member of "foo"
                - A build called "Test Build"
                - A group trove called "testtrove"
                - A single group trove cook job, in the "started" state

        @param cfg: The current effective Mint configuration.
        @return: A 2-tuple consisting of the current Mint configuration and a
            a dictionary containing the following:
                - C{test} - the id of the user "test"
        """
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)

        userId = self.createUser(cfg, db, 'test')
        client = shimclient.ShimMintClient(cfg, ('test', 'testpass'))

        projectId = client.newProject("Foo", "foo", "rpath.org")

        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        groupTroveId = groupTrove.getId()

        trvName = 'testtrove'
        trvVersion = '/testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)

        cookJobId = groupTrove.startCookJob("1#x86")
        return cfg, { 'userId': userId }

    def fixtureImageJob(self, cfg):
        """
        ImageJob fixture.

        Creates the following setup:
            - One user:
                - test (a basic user with no special privileges)
            - A project called "foo"
                - "test" is a member of "foo"
                - A build called "Test Build"
                - A single image job, in the "started" state

        @param cfg: The current effective Mint configuration.
        @return: A 2-tuple consisting of the current Mint configuration and a
            a dictionary containing the following:
                - C{test} - the id of the user "test"
        """
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        testId = self.createUser(cfg, db, 'test')

        client = shimclient.ShimMintClient(cfg, ('test', 'testpass'))

        projectId = client.newProject("Foo", "foo", "rpath.org")

        build = client.newBuild(projectId, "Test Build")
        build.setBuildType(buildtypes.STUB_IMAGE)

        stockBuildFlavor(db, build.getId())

        prodJob = client.startImageJob(build.getId())
        return cfg, { 'test': testId }

    def fixtureBothJobs(self, cfg):
        """
        BothJobs fixture.

        Creates the following setup:
            - One user:
                - test (a basic user with no special privileges)
            - A project called "foo"
                - "test" is a member of "foo"
                - A group trove called "testtrove"
                - A build called "Test Build"
                - A single image job, in the "started" state
                - A single group trove cook job, in the "started" state

        @param cfg: The current effective Mint configuration.
        @return: A 2-tuple consisting of the current Mint configuration and a
            a dictionary containing the following:
                - C{test} - the id of the user "test"
        """
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)

        testId = self.createUser(cfg, db, 'test')

        client = shimclient.ShimMintClient(cfg, ('test', 'testpass'))
        projectId = client.newProject("Foo", "foo", "rpath.org")

        build = client.newBuild(projectId, "Test Build")
        build.setBuildType(buildtypes.STUB_IMAGE)

        stockBuildFlavor(db, build.getId())

        prodJob = client.startImageJob(build.getId())

        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
            'No Description', False)

        groupTroveId = groupTrove.getId()

        trvName = 'testtrove'
        trvVersion = '/testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel/1.0-1-1'
        trvFlavor = '1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        trvid = groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                    subGroup, False, False, False)

        cookJobId = groupTrove.startCookJob("1#x86")

        db.commit()
        return cfg, { 'test': testId }

    def fixtureEC2(self, cfg):
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)

        adminId = self.createUser(cfg, db,
                username = 'admin', isAdmin = True)

        developerId = self.createUser(cfg, db,
                username = 'developer', isAdmin = False)

        someOtherDeveloperId = self.createUser(cfg, db,
                username = 'someotherdeveloper', isAdmin = False)

        normalUserId = self.createUser(cfg, db,
                username = 'normaluser', isAdmin = False)

        client    = shimclient.ShimMintClient(cfg,
                ('admin', 'adminpass'))

        someOtherClient = shimclient.ShimMintClient(cfg,
                ('someotherdeveloper', 'someotherdeveloperpass'))

        normalUserClient = shimclient.ShimMintClient(cfg,
                ('normaluser', 'normaluserpass'))

        # Create a user to be used for joining products in the tests.
        loneUserId = self.createUser(cfg, db,
                username = 'loneuser', isAdmin = False)

        hostname = shortname = "testproject"
        projectId = someOtherClient.newProject("Test Project",
                                      hostname,
                                      MINT_PROJECT_DOMAIN,
                                      shortname=shortname,
                                      version="1.0",
                                      prodtype="Component")

        hostname = shortname = "otherproject"
        otherProjectId = someOtherClient.newProject("Other Project",
                                      hostname,
                                      MINT_PROJECT_DOMAIN,
                                      shortname=shortname,
                                      version="1.0",
                                      prodtype="Component")

        hostname = shortname = "hiddenproject"
        hiddenProjectId = someOtherClient.newProject("Hidden Test Project",
                                      hostname,
                                      MINT_PROJECT_DOMAIN,
                                      shortname=shortname,
                                      version="1.0",
                                      prodtype="Component")
        hiddenproject = client.getProject(hiddenProjectId)

        # add the developer to the testproject
        project = client.getProject(projectId)
        project.addMemberById(developerId, userlevels.DEVELOPER)
        # add the normal user to the testproject
        normalProject = normalUserClient.getProject(projectId)
        normalProject.addMemberById(normalUserId, userlevels.USER)

        # add the developer to the hiddenproject
        hiddenproject.addMemberById(developerId, userlevels.DEVELOPER)
        # add the normal user to the hiddenproject
        normalHiddenProject = normalUserClient.getProject(hiddenProjectId)
        normalHiddenProject.addMemberById(normalUserId, userlevels.USER)
        ret = client.hideProject(hiddenProjectId)

        # create an AMI build that isn't a part of a release
        build = client.newBuild(projectId,
                "Test AMI Build (Unpublished, not in release)")
        build.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.1-1-1", "1#x86")
        build.setBuildType(buildtypes.AMI)
        build.setDataValue('amiId', 'ami-00000001', RDT_STRING,
                validate=False)

        # create an AMI build and add it to an unpublished
        # (not final) release
        build = client.newBuild(projectId, "Test AMI Build (Unpublished)")
        build.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.2-1-1", "1#x86")
        build.setBuildType(buildtypes.AMI)
        build.setDataValue('amiId', 'ami-00000002', RDT_STRING,
                validate=False)
        pubRelease = client.newPublishedRelease(projectId)
        pubRelease.name = "(Not final) Release"
        pubRelease.version = "1.1"
        pubRelease.addBuild(build.id)
        pubRelease.save()
        buildId1 = build.id

        # create an AMI build and add it to a published release
        build = client.newBuild(projectId, "Test AMI Build (Published)")
        build.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.3-1-1", "1#x86")
        build.setBuildType(buildtypes.AMI)
        build.setDataValue('amiId', 'ami-00000003', RDT_STRING,
                validate=False)
        pubRelease = client.newPublishedRelease(projectId)
        pubRelease.name = "Release"
        pubRelease.version = "1.0"
        pubRelease.addBuild(build.id)
        pubRelease.save()
        pubRelease.publish()
        buildId2 = build.id

        # create a published AMI build on the other project
        build = client.newBuild(otherProjectId, "Test AMI Build (Published)")
        build.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.4-1-1", "1#x86")
        build.setBuildType(buildtypes.AMI)
        build.setDataValue('amiId', 'ami-00000004', RDT_STRING,
                validate=False)
        pubRelease = client.newPublishedRelease(otherProjectId)
        pubRelease.name = "Release"
        pubRelease.version = "1.0"
        pubRelease.addBuild(build.id)
        pubRelease.save()
        pubRelease.publish()
        buildId3 = build.id

        # create a plain ol' AMI build on the other project
        build = client.newBuild(otherProjectId,
                "Test AMI Build (Published)")
        build.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.5-1-1", "1#x86")
        build.setBuildType(buildtypes.AMI)
        build.setDataValue('amiId', 'ami-00000005', RDT_STRING,
                validate=False)
        buildId4 = build.id

        # create an AMI build and add it to an unpublished
        # (not final) release on the hiddenproject
        build = client.newBuild(hiddenProjectId, "Test AMI Build (Unpublished)")
        build.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.2-1-1", "1#x86")
        build.setBuildType(buildtypes.AMI)
        build.setDataValue('amiId', 'ami-00000006', RDT_STRING,
                validate=False)
        pubRelease = client.newPublishedRelease(hiddenProjectId)
        pubRelease.name = "(Not final) Release"
        pubRelease.version = "1.1"
        pubRelease.addBuild(build.id)
        pubRelease.save()
        hiddenProjUnpubPubReleaseId = pubRelease.id
        buildId5 = build.id

        # create an AMI build and add it to a published release on the hidden
        # project.
        build = client.newBuild(hiddenProjectId, "Test AMI Build (Published)")
        build.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.3-1-1", "1#x86")
        build.setBuildType(buildtypes.AMI)
        build.setDataValue('amiId', 'ami-00000007', RDT_STRING,
                validate=False)
        pubRelease = client.newPublishedRelease(hiddenProjectId)
        pubRelease.name = "Release"
        pubRelease.version = "1.0"
        pubRelease.addBuild(build.id)
        pubRelease.save()
        pubRelease.publish()
        hiddenProjPubPubReleaseId = pubRelease.id
        buildId6 = build.id

        amiIds = []
        for i in range(0,7):
            amiIds.append(client.createBlessedAMI('ami-%08d' % i,
                    "This is test AMI instance %d" % i))

        return cfg, { 'adminId': adminId,
                      'developerId': developerId,
                      'normalUserId': normalUserId,
                      'someOtherDeveloperId': someOtherDeveloperId,
                      'amiIds': amiIds,
                      'projectId': projectId,
                      'otherProjectId': otherProjectId,
                      'hiddenProjectId': hiddenProjectId,
                      'loneUserId': loneUserId,
                      'hiddenProjUnpubPubReleaseId': hiddenProjUnpubPubReleaseId,
                      'hiddenProjPubPubReleaseId': hiddenProjPubPubReleaseId,
                      'buildId1' : buildId1,
                      'buildId2' : buildId2,
                      'buildId3' : buildId3,
                      'buildId4' : buildId4,
                      'buildId5' : buildId5,
                      'buildId6' : buildId6,
                      }

    def getAMIConfig(self, testCfg):
        # AMI testing
        testCfg.ec2PublicKey = '123456789ABCDEFGHIJK'
        testCfg.ec2PrivateKey = '123456789ABCDEFGHIJK123456789ABCDEFGHIJK'
        testCfg.ec2AccountId   = '000000000000'
        testCfg.ec2S3Bucket    = 'extracrispychicken'
        testCfg.ec2CertificateFile = os.path.join(testCfg.dataPath, 'config', 'ec2.pem')
        testCfg.ec2CertificateKeyFile = os.path.join(testCfg.dataPath, 'config', 'ec2.key')
        testCfg.configLine("ec2LaunchUsers 000000001111")
        testCfg.configLine("ec2LaunchUsers 000000002222")
        testCfg.configLine("ec2LaunchGroups group1")
        testCfg.configLine("ec2LaunchGroups group2")
        util.copyfile(os.path.join(resources.mintArchivePath, 'ec2.key'),
                      os.path.join(testCfg.dataPath, 'config'))
        util.copyfile(os.path.join(resources.mintArchivePath, 'ec2.pem'),
                      os.path.join(testCfg.dataPath, 'config'))

    def __del__(self):
        for f in self._fixtures.values():
            util.rmtree(f[0].dataPath)

class SqliteFixtureCache(FixtureCache):

    def newMintCfg(self, name):
        cfg = FixtureCache.newMintCfg(self, name)
        cfg.dbDriver = cfg.reposDBDriver = 'sqlite'
        cfg.dbPath = os.path.join(cfg.dataPath, 'mintdb')
        cfg.reposDBPath = os.path.join(cfg.dataPath, 'repos', '%s', 'sqldb')
        from mint import schema
        db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
        schema.loadSchema(db, cfg)
        return cfg

    def load(self, name):
        cfg, data = self.loadFixture(name)

        # make a copy of the data directory and update the cfg
        testDataPath = tempfile.mkdtemp(prefix = "fixture%s" % name, suffix = '.copy')
        self.testDataPath = testDataPath
        util.copytree(os.path.join(cfg.dataPath,'*'), testDataPath)
        testCfg = copy.deepcopy(cfg)
        testCfg.dataPath = testDataPath
        testCfg.dbPath = os.path.join(testCfg.dataPath, 'mintdb')
        testCfg.imagesPath = os.path.join(testCfg.dataPath, 'images')
        testCfg.reposContentsDir = "%s %s" % (os.path.join(testCfg.dataPath, 'contents1', '%s'), os.path.join(cfg.dataPath, 'contents2', '%s'))
        testCfg.reposDBPath = os.path.join(testCfg.dataPath, 'repos', '%s', 'sqldb')
        testCfg.reposPath = os.path.join(testCfg.dataPath, 'repos')
        testCfg.conaryRcFile = os.path.join(testCfg.dataPath, 'run', 'conaryrc')

        self.getAMIConfig(testCfg)

        f = open(os.path.join(testCfg.dataPath, "rbuilder.conf"), 'w')
        testCfg.display(out=f)
        f.close()

        return testCfg, data

    def delRepos(self):
        try:
            util.rmtree(self.testDataPath)
        except AttributeError:
            pass

class SQLServerFixtureCache(FixtureCache):
    harness = None
    def __init__(self):
        self.harness = sqlharness.getHarness(self.driver)
    def _randomName(self):
        return "".join(random.sample(string.lowercase, 5))
    def _getConnectStringForDb(self, dbName = "%s"):
        return os.path.join(self.harness.conn, dbName)


class MySqlFixtureCache(SQLServerFixtureCache):
    keepDbs = ['mysql', 'test', 'information_schema', 'testdb']
    driver = "mysql"

    def _dupDb(self, srcDb, destDb):
        self.harness.getDB(destDb)
        output = ["mysqldump", "-u", "root", "-S", "%s/socket" % self.harness.path, srcDb]
        input = ["mysql", "-u", "root", "-S", "%s/socket" % self.harness.path, destDb]
        dump = subprocess.Popen(output, stdout = subprocess.PIPE)
        load = subprocess.Popen(input, stdin = dump.stdout)
        load.communicate()
        
    def newMintCfg(self, name):
        cfg = super(self.__class__,self).newMintCfg(name)
        dbName = "mf%s" % name
        self.keepDbs.append(dbName.lower())
        db = self.harness.getDB(dbName)
        cfg.dbDriver = cfg.reposDBDriver = "mysql"
        cfg.dbPath = self._getConnectStringForDb(dbName)
        cfg.reposDBPath = self._getConnectStringForDb()
        from mint import schema
        schema.loadSchema(db.connect(), cfg)
        db.stop()
        return cfg

    def loadFixture(self, name):
        ret = super(self.__class__, self).loadFixture(name)
        # save repos tables off for later
        db = self.harness.getRootDB()
        cu = db.cursor()
        cu.execute("SHOW DATABASES")
        for dbname in [x[0] for x in cu.fetchall() if x[0] not in self.keepDbs]:
            if '_' in dbname and not dbname.startswith('cr'):
                newName = ("cr%s%s" % (name, dbname)).lower()
                self._dupDb(dbname, newName)
                self.harness.dropDB(dbname)
                self.keepDbs.append(newName)
        return ret

    def load(self, name):
        cfg, data = self.loadFixture(name)

        # get a random name for this particular instance of the fixture
        # in order to create unique copies
        randomDbName = self._randomName()

        # make a copy of the data directory and update the cfg
        testDataPath = tempfile.mkdtemp(prefix = "fixture%s" % name, suffix = '.copy')
        util.copytree(os.path.join(cfg.dataPath,'*'), testDataPath)
        testCfg = copy.deepcopy(cfg)
        testCfg.dataPath = testDataPath
        testCfg.imagesPath = os.path.join(testCfg.dataPath, 'images')
        testCfg.reposContentsDir = "%s %s" % (os.path.join(testCfg.dataPath, 'contents1', '%s'),
                                              os.path.join(testCfg.dataPath, 'contents2', '%s'))
        testCfg.reposPath = os.path.join(testCfg.dataPath, 'repos')
        testCfg.conaryRcFile = os.path.join(testCfg.dataPath, 'run', 'conaryrc')

        self.getAMIConfig(testCfg)

        # restore the mint db into a unique copy
        fixtureMintDbName = ("mf%s" % name).lower()
        fixtureCopyMintDbName = ("cmf_%s%s" % (name, randomDbName)).lower()
        self._dupDb(fixtureMintDbName, fixtureCopyMintDbName)
        testCfg.dbPath = self._getConnectStringForDb(fixtureCopyMintDbName)

        # restore the repos dbs
        db = self.harness.getRootDB()
        cu = db.cursor()
        cu.execute("SHOW DATABASES LIKE 'cr%s%%'" % name.lower())
        for dbname in [x[0] for x in cu.fetchall()]:
            fixtureCopyReposDbName = dbname[2+len(name):]
            self._dupDb(dbname, fixtureCopyReposDbName)

        f = open(os.path.join(testCfg.dataPath, "rbuilder.conf"), 'w')
        testCfg.display(out=f)
        f.close()

        return testCfg, data

    def delRepos(self):
        db = self.harness.getRootDB()
        cu = db.cursor()
        cu.execute("SHOW DATABASES")
        for dbname in [x[0] for x in cu.fetchall() if x[0] not in self.keepDbs]:
           if '_' in dbname and not dbname.startswith('cr'):
               self.harness.dropDB(dbname)

    def __del__(self):
        self.harness.stop()
        for f in self._fixtures.values():
            util.rmtree(f[0].dataPath)

class PostgreSqlFixtureCache(SQLServerFixtureCache):
    keepDbs = ['postgres', 'testdb', 'template1', 'template0']
    driver = "postgresql"

    def _dupDb(self, srcDb, destDb):
        self.harness.getDB(destDb)
        output = ["pg_dump", "-U", self.harness.user, '-c', '-O', 
                  '-p', str(self.harness.port), '-d', srcDb]
        input = ["psql", '-p', str(self.harness.port), "-U", self.harness.user, destDb.lower()]
        dump = subprocess.Popen(output, stdout = subprocess.PIPE)
        fd = open('/dev/null', 'w')
        load = subprocess.Popen(input, stdin = dump.stdout, stdout=fd, 
            stderr=fd)
        load.communicate()
        fd.close()

    def newMintCfg(self, name):
        cfg = super(self.__class__, self).newMintCfg(name)
        cfg.reposDBDriver = 'postgresql'
        cfg.dbDriver = 'sqlite'
        cfg.dbPath = os.path.join(cfg.dataPath, 'mintdb')
        cfg.reposDBPath = self._getConnectStringForDb()
        db = dbstore.connect(cfg.dbPath, driver = cfg.dbDriver)
        from mint import schema
        schema.loadSchema(db, cfg)
        return cfg

    def loadFixture(self, name):
        ret = super(self.__class__, self).loadFixture(name)
        # save repos tables off for later
        db = self.harness.getRootDB()
        cu = db.cursor()
        cu.execute("SELECT datname FROM pg_database")
        for dbname in [x[0] for x in cu.fetchall() if x[0] not in self.keepDbs]:
            if '_' in dbname and not dbname.startswith('cr'):
                newName = "cr%s%s" % (name, dbname)
                self._dupDb(dbname, newName)
                self.harness.dropDB(dbname)
                self.keepDbs.append(newName.lower())
        return ret

    def load(self, name):
        cfg, data = self.loadFixture(name)

        # get a random name for this particular instance of the fixture
        # in order to create unique copies
        randomDbName = self._randomName()

        # make a copy of the data directory and update the cfg
        testDataPath = tempfile.mkdtemp(prefix = "fixture%s" % name, suffix = '.copy')
        util.copytree(os.path.join(cfg.dataPath,'*'), testDataPath)
        testCfg = copy.deepcopy(cfg)
        testCfg.dataPath = testDataPath
        testCfg.dbPath = os.path.join(testCfg.dataPath, 'mintdb')
        testCfg.imagesPath = os.path.join(testCfg.dataPath, 'images')
        testCfg.reposContentsDir = "%s %s" % (os.path.join(testCfg.dataPath, 'contents1', '%s'),
                                              os.path.join(cfg.dataPath, 'contents2', '%s'))
        testCfg.reposPath = os.path.join(testCfg.dataPath, 'repos')
        testCfg.conaryRcFile = os.path.join(testCfg.dataPath, 'run', 'conaryrc')

        self.getAMIConfig(testCfg)

        f = open(os.path.join(testCfg.dataPath, "rbuilder.conf"), 'w')
        testCfg.display(out=f)
        f.close()

        # restore the repos dbs
        db = self.harness.getRootDB()
        cu = db.cursor()
        cu.execute("""SELECT datname FROM pg_database 
                      WHERE datname LIKE 'cr%s%%'""" % name.lower())
        for dbname in [x[0] for x in cu.fetchall()]:
            fixtureCopyReposDbName = dbname[2+len(name):]
            self._dupDb(dbname, fixtureCopyReposDbName)

        return testCfg, data

    def delRepos(self):
        db = self.harness.getRootDB()
        cu = db.cursor()
        cu.execute("SELECT datname FROM pg_database")
        for dbname in [x[0] for x in cu.fetchall() if x[0] not in self.keepDbs]:
           if '_' in dbname and not dbname.startswith('cr'):
               self.harness.dropDB(dbname)

    def __del__(self):
        self.harness.stop()
        for f in self._fixtures.values():
            util.rmtree(f[0].dataPath)


class FixturedUnitTest(testhelp.TestCase, MCPTestMixin):
    adminClient = None
    cfg = None

    # apply default context of "fixtured" to all children of this class
    contexts = ("fixtured",)

    def listFixtures(self):
        return fixtureCache.list()

    def loadFixture(self, name):
        """
        Loads the fixture for the unit test.
        @param name: the name of the fixture (e.g. "Full")
        @returns: A 3-typle consisting of a database connection,
           a Mint client with admin credentials, and a dictionary of 
           fixture data (may be empty).
        """

        # reset the cached db connection
        self.cfg, fixtureData = fixtureCache.load(name)
        db = dbstore.connect(self.cfg.dbPath, self.cfg.dbDriver)
        # this is so fugly it makes me wanna cry --gafton
        server.dbConnection = db
        return db, fixtureData

    def getAdminClient(self):
        if not self.adminClient:
            self.adminClient = shimclient.ShimMintClient(self.cfg, ('mintauth', 'mintpass'))
        return self.adminClient

    def getClient(self, username, password=None):
        if password is None:
            if username == 'anonymous':
                password = 'anonymous'
            else:
                password = '%spass' % username
        s = shimclient.ShimMintClient(self.cfg, (username, password))
        s.server._server.mcpClient = self.mcpClient
        return s

    def getAnonymousClient(self):
        return self.getClient('anonymous')

    def quickMintUser(self, username, password, email = "test@example.com"):
        client = self.getAdminClient()
        userId = client.registerNewUser(username, password, "Test User",
            email, "test at example.com", "", active=True)
        client = shimclient.ShimMintClient(self.cfg, (username, password))
        return client, userId

    def getMirrorAcl(self, project, username):
        """
        Given a project and a username, will determine whether or not the
        user has the ability to mirror.
        @param project: the project to check against
        @param username: the user whose credentials should be checked
        @returns: C{True} if C{username} can mirror C{project}; C{False}
            otherwise.
        """
        dbCon = project.server._server.projects.reposDB.getRepositoryDB( \
            project.getFQDN())
        db = dbstore.connect(dbCon[1], dbCon[0])

        cu = db.cursor()

        cu.execute("""SELECT canMirror
                          FROM Users
                          LEFT JOIN UserGroupMembers ON Users.userId =
                                  UserGroupMembers.userId
                          LEFT JOIN UserGroups ON UserGroups.userGroupId =
                                  UserGroupMembers.userGroupId
                          WHERE Users.username=?""", username)

        try:
            # nonexistent results trigger value error
            canMirror = max([x[0] for x in cu.fetchall()])
        except ValueError:
            canMirror = None
        db.close()
        return canMirror

    def getWriteAcl(self, project, username):
        dbCon = project.server._server.projects.reposDB.getRepositoryDB( \
            project.getFQDN())
        db = dbstore.connect(dbCon[1], dbCon[0])

        cu = db.cursor()

        cu.execute("""SELECT MAX(canWrite)
                          FROM Users
                          LEFT JOIN UserGroupMembers ON Users.userId =
                                  UserGroupMembers.userId
                          LEFT JOIN Permissions ON Permissions.userGroupId =
                                  UserGroupMembers.userGroupId
                          WHERE Users.username=?""", username)
        return cu.fetchone()[0]

    def getAdminAcl(self, project, username):
        dbCon = project.server._server.projects.reposDB.getRepositoryDB( \
            project.getFQDN())
        db = dbstore.connect(dbCon[1], dbCon[0])

        cu = db.cursor()
        cu.execute("""SELECT MAX(admin) FROM Users
                      JOIN UserGroupMembers ON
                          Users.userId = UserGroupMembers.userId
                      JOIN UserGroups ON
                          UserGroups.userGroupId = UserGroupMembers.userGroupId
                      WHERE Users.username=?""", username)
        return cu.fetchone()[0]

    def captureAllOutput(self, func, *args, **kwargs):
        oldErr = os.dup(sys.stderr.fileno())
        oldOut = os.dup(sys.stdout.fileno())
        fd = os.open(os.devnull, os.W_OK)
        os.dup2(fd, sys.stderr.fileno())
        os.dup2(fd, sys.stdout.fileno())
        try:
            return func(*args, **kwargs)
        finally:
            os.dup2(oldErr, sys.stderr.fileno())
            os.dup2(oldOut, sys.stdout.fileno())

    def setUp(self):
        testhelp.TestCase.setUp(self)
        MCPTestMixin.setUp(self)

    def tearDown(self):
        if server.dbConnection:
            server.dbConnection.close()
        server.dbConnection = None
        testhelp.TestCase.tearDown(self)
        MCPTestMixin.tearDown(self)
        try:
            fixtureCache.delRepos()
            self.cfg and util.rmtree(self.cfg.dataPath)
        except OSError:
            pass

class FixturedProductVersionTest(FixturedUnitTest):

    global _testxmldata
    _testxmldata = None

    class _MockProductDefinition(proddef.ProductDefinition):
        def saveToRepository(self, *args, **kwargs):
            sio = StringIO.StringIO()
            self.serialize(sio)
            global _testxmldata
            _testxmldata = sio.getvalue()

        def loadFromRepository(self, *args, **kwargs):
            global _testxmldata
            if not _testxmldata:
                raise proddef.ProductDefinitionTroveNotFound
            sio = StringIO.StringIO(_testxmldata)
            sio.seek(0)
            self.parseStream(sio)

    def setUp(self):
        self.oldProductDefinition = proddef.ProductDefinition
        proddef.ProductDefinition = self._MockProductDefinition
        FixturedUnitTest.setUp(self)
        global _testxmldata
        _testxmldata = None

    def tearDown(self):
        FixturedUnitTest.tearDown(self)
        proddef.ProductDefinition = self.oldProductDefinition
        global _testxmldata
        _testxmldata = None


driver = os.environ.get("CONARY_REPOS_DB", "sqlite")
if driver == "sqlite":
    fixtureCache = SqliteFixtureCache()
elif driver == "mysql":
    fixtureCache = MySqlFixtureCache()
elif driver == "postgresql":
    fixtureCache = PostgreSqlFixtureCache()
else:
    raise RuntimeError, "Invalid database driver specified"

# test case decorator
def fixture(arg):
    def deco(func):
        def wrapper(self):
            db, data = self.loadFixture(arg)
            return func(self, db, data)
        wrapper.__name__ = func.__name__
        wrapper.__dict__.update(func.__dict__)
        return wrapper
    return deco