#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

import sys

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_PROJECT_DOMAIN

from mint import userlevels
from mint.database import DuplicateItem, ItemNotFound
from mint.projects import InvalidHostname, DuplicateHostname, DuplicateName
from mint.server import ParameterError, PermissionDenied

from conary import dbstore
from conary.conaryclient import ConaryClient

import fixtures

class ProjectTest(fixtures.FixturedUnitTest):

    def _checkMembership(self, project, expectedUserId, expectedAcl):
        return [expectedUserId, expectedAcl] in \
                [[x[0], x[2]] for x in project.getMembers()]

    @fixtures.fixture("Full")
    def testBasicAttributes(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])

        assert(project.getFQDN() == "foo.%s" % MINT_PROJECT_DOMAIN)
        assert(project.getHostname() == "foo")
        assert(project.getDomainname() == MINT_PROJECT_DOMAIN)
        assert(project.getName() == "Foo")
        assert(project.getMembers() == [ \
                [data['owner'], 'owner', userlevels.OWNER], \
                [data['developer'], 'developer', userlevels.DEVELOPER], \
                [data['user'], 'user', userlevels.USER] ])
        assert(project.hidden == 0)
        assert(project.external == 0)
        assert(project.disabled == 0)

    @fixtures.fixture("Full")
    def testEditProject(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        project.editProject("http://example.com/", "Description", "Foo Title")
        project.refresh()

        assert(project.getName() == "Foo Title")
        assert(project.getDesc() == "Description")
        assert(project.getProjectUrl() == "http://example.com/")

        # create a new project to conflict with
        newProjectId = client.newProject("Foo2", "foo2", MINT_PROJECT_DOMAIN)

        self.failUnlessRaises(DuplicateItem, project.editProject,
                "http://example.com/", "Description", "Foo2")

        # test automatic prepending of http://
        project.editProject("www.example.com", "Description", "Foo Title")
        project.refresh()
        assert(project.getProjectUrl() == "http://www.example.com")

        # except when there's no project URL
        project.editProject("", "Description", "Foo Title")
        project.refresh()
        assert(project.getProjectUrl() == "")

    @fixtures.fixture("Full")
    def testGetProjects(self, db, data):
        client = self.getClient("owner")
        project = client.getProjectByHostname("foo")
        assert(data['projectId'] == project.getId())

        project = client.getProjectByFQDN("foo.%s" % MINT_PROJECT_DOMAIN)
        assert(data['projectId'] == project.getId())

    @fixtures.fixture("Full")
    def testMembers(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])

        project.addMemberById(data['nobody'], userlevels.DEVELOPER)
        self.failUnless(self._checkMembership(project, data['nobody'], \
                userlevels.DEVELOPER))

        project.delMemberById(data['nobody'])
        self.failIf(self._checkMembership(project, data['nobody'], \
                userlevels.DEVELOPER))

        project.addMemberByName('nobody', userlevels.OWNER)
        self.failUnless(self._checkMembership(project, data['nobody'], \
                userlevels.OWNER))

        project.updateUserLevel(data['nobody'], userlevels.DEVELOPER)
        self.failUnless(self._checkMembership(project, data['nobody'], \
                userlevels.DEVELOPER))

    @fixtures.fixture("Full")
    def testWatcher(self, db, data):
        nobodyClient = self.getClient('nobody')
        project = nobodyClient.getProject(data['projectId'])

        project.addMemberByName("nobody", userlevels.USER)
        self.failUnless(self._checkMembership(project, data['nobody'], \
                userlevels.USER))

        assert([x[0].id for x in nobodyClient.getProjectsByMember(data['nobody'])] == [data['projectId']])

    @fixtures.fixture("Full")
    def testDuplicateMembers(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        project.addMemberById(data['nobody'], userlevels.DEVELOPER)
        # a consecutive addMember should run properly--just becomes an update
        project.addMemberById(data['nobody'], userlevels.OWNER)

    @fixtures.fixture("Full")
    def testMissingUser(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        cu = db.cursor()
        cu.execute("DELETE FROM Users WHERE username='nobody'")
        db.commit()
        self.assertRaises(ItemNotFound, project.addMemberById, data['nobody'],
                          userlevels.DEVELOPER)

    @fixtures.fixture("Full")
    def testBadHostname(self, db, data):
        client = self.getClient("owner")
        for hostname in ('admin', 'a bad name', '', 'a_bad_name', 'a.bad.name'):
            try:
                projectId = client.newProject("Quux", hostname, 'localhost')
                self.fail("allowed to create a project with a bad name")
            except InvalidHostname:
                pass
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if str(exc_value).split(' ')[0] != 'ParameterError':
                    raise

    @fixtures.fixture("Full")
    def testUnconfirmedMembers(self, db, data):
        client = self.getClient("owner")
        unconfirmedUserId = client.registerNewUser("unconfirmed",
                                                   "memberpass",
                                                   "Unconfirmed Member",
                                                   "test@example.com",
                                                   "test at example.com",
                                                   "", active=False)
 
        project = client.getProject(data['projectId'])

        #Try to add an unconfirmed member to the project by userName
        try:
            project.addMemberByName("unconfirmed", userlevels.DEVELOPER)
        except ItemNotFound, e:
            pass
        else:
            self.fail("ItemNotFound Exception expected")

        #Try to add an unconfirmed member to the project by userId
        try:
            project.addMemberById(unconfirmedUserId, userlevels.DEVELOPER)
        except ItemNotFound, e:
            pass
        else:
            self.fail("ItemNotFound Exception expected")

    @fixtures.fixture("Full")
    def testGetProjectsByMember(self, db, data):
        # create a new project with the nobody client
        client = self.getClient("owner")
        nobodyClient = self.getClient('nobody')
        newProjectId = nobodyClient.newProject("Quux", "quux", "localhost")
        projects = client.getProjectsByMember(data['nobody'])
        assert(projects[0][0].getId() == newProjectId)
        assert(projects[0][1] == userlevels.OWNER)

        if client.server.getProjectsByUser(data['nobody']) != \
                [['quux.localhost', 'Quux', 0]]:
            self.fail("getProjectsByUser returned incorrect results")

    @fixtures.fixture("Full")
    def testHideProject(self, db, data):
        adminClient = self.getClient("admin")
        ownerClient = self.getClient("owner")
        developerClient = self.getClient("developer")
        watcherClient = self.getClient("user")
        nobodyClient = self.getClient("nobody")

        project = ownerClient.getProject(data['projectId'])
        nobodyProject = nobodyClient.getProject(data['projectId'])

        # hide the project
        adminClient.hideProject(data['projectId'])

        # try getting the project from various levels
        developerClient.getProject(data['projectId'])
        adminClient.getProject(data['projectId'])

        self.assertRaises(ItemNotFound, nobodyClient.getProject, data['projectId'])
        self.assertRaises(ItemNotFound, watcherClient.getProject, data['projectId'])
        self.assertRaises(ItemNotFound, nobodyClient.server.getProjectIdByFQDN,
                          "foo.%s" % MINT_PROJECT_DOMAIN)
        self.assertRaises(ItemNotFound, nobodyClient.server.getProjectIdByHostname,
                          "foo")

        self.failIf(nobodyClient.server.getProjectIdsByMember(data['owner']),
                    "Nonmember found hidden project (getProjectIdsByMember)")

        self.failUnless(adminClient.server.getProjectIdsByMember(data['owner']),
                    "Admin missed hidden project (getProjectIdsByMember)")

        self.failUnless(ownerClient.server.getProjectIdsByMember(data['owner']),
                    "Owner missed hidden project (getProjectIdsByMember)")

        self.failIf(watcherClient.server.getProjectIdsByMember(data['owner']),
                    "Watcher saw hidden project (getProjectIdsByMember)")

        self.assertRaises(ItemNotFound, nobodyClient.server.getMembersByProjectId,
                          data['projectId'])

        adminClient.server.getOwnersByProjectName(project.getName())

        self.assertRaises(ItemNotFound, nobodyClient.userHasRequested,
                data['projectId'], data['owner'])

        self.assertRaises(ItemNotFound, nobodyClient.setJoinReqComments,
                data['projectId'], "foo")
        self.assertRaises(ItemNotFound, nobodyClient.getJoinReqComments,
                data['projectId'], data['user'])
        self.assertRaises(ItemNotFound, nobodyClient.deleteJoinRequest,
                data['projectId'], data['owner'])
        self.assertRaises(ItemNotFound, nobodyClient.listJoinRequests,
                data['projectId'])

        self.assertRaises(ItemNotFound, nobodyProject.addMemberById,
                          data['nobody'], userlevels.USER)

        self.assertRaises(ItemNotFound, nobodyClient.server.lastOwner,
                          data['projectId'], data['owner'])
        self.assertRaises(ItemNotFound, nobodyClient.server.onlyOwner,
                          data['projectId'], data['owner'])
        self.assertRaises(ItemNotFound,
                          watcherClient.server.delMember, data['projectId'],
                          data['user'], False)

        ownerClient.server.getUserLevel(data['user'], data['projectId'])

        adminClient.unhideProject(data['projectId'])

    @fixtures.fixture("Full")
    def testDisableProject(self, db, data):

        adminClient = self.getClient("admin")
        ownerClient = self.getClient("owner")
        developerClient = self.getClient("developer")
        watcherClient = self.getClient("user")
        nobodyClient = self.getClient("nobody")

        adminClient.disableProject(data['projectId'])

        # try getting the project from various levels
        adminClient.getProject(data['projectId'])

        self.assertRaises(ItemNotFound, ownerClient.getProject,
                data['projectId'])

        self.assertRaises(ItemNotFound, nobodyClient.getProject,
                data['projectId'])

        self.assertRaises(ItemNotFound, watcherClient.getProject,
                data['projectId'])

        adminClient.enableProject(data['projectId'])
        adminClient.getProject(data['projectId'])
        ownerClient.getProject(data['projectId'])
        nobodyClient.getProject(data['projectId'])
        watcherClient.getProject(data['projectId'])

    @fixtures.fixture("Full")
    def testCreateExternalProject(self, db, data):
        # ensure only site admins can create external projects
        nobodyClient = self.getClient("nobody")
        self.assertRaises(PermissionDenied, nobodyClient.newExternalProject,
                          'rPath Linux', 'rpath', 'rpath.local',
                          'conary.rpath.com@rpl:devel', '')

        adminClient = self.getClient("admin")
        projectId = adminClient.newExternalProject('rPath Linux', 'rpath',
                          'rpath.local',
                          'conary.rpath.com@rpl:devel', '')

        project = adminClient.getProject(projectId)
        self.failUnless(project.external, "created project was not external")

        # ensure project users table was populated.
        assert(project.onlyOwner(data['admin']))
        assert(not project.lastOwner(data['admin']))

        # ensure labels table was populated.
        self.failIf(project.getLabel() != 'conary.rpath.com@rpl:devel',
                    "Improper labels table entry for external project")

    @fixtures.fixture("Full")
    def testBlankExtProjectUrl(self, db, data):

        reposUrl = 'http://bar.rpath.local/conary/'
        adminClient = self.getClient('admin')

        # let system set url by leaving it blank
        projectId = adminClient.newExternalProject('Bar', 'bar',
               'rpath.local', 'bar.rpath.local@rpl:devel', '')

        project = adminClient.getProject(projectId)
        labelId = project.getLabelIdMap()['bar.rpath.local@rpl:devel']

        cu = db.cursor()
        cu.execute("SELECT url FROM Labels WHERE labelId=?", labelId)
        url = cu.fetchall()[0][0]

        self.failIf(url != reposUrl,
                    "repos url was lost in translation. expected %s, got %s" %\
                    (reposUrl, url))

    @fixtures.fixture("Full")
    def testSetExtProjectUrl(self, db, data):
        adminClient = self.getClient("admin")

        reposUrl = 'http://some.repos/conary'

        # set url manually
        projectId = adminClient.newExternalProject('Bar', 'bar',
                                              'rpath.local',
                                              'bar.rpath.local@rpl:devel',
                                              reposUrl)

        project = adminClient.getProject(projectId)
        labelId = project.getLabelIdMap()['bar.rpath.local@rpl:devel']

        cu = db.cursor()
        cu.execute("SELECT url FROM Labels WHERE labelId=?", labelId)
        url = cu.fetchall()[0][0]

        self.failIf(url != reposUrl,
                    "repos url was lost in translation. expected %s, got %s" %\
                    (reposUrl, url))

    @fixtures.fixture("Full")
    def testDuplicateProjects(self, db, data):
        # fixture already has a foo project, so we try to create duplicates
        client = self.getClient("owner")
        self.assertRaises(DuplicateHostname,
            client.newProject, "Hello World", "foo", "localhost")
        self.assertRaises(DuplicateName,
            client.newProject, "Foo", "another", "localhost")

    @fixtures.fixture("Full")
    def testOwnerMirror(self, db, data):
        ownerClient = self.getClient('owner')
        project = ownerClient.getProject(data['projectId'])
        canMirror = self.getMirrorAcl(project, 'owner')

        self.failUnless(canMirror, "Project owner does not have mirror ACL.")

    @fixtures.fixture("Full")
    def testRemovedMirror(self, db, data):
        ownerClient = self.getClient('owner')

        project = ownerClient.getProject(data['projectId'])
        project.delMemberById(data['developer'])
        project.delMemberById(data['owner'])

        canMirror = self.getMirrorAcl(project, 'owner')

        self.failIf(canMirror is not None,
                    "Project owner's ACL outlived membership.")

    @fixtures.fixture("Full")
    def testDevelMirror(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        canMirror = self.getMirrorAcl(project, 'developer')

        self.failIf(canMirror, "Project developer has mirror ACL.")

    @fixtures.fixture("Full")
    def testPromotedMirror(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])

        # ensure a promoted member gets same treatment as others
        project.addMemberById(data['developer'], userlevels.OWNER)
        canMirror = self.getMirrorAcl(project, 'developer')

        self.failUnless(canMirror, "Promoted owner does not have mirror ACL.")

    @fixtures.fixture("Full")
    def testDemotedMirror(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])

        # ensure a demoted member gets same treatment as others
        project.addMemberById(data['admin'], userlevels.OWNER)
        project.addMemberById(data['owner'], userlevels.DEVELOPER)
        canMirror = self.getMirrorAcl(project, 'owner')

        self.failIf(canMirror, "Demoted project developer has mirror ACL.")

    @fixtures.fixture("Full")
    def testAuthUserMirror(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        canMirror = self.getMirrorAcl(project, self.cfg.authUser)

        self.failUnless(canMirror, "Auth user does not have mirror ACL.")

    @fixtures.fixture("Full")
    def testDemotedWrite(self, db, data):
        client = self.getClient('developer')
        project = client.getProject(data['projectId'])
        self.failIf(not self.getWriteAcl(project, 'developer'),
                    "Developer does not have write access")
        project.addMemberByName('developer', userlevels.USER)
        self.failIf(self.getWriteAcl(project, 'developer'),
                    "Demoted user has write access")

    @fixtures.fixture("Full")
    def testPromotedWrite(self, db, data):
        client = self.getClient('owner')
        project = client.getProject(data['projectId'])
        self.failIf(self.getWriteAcl(project, 'user'),
                    "User has write access")
        project.addMemberByName('user', userlevels.DEVELOPER)
        self.failIf(not self.getWriteAcl(project, 'user'),
                    "Promoted developer does not have write access")

    @fixtures.fixture("Full")
    def testAdminAcl(self, db, data):
        client = self.getClient('owner')
        project = client.getProject(data['projectId'])
        self.failIf(self.getAdminAcl(project, 'owner') != \
                    self.cfg.projectAdmin,
                    "Owner admin acl does not reflect site default")
        projectAdmin = self.cfg.projectAdmin
        try:
            self.cfg.projectAdmin = False
            project.addMemberByName('user', userlevels.OWNER)
            self.failIf(self.getAdminAcl(project, 'user') != False,
                    "Owner has admin access")
            self.cfg.projectAdmin = True
            project.addMemberByName('developer', userlevels.OWNER)
            self.failIf(self.getAdminAcl(project, 'developer') != True,
                    "Owner does not have admin access")
        finally:
            self.cfg.projectAdmin = projectAdmin

    @fixtures.fixture("Empty")
    def testAdminNewProject(self, db, data):
        client = self.getClient('test')
        adminNewProjects = self.cfg.adminNewProjects
        try:
            self.cfg.adminNewProjects = False
            # ensure no errors
            client.newProject('Test', 'test', 'rpath.local')
            self.cfg.adminNewProjects = True
            self.assertRaises(PermissionDenied,
                              client.newProject, 'Test', 'test', 'rpath.local')
        finally:
            self.cfg.adminNewProjects = adminNewProjects


class ProjectTestConaryRepository(MintRepositoryHelper):

    def testTranslatedProjectName(self):
        client, userid = self.quickMintUser("test", "testpass")

        # make sure we can properly translate a hostname with a dash in it
        # all the way to the conary handler.
        newProjectId = client.newProject("Quux", "quux-project",
                MINT_PROJECT_DOMAIN)

        project = client.getProject(newProjectId)
        cfg = project.getConaryConfig()
        assert(ConaryClient(cfg).getRepos().troveNamesOnServer("quux-project." \
                + MINT_PROJECT_DOMAIN) == [])


if __name__ == "__main__":
    testsuite.main()
