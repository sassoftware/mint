#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import testsuite
testsuite.setup()

import sys

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_PROJECT_DOMAIN, PFQDN

from mint import userlevels
from mint.database import DuplicateItem, ItemNotFound
from mint.projects import InvalidHostname, DuplicateHostname, DuplicateName, \
     DuplicateLabel
from mint.server import ParameterError, PermissionDenied
from mint import mint_error
from mint import database
from mint import urltypes

from conary import dbstore
from conary.conaryclient import ConaryClient

import fixtures

class dummyProj(object):
    def __init__(self, name):
        self.name = name

    def getName(self):
        return self.name


class ProjectTest(fixtures.FixturedUnitTest):

    def _checkMembership(self, project, expectedUserId, expectedAcl):
        return [expectedUserId, expectedAcl] in \
                [[x[0], x[2]] for x in project.getMembers()]

    def _callDeleteProjectScript(self, projectName):
        import os
        configFile = os.path.join(self.cfg.dataPath, "rbuilder.conf")
        ret = os.system('echo yes | ../scripts/deleteproject --xyzzy=%s %s > /dev/null' % (configFile, projectName))
        return ret >> 8

    @testsuite.context("quick")
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
        assert(project.getCreatorId() == 2)

    @fixtures.fixture("Full")
    def testNewProjectError(self, db, data):
        client = self.getClient("user")
        self.failUnlessRaises(InvalidHostname, client.newProject, "Test", 
                              '&bar', MINT_PROJECT_DOMAIN)
        self.failUnlessRaises(DuplicateHostname, client.newProject, "Test", 
                              'foo', MINT_PROJECT_DOMAIN)
        self.failUnlessRaises(DuplicateName, client.newProject, "Foo", 'bar',
                              MINT_PROJECT_DOMAIN)

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

    def _checkRepoMap(self, contents):
        f = open(self.cfg.conaryRcFile)
        x = f.read()
        f.close()

        contents = contents.replace("rpath.local2", MINT_PROJECT_DOMAIN)
        return x == contents

    @fixtures.fixture("Empty")
    def testConaryRc(self, db, data):
        client = self.getClient('test')
        adminClient = self.getClient('admin')

        hideProjId = client.newProject('Proj', 'proj', 'rpath.local')
        assert(self._checkRepoMap('repositoryMap proj.rpath.local http://%s/repos/proj/\n' % PFQDN) )

        adminClient.hideProject(hideProjId)
        assert(self._checkRepoMap(''))

        client.newProject('Baz', 'baz', 'rpath.local')
        assert(self._checkRepoMap('repositoryMap baz.rpath.local http://%s/repos/baz/\n' % PFQDN))

        # one regular project, one hidden project, one external project
        reposUrl = 'http://bar.rpath.local/conary/'
        exProjectId = adminClient.newExternalProject('Bar', 'bar',
                                                   'rpath.local',
                                                   'bar.rpath.local@rpl:devel',
                                                    reposUrl)
        # only the regular project will show up
        assert(self._checkRepoMap('repositoryMap baz.rpath.local http://%s/repos/baz/\n' % PFQDN))

        # two regular projects, one external project, not mirrored
        adminClient.unhideProject(hideProjId)
        # both regular projects will show up
        assert(self._checkRepoMap('repositoryMap baz.rpath.local http://%s/repos/baz/\nrepositoryMap proj.rpath.local http://%s/repos/proj/\n' %\
            (PFQDN, PFQDN)))

        exProject = client.getProject(exProjectId)
        # two regular projects, one external project, mirrored
        adminClient.addInboundMirror(exProjectId, [ exProject.getLabel() ],
            "http://www.example.com/conary/",
            "mirror", "mirrorpass")
        # all projects will show up
        assert(self._checkRepoMap('repositoryMap baz.rpath.local http://%s/repos/baz/\n'
                                  'repositoryMap proj.rpath.local http://%s/repos/proj/\n'
                                  'repositoryMap bar.rpath.local http://bar.rpath.local/conary/\n' % \
                                  (PFQDN, PFQDN)))

    @fixtures.fixture('Full')
    def testGenConaryRc(self, db, data):
        client = self.getClient('admin')
        createConaryRcFile = self.cfg.createConaryRcFile
        try:
            self.cfg.createConaryRcFile = False
            # ensure conaryrc file is not generated
            assert(client.server._server._generateConaryRcFile() is False)
            self.cfg.createConaryRcFile = True
            # ensure conaryrc file is generated
            assert(client.server._server._generateConaryRcFile() is None)
        finally:
            self.cfg.createConaryRcFile = createConaryRcFile

    @fixtures.fixture("Empty")
    def testBrokenVersion(self, db, data):
        client = self.getClient('test')
        self.assertRaises(ItemNotFound, client.versionIsExternal, 'foo')

    @fixtures.fixture('Full')
    def testProjectVersion(self, db, data):
        client = self.getClient('admin')
        project = client.getProject(data['projectId'])
        label = project.getLabel()
        versionStr = '/' + label + '/1.0.2-2-1'
        assert(client.versionIsExternal(versionStr) == project.external)
        cu = db.cursor()
        cu.execute('UPDATE Projects SET external=1 WHERE projectId=?', project.id)
        db.commit()
        project.refresh()
        assert(client.versionIsExternal(versionStr) == project.external)

    @fixtures.fixture('Full')
    def testMissingProjectVersion(self, db, data):
        client = self.getClient('admin')
        project = client.getProject(data['projectId'])
        label = project.getLabel()
        versionStr = '/' + label + '/1.0.2-2-1'
        cu = db.cursor()
        cu.execute('DELETE FROM Projects WHERE projectId=?', project.id)
        db.commit()
        # result must always be true
        assert(client.versionIsExternal(versionStr))

    @fixtures.fixture('Full')
    def testProjectUrl(self, db, data):
        client = self.getClient('admin')
        preUrl = 'foo2.rpath.local/conary'
        postUrl = 'http://' + preUrl

        projectId = client.newProject('Foo 2', 'foo2', 'rpath.local2',
                                      preUrl, 'desc')

        project = client.getProject(projectId)
        assert(postUrl == project.getProjectUrl())

    @fixtures.fixture('Full')
    def testInvalidLabelExtProj(self, db, data):
        client = self.getClient('admin')
        self.assertRaises(ParameterError, client.newExternalProject, 'Foo 2',
                          'foo2', 'rpath.local2', 'bad-label', '', False)

    @fixtures.fixture('Empty')
    def testMyProjCompUL(self, db, data):
        projectsList = (('foo', userlevels.OWNER),
                        ('bar', userlevels.DEVELOPER))
        assert userlevels.myProjectCompare(*projectsList) == -1
        assert userlevels.myProjectCompare(*reversed(projectsList)) == 1

    @fixtures.fixture('Empty')
    def testMyProjCompName(self, db, data):
        projectsList = ((dummyProj('foo'), userlevels.OWNER),
                        (dummyProj('bar'), userlevels.OWNER))
        assert userlevels.myProjectCompare(*projectsList) == 1
        assert userlevels.myProjectCompare(*reversed(projectsList)) == -1

    @fixtures.fixture('Empty')
    def testMyProjCompEq(self, db, data):
        projectsList = ((dummyProj('foo'), userlevels.OWNER),
                        (dummyProj('foo'), userlevels.OWNER))
        assert userlevels.myProjectCompare(*projectsList) == 0
        assert userlevels.myProjectCompare(*reversed(projectsList)) == 0

    @fixtures.fixture('Full')
    def testInitTimeModified(self, db, data):
        client = self.getClient('admin')
        project = client.getProject(data['projectId'])
        assert project.timeModified == project.getTimeModified()
        assert project.timeModified == project.timeCreated

    @fixtures.fixture('Full')
    def testBadPFQDN(self, db, data):
        client = self.getClient('admin')
        project = client.getProject(data['projectId'])
        self.assertRaises(ItemNotFound,
                          client.server._server.projects.getProjectIdByFQDN,
                          'bad.name')
        self.assertRaises(ItemNotFound,
                          client.server._server.getProjectIdByFQDN,
                          'not.in.the.db')

    @fixtures.fixture('Full')
    def testDefaultedLabel(self, db, data):
        client = self.getClient('admin')
        project = client.getProject(data['projectId'])
        cu = db.cursor()
        cu.execute("UPDATE LABELS SET url=''")
        db.commit()
        project.refresh()
        labelData = client.server._server.getLabelsForProject(project.id,
                                                              False, '', '')
        assert labelData[1].values()[0] == 'http://foo.%s/conary/' % MINT_PROJECT_DOMAIN

    @fixtures.fixture('Full')
    def testDuplicateLabel(self, db, data):
        client = self.getClient('admin')
        project = client.getProject(data['projectId'])
        self.assertRaises(DuplicateLabel, project.addLabel,
                          project.getLabel(), '')

    @fixtures.fixture('Full')
    def testDeleteProjectScript(self, db, data):
        client = self.getClient('admin')
        project = client.getProject(data['projectId'])
        projectName = project.hostname
        del project

        # call the database deletion script
        self.failUnless(self._callDeleteProjectScript(projectName) == 0,
                "Script exited with non-zero exit code")

        # check for remnants
        self.assertRaises(database.ItemNotFound, client.getProject, data['projectId'])

    @fixtures.fixture('Full')
    def testDeleteLocalMirrorProjectScript(self, db, data):
        client = self.getClient('admin')
        project = client.getProject(data['projectId'])
        projectName = project.hostname
        cu = db.cursor()
        cu.execute("INSERT INTO InboundMirrors (targetProjectId, sourceLabels, sourceUrl, sourceUsername, sourcePassword) VALUES(?, '', '', '', '')", project.id)
        db.commit()
        project.refresh()
        del project

        # call the database deletion script
        self.failUnless(self._callDeleteProjectScript(projectName) == 0,
                "Script exited with non-zero exit code")

        # check for remnants
        self.assertRaises(database.ItemNotFound, client.getProject, data['projectId'])

    @fixtures.fixture('Full')
    def testDeleteExtraUrlsProjectScript(self, db, data):
        # extra mirror URLs (e.g. Amazon S3) should be left behind; only
        # urltypes.LOCAL should be deleted
        client = self.getClient('admin')
        project = client.getProject(data['projectId'])
        projectName = project.hostname
        build = client.getBuild(data['anotherBuildId'])
        buildFiles = build.getFiles()
        assert(len(buildFiles) == 1)
        fileId = buildFiles[0]['fileId']

        build.addFileUrl(fileId, urltypes.AMAZONS3, "http://s3.amazonaws.com/rbuilder/foo.iso")
        build.addFileUrl(fileId, urltypes.AMAZONS3TORRENT, "http://s3.amazonaws.com/rbuilder/foo.iso?torrent")

        cu = db.cursor()
        cu.execute("""SELECT fu.urlId
                      FROM BuildFilesUrlsMap bfum
                           LEFT OUTER JOIN FilesUrls fu USING (urlId)
                           WHERE bfum.fileId = ?
                              AND fu.urlType IN (?, ?)""", fileId,
                              urltypes.AMAZONS3, urltypes.AMAZONS3TORRENT)

        expectedUrlIds = [ x[0] for x in cu.fetchall() ]

        # call the database deletion script
        self.failUnless(self._callDeleteProjectScript(projectName) == 0,
                "Script exited with non-zero exit code")

        # make sure some things are left behind!
        self.assertRaises(database.ItemNotFound, client.getProject, data['anotherBuildId'])
        cu.execute("""SELECT COUNT(*) FROM BuildFilesUrlsMap WHERE fileId = ?""", fileId)
        self.failUnlessEqual(cu.fetchall()[0][0], 0, "BuildFilesUrlsMap query should be empty")
        cu.execute("""SELECT COUNT(*) FROM FilesUrls WHERE urlId IN ( %s )""" % ','.join([str(x) for x in expectedUrlIds]))
        self.failUnlessEqual(cu.fetchall()[0][0], len(expectedUrlIds), "FilesUrls query should contain two URL types that are non local")

    @fixtures.fixture('Full')
    def testLocalMirror(self, db, data):
        client = self.getClient('admin')
        project = client.getProject(data['projectId'])
        self.failIf(client.isLocalMirror(project.id),
                    "project is local mirror without inbound label")

        cu = db.cursor()
        cu.execute("INSERT INTO InboundMirrors (targetProjectId, sourceLabels, sourceUrl, sourceUsername, sourcePassword) VALUES(?, '', '', '', '')", project.id)
        db.commit()
        project.refresh()
        self.failIf(not client.isLocalMirror(project.id),
                    "project is not local mirror with inbound label")

    @fixtures.fixture('Full')
    def testHideAllProjects(self, db, data):
        client = self.getClient('nobody')

        client.server._server.cfg.hideNewProjects = True
        projectId = client.newProject("Quux", "quux", "localhost")

        project = client.getProject(projectId)
        self.failUnlessEqual(project.hidden, True)


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
