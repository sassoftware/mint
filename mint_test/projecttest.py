#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#

import testsuite
testsuite.setup()

import sys
import os
import re
import socket
import tempfile
import time
from testrunner.testhelp import SkipTestException

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_PROJECT_DOMAIN, FQDN

from mint import userlevels
from mint.mint_error import *
from mint.mint_error import ParameterError, PermissionDenied
from mint.lib import database
from mint import urltypes

from conary import dbstore
from conary.conaryclient import ConaryClient
from conary.lib import util

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
        scriptPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ret = os.system('echo yes | %s/scripts/deleteproject --xyzzy=%s %s > /dev/null'
                % (scriptPath, configFile, projectName))
        return ret >> 8

    @testsuite.context("quick")
    @fixtures.fixture("Full")
    def testBasicAttributes(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])

        assert(project.getFQDN() == "foo.%s" % MINT_PROJECT_DOMAIN)
        assert(project.getHostname() == "foo")
        assert(project.getShortname() == "foo")
        assert(project.getDomainname() == MINT_PROJECT_DOMAIN)
        assert(project.getName() == "Foo")
        assert(project.getMembers() == [ \
                [data['owner'], 'owner', userlevels.OWNER], \
                [data['developer'], 'developer', userlevels.DEVELOPER], \
                [data['user'], 'user', userlevels.USER] ])
        assert(project.hidden == 0)
        assert(project.external == 0)
        assert(project.getCreatorId() == 2)
        assert([[x[2],x[3],x[4]] for x in project.getProductVersionList()] ==
                [['ns', 'FooV1', 'FooV1Description'],['ns2', 'FooV2', 'FooV2Description']])

    @fixtures.fixture("Full")
    def testNewProjectError(self, db, data):
        client = self.getClient("user")
        self.failUnlessRaises(InvalidHostname, client.newProject, "Test", 
                              '&bar', MINT_PROJECT_DOMAIN, shortname="bar")
        self.failUnlessRaises(DuplicateHostname, client.newProject, "Test", 
                              'foo', MINT_PROJECT_DOMAIN, shortname="foo",
                              version='1.0', prodtype='Component')

        self.mock(socket, 'gethostname', lambda: 'sir.robin')
        sData = re.split("\.", socket.gethostname(), 1)
        self.failUnlessRaises(InvalidHostname, client.newProject, "Foo", 
                              sData[0], sData[1], shortname='bar3')
        self.failUnlessRaises(InvalidShortname, client.newProject, "Test", 
                          'barbar', MINT_PROJECT_DOMAIN, shortname="&bar")
        self.failUnlessRaises(ProductVersionInvalid, client.newProject, "Test", 
                          'barbar', MINT_PROJECT_DOMAIN, 
                           shortname="barbara", version="")
        self.failUnlessRaises(ProductVersionInvalid, client.newProject, "Test", 
                          'barbar', MINT_PROJECT_DOMAIN, 
                           shortname="barbara", version="9 8")

    @fixtures.fixture("Full")
    def testNewProjectWithNamespace(self, db, data):
        client = self.getClient('owner')
        hostname=shortname = "foo2"
        namespace = 'ns1'
        newProjectId = client.newProject("Foo2", hostname, MINT_PROJECT_DOMAIN,
                                         shortname=shortname,
                                         namespace=namespace,
                                         version='1.0', prodtype='Component')
        project = client.getProject(newProjectId)

        #Invalid product
        self.assertRaises(InvalidNamespace, client.newProject, 'Foo3', hostname, MINT_PROJECT_DOMAIN,
                                         shortname=shortname, namespace='0123456789abcdefg',
                                         version='1.1', prodtype='Component')

    @fixtures.fixture("Full")
    def testEditProject(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        project.editProject("http://example.com/", "Description", "Foo Title")
        project.refresh()

        assert(project.getName() == "Foo Title")
        assert(project.getDesc() == "Description")
        assert(project.getProjectUrl() == "http://example.com/")

        # test automatic prepending of http://
        project.editProject("www.example.com", "Description", "Foo Title")
        project.refresh()
        assert(project.getProjectUrl() == "http://www.example.com")

        # except when there's no project URL
        project.editProject("", "Description", "Foo Title")
        project.refresh()
        assert(project.getProjectUrl() == "")

        self.failUnlessEqual(project.commitEmail, "")
        project.setCommitEmail("commit@email.com")
        project.refresh()
        self.failUnlessEqual(project.commitEmail, "commit@email.com")
        
    @fixtures.fixture("Full")
    def testEditProjectNamespace(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        project.setNamespace("spacemonkey")
        project.refresh()

        assert(project.getNamespace() == "spacemonkey")

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
                projectId = client.newProject("Quux", hostname, 'localhost',
                                            shortname='validone',
                                            version='1.0', prodtype='Component')
                self.fail("allowed to create a project with a bad name")
            except InvalidHostname:
                pass
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if str(exc_value).split(' ')[0] != 'ParameterError':
                    raise

    @fixtures.fixture("Full")
    def testBadShortname(self, db, data):
        client = self.getClient("owner")
        for shortname in ('admin', 'a bad name', '', 'a_bad_name', 'a.bad.name'):
            try:
                projectId = client.newProject("Quux", 'validhn', 'localhost',
                                            shortname=shortname,
                                            version='1.0', prodtype='Component')
                self.fail("allowed to create a project with a bad short name")
            except InvalidShortname:
                pass
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if str(exc_value).split(' ')[0] != 'ParameterError':
                    raise

    @fixtures.fixture("Full")
    def testVersion(self, db, data):
        client = self.getClient("owner")
        projectId = client.newProject("Quux", 'footoo', 'localhost',
                                    shortname="footoo", version="9.7",
                                    prodtype='Component')
        project = client.getProject(projectId)
        assert(project.getVersion() == "9.7")

    @fixtures.fixture("Full")
    def testProdTypeAppliance(self, db, data):

        client = self.getClient("owner")
        projectId = client.newProject("Quux", 'footoo', 'localhost', 
                                  shortname="footoo", prodtype="Appliance",
                                  version="1.0")
        project = client.getProject(projectId)
        assert(project.getProdType() == "Appliance")
        if not self.cfg.rBuilderOnline:
            assert(project.getApplianceValue() == "yes")
        else:
            assert(project.getApplianceValue() == "unknown")

    @fixtures.fixture("Full")
    def testProdTypeComponentApplianceValUnknown(self, db, data):
        client = self.getClient("owner")
        projectId = client.newProject("Quux", 'footoo', 'localhost',
                                      shortname="footoo", prodtype="Component",
                                      version="1.0")
        project = client.getProject(projectId)
        assert(project.getProdType() == "Component")
        assert(project.getApplianceValue() == "no")

    @fixtures.fixture("Full")
    def testProdTypeComponentApplianceValNo(self, db, data):
        client = self.getClient("owner")
        projectId = client.newProject("Quux", 'footoo', 'localhost', 
                                      appliance="no",
                                      shortname="footoo", prodtype="Component",
                                      version="1.0")
        project = client.getProject(projectId)
        assert(project.getProdType() == "Component")
        assert(project.getApplianceValue() == "no")

    @fixtures.fixture("Full")
    def testCommitEmail(self, db, data):
        client = self.getClient("owner")
        projectId = client.newProject("Quux", 'footoo', 'localhost',
                                      appliance="no",
                                      shortname="footoo", prodtype="Component",
                                      version="1.0", commitEmail="foo@bar.net")
        project = client.getProject(projectId)
        assert(project.getCommitEmail() == "foo@bar.net")

    @fixtures.fixture("Full")
    def testCommitEmailBlank(self, db, data):
        client = self.getClient("owner")
        projectId = client.newProject("Quux", 'footoo', 'localhost',
                                      appliance="no",
                                      shortname="footoo", prodtype="Component",
                                      version="1.0")
        project = client.getProject(projectId)
        assert(project.getCommitEmail() == "")

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
        hostname = "quux"
        newProjectId = nobodyClient.newProject("Quux", hostname, "localhost",
                                            shortname=hostname,
                                            version='1.0', prodtype='Component')
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

        # This no longer raises ItemNotFound because normal users can browse
        # private products they are a member of.
        watcherClient.getProject(data['projectId'])

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

        # This no longer raises ItemNotFound, a user can be deleted from a
        # private product they are a member of.
        watcherClient.server.delMember(data['projectId'], data['user'], False)

        self.assertRaises(ItemNotFound, ownerClient.server.getUserLevel, data['user'], 
                          data['projectId'])

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
        # make sure it is a repo by default, RBL-4938
        self.failUnless(project.prodtype == "Repository", "created project was not repository")

        # ensure project users table was populated.
        assert(project.onlyOwner(data['admin']))
        assert(not project.lastOwner(data['admin']))

        # ensure labels table was populated.
        self.failIf(project.getLabel() != 'conary.rpath.com@rpl:devel',
                    "Improper labels table entry for external project")

        x = adminClient.server._server._getProjectRepo(project)
        self.failIf(x is None)

        # test with invalid hostnames
        self.failUnlessRaises(InvalidHostname, adminClient.newExternalProject,
                              "Foo",  "www", MINT_PROJECT_DOMAIN, "label",
                              "url")

        # mock out hostname for consistency
        self.mock(socket, 'gethostname', lambda: 'sir.galahad')
        sData = re.split("\.", socket.gethostname(), 1)

        self.failUnlessRaises(InvalidHostname, adminClient.newExternalProject,
                              "Foo", sData[0], sData[1], "label", "url")
        self.failUnlessRaises(InvalidHostname, adminClient.newExternalProject,
                              "Test", '&bar', MINT_PROJECT_DOMAIN, "label",
                              "url")

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
            client.newProject, "Hello World", "foo", "localhost", 
                    shortname="foo", version='1.0', prodtype='Component')

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
    def testPromotedMirrorAcls(self, db, data):
        client = self.getClient('owner')
        project = client.getProject(data['projectId'])
        self.failIf(self.getMirrorAcl(project, 'developer'),
                    "Developer has mirror access")
        project.updateUserLevel(data['developer'], userlevels.OWNER)
        self.failIf(not self.getMirrorAcl(project, 'developer'),
                    "Promoted developer -> owner does not have mirror access")

        project.updateUserLevel(data['developer'], userlevels.DEVELOPER)
        self.failIf(self.getMirrorAcl(project, 'developer'),
            "Demoted owner -> developer still has mirror access")

    @fixtures.fixture("Full")
    def testAdminAcl(self, db, data):
        import epdb
        epdb.stc('f')
        client = self.getClient('owner')
        project = client.getProject(data['projectId'])
        self.failUnless(self.getAdminAcl(project, 'owner'),
                "Owner does not have admin access")

        project.addMemberByName('developer', userlevels.OWNER)
        self.failIf(self.getAdminAcl(project, 'developer') != True,
                "Owner does not have admin access")

    @fixtures.fixture("Empty")
    def testAdminNewProject(self, db, data):
        client = self.getClient('test')
        adminNewProjects = self.cfg.adminNewProjects
        try:
            self.cfg.adminNewProjects = False
            # ensure no errors
            hostname = shortname = "test"
            client.newProject('Test', hostname, 'rpath.local', 
                              shortname=shortname,
                              version='1.0', prodtype='Component')
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
        self.failUnlessEqual(set(x.split("\n")), set(contents.split("\n")))

    @fixtures.fixture("Empty")
    def testConaryRc(self, db, data):
        client = self.getClient('test')
        adminClient = self.getClient('admin')

        hostname="proj"
        hideProjId = client.newProject('Proj', hostname, 'rpath.local',
                                       shortname=hostname,
                                       version='1.0', prodtype='Component')
        self._checkRepoMap('repositoryMap proj.rpath.local http://%s/repos/proj/\n' % FQDN)

        adminClient.hideProject(hideProjId)
        self._checkRepoMap('')

        hostname="baz"
        client.newProject('Baz', hostname, 'rpath.local', shortname=hostname,
                version='1.0', prodtype='Component')
        self._checkRepoMap('repositoryMap baz.rpath.local http://%s/repos/baz/\n' % FQDN)

        # one regular project, one hidden project, one external project
        reposUrl = 'http://bar.rpath.local/conary/'
        exProjectId = adminClient.newExternalProject('Bar', 'bar',
                                                   'rpath.local',
                                                   'bar.rpath.local@rpl:devel',
                                                    reposUrl)
        # only the regular project will show up
        self._checkRepoMap('repositoryMap baz.rpath.local http://%s/repos/baz/\n' % FQDN)

        # another external project with a repository map:
        adminClient.newExternalProject('Wobble', 'wobble',
                                       'rpath.local',
                                       'wobble.rpath.com@rpl:devel',
                                       'http://wobble-commits.rpath.com/conary/')

        # this external project will show up:
        self._checkRepoMap('repositoryMap baz.rpath.local http://%s/repos/baz/\n'
                           'repositoryMap wobble.rpath.com http://wobble-commits.rpath.com/conary/\n' % FQDN)

        # two regular projects, one external project, not mirrored
        adminClient.unhideProject(hideProjId)
        # both regular projects will show up
        self._checkRepoMap('repositoryMap baz.rpath.local http://%s/repos/baz/\n'
                           'repositoryMap wobble.rpath.com http://wobble-commits.rpath.com/conary/\n'
                           'repositoryMap proj.rpath.local http://%s/repos/proj/\n' % (FQDN, FQDN))

        exProject = client.getProject(exProjectId)
        # two regular projects, one external project, mirrored
        adminClient.addInboundMirror(exProjectId, [ exProject.getLabel() ],
            "http://www.example.com/conary/",
            "mirror", "mirrorpass")
        # all projects will show up
        self._checkRepoMap('repositoryMap baz.rpath.local http://%s/repos/baz/\n'
                           'repositoryMap proj.rpath.local http://%s/repos/proj/\n'
                           'repositoryMap bar.rpath.local http://bar.rpath.local/conary/\n'
                           'repositoryMap wobble.rpath.com http://wobble-commits.rpath.com/conary/\n' % \
                           (FQDN, FQDN))

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

    @fixtures.fixture('Full')
    def testProjectUrl(self, db, data):
        client = self.getClient('admin')
        preUrl = 'foo2.rpath.local/conary'
        postUrl = 'http://' + preUrl

        hostname = "foo2"
        projectId = client.newProject('Foo 2', hostname, 'rpath.local2',
                                      preUrl, 'desc', shortname=hostname,
                                      version='1.0', prodtype='Component')

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
    def testDeleteProject(self, db, data):
        if db.driver == 'sqlite':
            raise SkipTestException("test requires working foreign key constraints")
        client = self.getClient('admin')
        project = client.getProject(data['projectId'])
        
        # make sure there is at least 1 build
        self.failUnless(len(client.server._server.getBuildsForProject(project.id)) > 0, 
            "Need at least one build for a valid test")
        
        # make sure there is at least 1 published release
        self.failUnless(len(client.server._server.getPublishedReleasesByProject(project.id)) > 0, 
            "Need at least one published release for a valid test")
        
        # make sure there is at least one membership request
        client.server._server.membershipRequests.setComments(project.id, '80', 'some comment')
        self.failUnless(len(client.server._server._listAllJoinRequests(project.id)) > 0, 
            "Need at least one membership request for a valid test")
        
        # make sure there is at least 1 commit
        client.server.registerCommit(project.getFQDN(), 'testuser', 'mytrove:source',
                                     '/testproject.' + MINT_PROJECT_DOMAIN + '@rpl:devel/1.0-1')
        self.failUnless(len(client.server._server.getCommitsForProject(project.id)) > 0, 
            "Need at least one commit for a valid test")
        
        # make sure there is at least 1 project user
        self.failUnless(len(client.server._server.getMembersByProjectId(project.id)) > 0, 
            "Need at least one project user for a valid test")        
        
        # make sure there is an inbound and outbound mirror
        client.addInboundMirror(project.id, ['conary.rpath.com@rpl:1'],
            'http://example.com/conary/', 'user', 'pass')
        client.addOutboundMirror(project.id,
                ["localhost.rpath.local2@rpl:devel"], allLabels = True)

        # add image files
        imageDir = os.path.join(self.cfg.imagesPath, project.hostname)
        os.mkdir(imageDir)
        f = open(os.path.join(imageDir, "someimagefile"), 'w')
        f.write("...")
        f.close()

        # delete the project
        self.failUnless(client.deleteProject(project.id) == True, "Failed deleting project")

        # make sure project is gone
        self.assertRaises(database.ItemNotFound, client.getProject, data['projectId'])
        
        # make sure images dir is gone
        self.failUnless(not os.path.exists(imageDir))
        
        # make sure the builds have been removed
        cu = db.cursor()
        cu.execute("SELECT COUNT(*) FROM Builds WHERE projectId = ?", project.id)
        self.failUnlessEqual(cu.fetchone()[0], 0)

        # make sure the published releases have been removed
        cu.execute("SELECT COUNT(*) FROM PublishedReleases WHERE projectId = ?", project.id)
        self.failUnlessEqual(cu.fetchone()[0], 0)

        # make sure the membership requests have been removed
        cu.execute("SELECT COUNT(*) FROM MembershipRequests WHERE projectId = ?", project.id)
        self.failUnlessEqual(cu.fetchone()[0], 0)

        # make sure commits have been removed
        cu.execute("SELECT COUNT(*) FROM Commits WHERE projectId = ?", project.id)
        self.failUnlessEqual(cu.fetchone()[0], 0)

        # make sure project user references have been removed
        cu.execute("SELECT COUNT(*) FROM ProjectUsers WHERE projectId = ?", project.id)
        self.failUnlessEqual(cu.fetchone()[0], 0)

        # make sure mirrors are gone
        cu.execute("SELECT COUNT(*) FROM InboundMirrors WHERE targetProjectId = ?", project.id)
        self.failUnlessEqual(cu.fetchone()[0], 0)
        cu.execute("SELECT COUNT(*) FROM OutboundMirrors WHERE sourceProjectId = ?", project.id)
        self.failUnlessEqual(cu.fetchone()[0], 0)

        # make sure project labels are gone
        cu.execute("SELECT COUNT(*) FROM Labels WHERE projectId = ?", project.id)
        self.failUnlessEqual(cu.fetchone()[0], 0)

    @fixtures.fixture('Full')
    def testDeleteExternalProject(self, db, data):
        client = self.getClient('admin')
        projectId = client.newExternalProject('rPath Linux', 'rpath',
                          'rpath.local', 'conary.rpath.com@rpl:devel', '')

        project = client.getProject(projectId)
        self.failUnless(client.deleteProject(project.id) == True, "Allow deleting external projects")
        
    @fixtures.fixture('Full')
    def testDeleteExternalProjectLocalMirror(self, db, data):
        client = self.getClient('admin')
        projectId = client.newExternalProject('rPath Linux', 'rpath',
                          'rpath.local', 'conary.rpath.com@rpl:devel', '')

        project = client.getProject(projectId)
        client.addInboundMirror(project.id, ['conary.rpath.com@rpl:1'],
            'http://example.com/conary/', 'user', 'pass')
        project.refresh()

        # call the database deletion script
        self.failUnless(client.deleteProject(project.id) == True, "Allow deleting external projects if local mirror")
        
    @testsuite.tests('RBL-4225')
    @fixtures.fixture('Full')
    def testDeleteProjectNotAdmin(self, db, data):
        adminClient = self.getClient('admin')
        project = adminClient.getProject(data['projectId'])
        
        client = self.getClient('owner')
        self.assertRaises(PermissionDenied, client.deleteProject, project.id)

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
        cu.execute("""INSERT INTO InboundMirrors
            (targetProjectId, sourceLabels, sourceUrl,
            sourceAuthType)
            VALUES(?, '', '', 'none')""", project.id)
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
        if db.driver == 'sqlite':
            raise SkipTestException("test requires working foreign key constraints")
        client = self.getClient('admin')
        project = client.getProject(data['projectId'])
        projectName = project.hostname
        build = client.getBuild(data['anotherBuildId'])
        buildFiles = build.getFiles()
        assert(len(buildFiles) == 1)
        fileId = buildFiles[0]['fileId']

        build.addFileUrl(fileId, urltypes.AMAZONS3, "http://s3.amazonaws.com/rbuilder/foo.iso")
        build.addFileUrl(fileId, urltypes.AMAZONS3TORRENT, "http://s3.amazonaws.com/rbuilder/foo.iso?torrent")

        # call the database deletion script
        self.failUnless(self._callDeleteProjectScript(projectName) == 0,
                "Script exited with non-zero exit code")

        # make sure some things are left behind!
        cu = db.cursor()
        self.assertRaises(database.ItemNotFound, client.getProject, data['anotherBuildId'])
        cu.execute("""SELECT COUNT(*) FROM BuildFilesUrlsMap WHERE fileId = ?""", fileId)
        self.failUnlessEqual(cu.fetchall()[0][0], 0, "BuildFilesUrlsMap query should be empty")
        cu.execute("""SELECT COUNT(*) FROM FilesUrls WHERE urlId IN ( %s )""" % ','.join([str(x) for x in expectedUrlIds]))
        self.failUnlessEqual(cu.fetchall()[0][0], 0, "FilesUrls query should be empty")

    @fixtures.fixture('Full')
    def testLocalMirror(self, db, data):
        client = self.getClient('admin')
        project = client.getProject(data['projectId'])
        self.failIf(client.isLocalMirror(project.id),
                    "project is local mirror without inbound label")

        cu = db.cursor()
        cu.execute('''INSERT INTO InboundMirrors (targetProjectId,
            sourceLabels, sourceUrl, sourceAuthType) VALUES(?, '', '',
            'none')''', project.id)
        db.commit()
        project.refresh()
        self.failIf(not client.isLocalMirror(project.id),
                    "project is not local mirror with inbound label")

    @fixtures.fixture('Full')
    def testEditMirror(self, db, data):
        client = self.getClient('admin')
        project = client.getProject(data['projectId'])

        client.addInboundMirror(project.id, ['conary.rpath.com@rpl:1'],
            'http://example.com/conary/', 'user', 'pass')

        client.editInboundMirror(project.id, ['conary.rpath.com@rpl:devel', 'conary.rpath.com@rpl:1'],
            'http://www.example.com/conary/', 'userpass', 'username', 'password', '', False)

        self.failUnlessEqual(client.getInboundMirror(project.id),
            {'inboundMirrorId': 1, 'mirrorOrder': 0,
             'sourceUrl': 'http://www.example.com/conary/',
             'sourceAuthType': 'userpass',
             'sourceUsername': 'username', 'sourcePassword': 'password',
             'sourceEntitlement': '',
             'allLabels': 0,
             'sourceLabels': 'conary.rpath.com@rpl:devel conary.rpath.com@rpl:1',
             'targetProjectId': 1}
        )

    @fixtures.fixture('Full')
    def testHideAllProjects(self, db, data):
        client = self.getClient('nobody')

        oldHideNewProjects = client.server._server.cfg.hideNewProjects
        client.server._server.cfg.hideNewProjects = True
        
        try:
            hostname = "quux"
            projectId = client.newProject("Quux", hostname, "localhost", 
                                          shortname=hostname,
                                          version='1.0', prodtype='Component')
    
            project = client.getProject(projectId)
            self.failUnlessEqual(project.hidden, True)
        finally:
            client.server._server.cfg.hideNewProjects = oldHideNewProjects
        
    @fixtures.fixture('Full')
    def testPrivateProjects(self, db, data):
        client = self.getClient('nobody')
        
        # make sure not using cfg val so we know param works
        oldHideNewProjects = client.server._server.cfg.hideNewProjects
        client.server._server.cfg.hideNewProjects = False
        
        try:
            # test public
            hostname = "manny"
            projectId = client.newProject("BoSox", hostname, "localhost", 
                                          shortname=hostname,
                                          version='1.0', prodtype='Component',
                                          isPrivate = False)
            project = client.getProject(projectId)
            self.failUnlessEqual(project.hidden, False)
            
            # test private
            hostname = "ortiz"
            projectId = client.newProject("BoSox2", hostname, "localhost", 
                                          shortname=hostname,
                                          version='1.0', prodtype='Component',
                                          isPrivate = True)
            project = client.getProject(projectId)
            self.failUnlessEqual(project.hidden, True)
        finally:
            client.server._server.cfg.hideNewProjects = oldHideNewProjects
            
    @fixtures.fixture('Full')
    def testVisibilityConversion(self, db, data):
        """
        Test converting public to private and vice versa
        """
                
        # test private to public
        client = self.getClient('owner')
        hostname = "manny"
        projectId = client.newProject("BoSox", hostname, "localhost", 
                                      shortname=hostname,
                                      version='1.0', prodtype='Component',
                                      isPrivate = True)
        project = client.getProject(projectId)
        self.failUnlessEqual(project.hidden, True)
        client.setProductVisibility(projectId, False)
        project = client.getProject(projectId)
        self.failUnlessEqual(project.hidden, False)
        
        # test public to private by owner (not allowed)
        client = self.getClient('owner')
        hostname = "ortiz"
        projectId = client.newProject("BoSox2", hostname, "localhost", 
                                      shortname=hostname,
                                      version='1.0', prodtype='Component',
                                      isPrivate = False)
        project = client.getProject(projectId)
        self.failUnlessEqual(project.hidden, False)
        self.failUnlessRaises(PublicToPrivateConversionError, 
                              client.setProductVisibility, projectId, True)
        
        # test public to private by admin (allowed)
        client = self.getClient('admin')
        hostname = "ortiz2"
        projectId = client.newProject("BoSox3", hostname, "localhost", 
                                      shortname=hostname,
                                      version='1.0', prodtype='Component',
                                      isPrivate = False)
        project = client.getProject(projectId)
        self.failUnlessEqual(project.hidden, False)
        client.setProductVisibility(projectId, True)
        project = client.getProject(projectId)
        self.failUnlessEqual(project.hidden, True)
        
        # make sure you must be owner or admin to do it at all
        client = self.getClient('nobody')
        self.failUnlessRaises(PermissionDenied, 
                              client.setProductVisibility, projectId, True)


class ProjectTestConaryRepository(MintRepositoryHelper):

    def testTranslatedProjectName(self):
        client, userid = self.quickMintUser("test", "testpass")

        # make sure we can properly translate a hostname with a dash in it
        # all the way to the conary handler.
        hostname = "quux-project"
        newProjectId = client.newProject("Quux", hostname,
                MINT_PROJECT_DOMAIN, shortname=hostname,
                version='1.0', prodtype='Component')

        project = client.getProject(newProjectId)
        cfg = project.getConaryConfig()
        assert(ConaryClient(cfg).getRepos().troveNamesOnServer("quux-project." \
                + MINT_PROJECT_DOMAIN) == [])

    def testNoCreateGroupTemplate(self):
        client, userid = self.quickMintUser("test", "testpass")

        #First, create a project without being an appliance
        hostname = "nap"
        projId = client.newProject('Not an appliance', hostname, 
                                   MINT_PROJECT_DOMAIN, appliance="no",
                                   shortname=hostname,
                                   version='1.0', prodtype='Component')
        project = client.getProject(projId)
        cfg = project.getConaryConfig()
        #This one should be empty
        self.assertEquals(ConaryClient(cfg).getRepos().troveNamesOnServer(
            'nap.' + MINT_PROJECT_DOMAIN), [])

    def testCreateGroupTemplate(self):

        client, userid = self.quickMintUser("test", "testpass")

        _groupApplianceLabel = client.server._server.cfg.groupApplianceLabel

        # set labels that don't use protected repositories so we can test
        client.server._server.cfg.groupApplianceLabel = 'conary.rpath.com@rpl:1'

        try:
            #First, create a project without being an appliance
            hostname = "nap"
            projId = client.newProject('Not an appliance', hostname, 
                        MINT_PROJECT_DOMAIN, appliance="no", shortname=hostname,
                        version='5.4', prodtype='Component')
            client.addProductVersion(projId, self.mintCfg.namespace, '5.4')
            #This one should be empty
            project = client.getProject(projId)
            cfg = project.getConaryConfig()
            trvLeaves = ConaryClient(cfg).getRepos().getAllTroveLeaves(
                    hostname + '.' + MINT_PROJECT_DOMAIN, {})
            self.assertEquals(sorted(trvLeaves.keys()),
                              ['product-definition:source'])

            hostname = "app"
            projId = client.newProject('An appliance', hostname, 
                   MINT_PROJECT_DOMAIN, appliance="yes", shortname=hostname,
                   version='5.4', prodtype='Appliance')
            client.addProductVersion(projId, self.mintCfg.namespace, '5.4')
            project = client.getProject(projId)
            cfg = project.getConaryConfig()
            #This one should have a group trove
            trvLeaves = ConaryClient(cfg).getRepos().getAllTroveLeaves(
                    '%s.' % hostname + MINT_PROJECT_DOMAIN, {})
            self.assertEquals(sorted(trvLeaves.keys()),
                    ['group-%s-appliance:source' % hostname,
                     'product-definition:source'])
            labels = trvLeaves['group-%s-appliance:source' % hostname]
            branch = '/%s.%s@%s:%s-%s-devel' % (hostname, MINT_PROJECT_DOMAIN, client.server._server.cfg.namespace, hostname, '5.4')
            self.assertEquals(len(labels), 1)
            self.assertEquals(str(labels.keys()[0].branch()), branch)
            self.assertEquals(str(labels.keys()[0].trailingRevision()), '5.4-1')
        finally:
            # reset the labels
            client.server._server.cfg.groupApplianceLabel = _groupApplianceLabel

    def testNewProjectAuthUser(self):
        client = self.openMintClient((self.mintCfg.authUser, self.mintCfg.authPass))
        projectId = client.newProject('foo', 'foo', 'rpath.local', shortname = 'foo', prodtype = 'Component', version = '1', isPrivate = True)

        project = client.getProject(projectId)

        self.assertEquals(project.getMembers(), [])
        self.assertEquals(project.hidden, 1)

        adminClient, adminId = self.quickMintAdmin('testuser', 'testpass')
        adminProject = adminClient.getProject(projectId)
        hidden = 1
        self.assertEquals(adminClient.getProjectsList(),
                [(projectId, hidden, 'foo - foo')])

        # ensure that site admins can add themselves to the project
        adminProject.addMemberById(adminId, userlevels.OWNER)
        projectList = adminClient.getProjectsByMember(adminId)
        self.assertEquals(len(projectList), 1)
        self.assertEquals(projectList[0][0].name, 'foo')

        # TODO: Add additional tests to exercise the label selecting, and
        # optional groupnames, label, etc.

    def testSetupRmake(self):
        from mint import rmake_setup
        fd, rmakeCfgPath = tempfile.mkstemp()
        self.commands = []

        def newSystem(command):
            self.commands.append(command)

        self.mock(os, 'system', newSystem)
        projectDomainName = self.mintCfg.projectDomainName
        try:
            os.close(fd)
            self.mintCfg.projectDomainName = projectDomainName.split(':')[0]
            rmake_setup.setupRmake(self.mintCfg, rmakeCfgPath,
                    restartRmake=True)
            data = open(rmakeCfgPath).read()
        finally:
            self.mintCfg.projectDomainName = projectDomainName
            util.rmtree(rmakeCfgPath, ignore_errors = True)

        self.assertEquals(set(x.split()[0] for x in data.splitlines()),
            set(['#', 'reposUser', 'reposName', 'reposUrl', 'rBuilderUrl']))

        self.assertEquals(self.commands,
                ['sudo /sbin/service rmake restart',
                'sudo /sbin/service rmake-node restart'])

        client, userId = self.quickMintAdmin('testuser', 'testpass')
        project = client.getProjectByHostname('rmake-repository')
        self.assertEquals(client.getProjectsList(),
                [(project.id, 1, 'rmake-repository - rMake Repository')])

        self.assertRaises(RmakeRepositoryExistsError,
                rmake_setup.setupRmake, self.mintCfg, rmakeCfgPath)


if __name__ == "__main__":
    testsuite.main()
