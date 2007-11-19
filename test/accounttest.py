#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import testsuite
testsuite.setup()

import fixtures

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN

from mint import userlevels
from mint.database import DuplicateItem, ItemNotFound
from mint.mint_error import PermissionDenied, UserAlreadyAdmin, \
     AdminSelfDemotion, LastAdmin
from mint.users import LastOwner, UserInduction, MailError, GroupAlreadyExists, AlreadyConfirmed
from mint import users

from conary import versions
from conary.conaryclient import ConaryClient
from conary.repository.netclient import UserNotFound
from conary import dbstore

class AccountTest(fixtures.FixturedUnitTest):

    # this function MUST be shortcutted since we should not make an xmlrpc
    # call for it
    def _getConfirmation(self, userId):
        cu = self.db.cursor()
        cu.execute("SELECT confirmation FROM Confirmations WHERE userId=?", userId)
        try:
            return cu.fetchone()[0]
        except TypeError:
            return None

    @testsuite.context("quick")
    @fixtures.fixture('Full')
    def testBasicAttributes(self, db, data):
        client, userId = self.getFixtureUser(data, 'user')
        user = client.getUser(userId)

        eMail = "not_for_real@broken.domain"
        displayEmail = "some@invalid.email"
        fullName = "Test A. User"
        blurb = 'An all-singing all-dancing \xe2\x99\xaa blurb \xe2\x99\xac for a user.'

        user.setDisplayEmail(displayEmail)
        user.setFullName(fullName)
        user.setBlurb(blurb)
        # FIXME: move validation logic to server side. this should not pass
        # in the future
        user.setEmail(eMail)
        user.setPassword("passtest")

        self.failUnlessRaises(PermissionDenied,
            client.updateAccessedTime, userId)

        client = self.getClient('user', 'passtest')

        # refresh the user
        user = client.getUser(userId)

        if user.getDisplayEmail() != displayEmail:
            self.fail("User's display email lost in translation")

        if user.getFullName() != fullName:
            self.fail("User's full name lost in translation")

        if user.getBlurb() != blurb:
            self.fail("User's Blurb lost in translation")

        if user.getEmail() != eMail:
            self.fail("User's email lost in translation")

        client.updateAccessedTime(userId)
        try:
            oldChecks = users.sendMailWithChecks
            users.sendMailWithChecks = lambda *args, **kwargs: True

            client.server.validateNewEmail(userId, eMail)
        finally:
            users.sendMailWithChecks = oldChecks
        try:
            users.validateEmailDomain(eMail)
            self.fail('Did not catch bad e-mail domain')
        except MailError:
            pass

    @fixtures.fixture('Full')
    def testProjectInteraction(self, db, data):
        # FIXME: needs annotation, and a good bludgeoning with the cluebat
        raise testsuite.SkipTestException, 'nonsensical test'

        client, userId = self.getFixtureUser(data, 'owner')
        user = client.getUser(userId)

        projectId = data['projectId']
        project = client.getProject(projectId)

        project.addMemberById(userId, userlevels.OWNER)

        user.setPassword("passtest")

        client = self.getClient('owner', 'passtest')
        user = client.getUser(userId)
        user.cancelUserAccount()

    @fixtures.fixture('Empty')
    def testConfirmedTwice(self, db, data):
        '''Confirm an account twice'''
        client = self.getAnonymous()
        client.registerNewUser('testuser', 'testpass', 'test user',
            'test@example.com', 'test at example dot com', 'LFO', False)
        conf = client.server._server.getConfirmation('testuser')
        client.confirmUser(conf)
        self.assertRaises(AlreadyConfirmed, client.confirmUser, conf)

    @fixtures.fixture('Empty')
    def testImmediatelyActive(self, db, data):
        '''Register a new user from an admin account'''

        regInfo = ('testuser', 'testpass', 'test user', 'test@example.com',
            'test at example dot com', 'LFO', True)

        client = self.getAnonymous()
        self.assertRaises(PermissionDenied, client.registerNewUser, *regInfo)

        client = self.getAdminClient()
        client.registerNewUser(*regInfo)

        self.assertRaises(ItemNotFound,
            client.server._server.getConfirmation, 'testuser')

    @fixtures.fixture('Empty')
    def testAccountConfirmation(self, db, data):
        '''Ensure that accounts can be activated after registration'''

        client = self.getAnonymous()
        userId = client.registerNewUser('newuser', 'newuserpass',
            'Test Member', 'test@example.com', 'test at example dot com',
            '', active=False)

        # These helpers lack XMLRPC calls
        def isActive():
            cu = db.cursor()
            cu.execute('SELECT active FROM Users WHERE userId=?', userId)
            return cu.fetchone()[0]
        def getConfirmation():
            cu = db.cursor()
            cu.execute('SELECT confirmation FROM Confirmations '
                'WHERE userId=?', userId)
            try:
                return cu.fetchone()[0]
            except TypeError:
                return None

        # Make sure the account isn't active yet
        self.failIf(isActive(), 'User should not have been active yet')

        # Confirm the account
        conf = getConfirmation()
        client.confirmUser(conf)
        self.failUnlessEqual(getConfirmation(), None,
            'User confirmation should have been deleted')
        self.failUnless(isActive(), 'User was not activated')

        # Make it stagnant
        # there's no xmlrpc call for this due to the fact that it's generally
        # something the server decides arbitrarily to do to an acct...
        client.server._server.users.invalidateUser(userId)
        self.failUnless(isActive(), 'User should have been active')

        # Confirm the account again
        conf = getConfirmation()
        client.confirmUser(conf)
        self.failUnlessEqual(getConfirmation(), None,
            'User confirmation should have been deleted')
        self.failUnless(isActive(), 'User should have been active')

    @fixtures.fixture('Full')
    def testWatchProjects(self, db, data):
        '''Test watching projects in various ways'''

        ownerClient, ownerId = self.getFixtureUser(data, 'owner')
        userClient, userId = self.getFixtureUser(data, 'user')

        projectId = data['projectId']
        project = userClient.getProject(projectId)

        # add by user name
        project.addMemberByName('user', userlevels.USER)
        self.failUnlessEqual(project.getUserLevel(userId), userlevels.USER)
        project.delMemberById(userId)

        # add by user id
        project.addMemberById(userId, userlevels.USER)
        self.failUnlessEqual(project.getUserLevel(userId), userlevels.USER)
        project.delMemberById(userId)

    @fixtures.fixture('Full')
    def testOrphanProjects(self, db, data):
        '''Try to quit projects in various ways'''

        ownerClient, ownerId = self.getFixtureUser(data, 'owner')
        develClient, develId = self.getFixtureUser(data, 'developer')
        readerClient, readerId = self.getFixtureUser(data, 'user')

        projectId = data['projectId']
        project = ownerClient.getProject(projectId)
        readerProject = readerClient.getProject(projectId)

        self.failUnlessRaises(project.updateUserLevel(ownerId,
            userlevels.USER), LastOwner)

        for i in range(2):
            self.failUnless(project.lastOwner(ownerId))
            assert(project.onlyOwner(ownerId))

            try:
                project.updateUserLevel(ownerId, userlevels.DEVELOPER)
                self.fail("Project allowed demotion of single owner")
            except LastOwner:
                pass

            try:
                project.addMemberById(develId, userlevels.DEVELOPER)
            except DuplicateItem:
                pass

            try:
                project.updateUserLevel(develId, userlevels.USER)
                self.fail("Project allowed demotion from developer to user")
            except UserInduction:
                pass

            assert(project.lastOwner(ownerId))
            assert(not project.lastOwner(develId))
            assert(not project.lastOwner(0))

            try:
                project.delMemberById(ownerId)
                self.fail("Project allowed deletion of single owner in a project with developers")
            except LastOwner:
                pass

            try:
                project.updateUserLevel(ownerId, userlevels.DEVELOPER)
                self.fail("Project allowed demotion of single owner")
            except LastOwner:
                pass

            user = ownerClient.getUser(ownerId)
            try:
                user.cancelUserAccount()
                self.fail("Project allowed owner to cancel account while orphaning a project with developers")
            except LastOwner:
                pass

            try:
                readerProject.delMemberById(readerId)
            except UserNotFound:
                pass

            try:
                project.addMemberById(readerId, userlevels.USER)
                self.fail('Owner inducted a user')
            except UserInduction:
                pass

            readerProject.addMemberById(readerId, userlevels.USER)
            try:
                project.delMemberById(readerId)
                self.fail('owner ejected a reader')
            except UserInduction:
                pass

            project.delMemberById(develId)

        readerProject.delMemberById(readerId)

    # one could argue that this test could go here or in searchtest. we put it
    # here so we can use the _getConfirmation shortcut...
    # FIXME: move me back
    def testSearchUnconfUsers(self):
        client, userId = self.quickMintUser("testuser", "testpass")

        newUserId = client.registerNewUser("newuser", "memberpass", "Test Member",
                                        "test@example.com", "test at example.com", "", active=False)

        if client.getUserSearchResults('newuser') != ([], 0):
            self.fail("Allowed to search for an unconfirmed user")

        conf = self._getConfirmation(newUserId)

        client.confirmUser(conf)

        if client.getUserSearchResults('newuser') == ([], 0):
            self.fail("Failed a search for a newly confirmed user")

    @fixtures.fixture('Full')
    def testIllegalCancel(self, db, data):
        client, userId = self.getFixtureUser(data, 'owner')
        client2, userId2 = self.getFixtureUser(data, 'user')
        self.failUnlessRaises(PermissionDenied,
            client.server.cancelUserAccount, userId2)
        self.failUnlessRaises(PermissionDenied,
            client.server.removeUserAccount, userId2)

    @fixtures.fixture('Full')
    def testUserList(self, db, data):
        user = self.getClient('user')
        admin = self.getAdminClient()

        self.failUnlessEqual(admin.getUsers(0, 10, 0)[1], 5,
            'Admin account could not see all users via getUsers')
        self.failUnlessEqual(len(admin.getUsersList()), 5,
            'Admin account could not see all users via getUsersList')
        self.failUnlessRaises(PermissionDenied, user.getUsers, 0, 10, 0)
        self.failUnlessEqual(user.server.searchUsers('user', 10, 0)[1], 5,
            'User-level user search returned incorrect results.')

    def testChangePassword(self):
        client, userId = self.quickMintAdmin("testuser", "testpass")
        intProjectId = self.newProject(client, "Internal Project", "internal",
                MINT_PROJECT_DOMAIN)
        extProjectId = client.newExternalProject("External Project",
                "external", MINT_PROJECT_DOMAIN, "localhost@rpl:devel",
                'http://localhost:%d/conary/' % self.servers.getServer(0).port, False)

        user = client.getUser(userId)
        user.setPassword("newpass")

        client = self.openMintClient(('testuser', 'newpass'))

        internal = client.getProject(intProjectId)
        external = client.getProject(extProjectId)

        intLabel = versions.Label('internal.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel')
        extLabel = versions.Label('localhost@rpl:devel')

        # accessed using new password
        cfg = internal.getConaryConfig()
        assert(ConaryClient(cfg).getRepos().troveNames(intLabel) == [])

        # external repository will be accessed anonymously
        cfg = external.getConaryConfig()
        assert(ConaryClient(cfg).getRepos().troveNames(extLabel) == [])

    def testPasswordPermissions(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        adminClient, adminId = self.quickMintAdmin("adminuser", "adminpass")

        # user changes own password
        user = client.getUser(userId)
        user.setPassword('newpass')
        client = self.openMintClient(('testuser', 'newpass'))

        # user attempts to change other user's password--should fail
        user = client.getUser(adminId)
        self.assertRaises(PermissionDenied, user.setPassword, 'newpass')

        # admin changes user's password
        user = adminClient.getUser(userId)
        user.setPassword('testpass')

        # verify auth user works
        client = self.openMintClient((self.mintCfg.authUser,
                                      self.mintCfg.authPass))
        user.setPassword('foobar')

    def testHangingGroupMembership(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        client.removeUserAccount(userId)

        cu = self.db.cursor()
        cu.execute("SELECT * FROM UserGroupMembers WHERE userId=?", userId)

        self.failIf(cu.fetchall(),
                    "Leftover UserGroupMembers after account was canceled")

    def testHangingGroups(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        client.removeUserAccount(userId)

        cu = self.db.cursor()
        cu.execute("SELECT * FROM UserGroups WHERE userGroup=?", 'testuser')

        self.failIf(cu.fetchall(),
                    "Leftover UserGroup after account was canceled")

    def testPromoteUserToAdmin(self):
        adminClient, adminId = self.quickMintAdmin("adminuser", "testpass")
        client, userId  = self.quickMintUser("testuser", "testpass")

        # promote test user
        adminClient.promoteUserToAdmin(userId)

        mintAdminId = client.server._server.userGroups.getMintAdminId()
        cu = self.db.cursor()
        cu.execute("SELECT COUNT(*) FROM UserGroupMembers WHERE userGroupId=? AND userId=?", mintAdminId, userId)
        (count, ) = cu.fetchone()
        self.failUnlessEqual(count, 1)

        # make sure we don't allow a user to be promoted twice
        self.failUnlessRaises(UserAlreadyAdmin,
                adminClient.promoteUserToAdmin,
                userId)

        # make sure joeblow (a non admin) cannot promote billybob
        client2, userId2  = self.quickMintUser("joeblow", "testpass")
        client3, userId3  = self.quickMintUser("billybob", "testpass")

        self.failUnlessRaises(PermissionDenied,
                client2.promoteUserToAdmin,
                userId3)

    def testDemoteUserFromAdmin(self):
        adminClient, adminId = self.quickMintAdmin("adminuser", "testpass")
        otherClient, otherUserId  = self.quickMintAdmin("testuser", "testpass")

        adminClient.demoteUserFromAdmin(otherUserId)

        # verify other user was demoted
        mintAdminId = adminClient.server._server.userGroups.getMintAdminId()
        cu = self.db.cursor()

        cu.execute("SELECT COUNT(*) FROM UserGroupMembers WHERE userGroupId=? AND userId=?", mintAdminId, otherUserId)

        self.failIf(cu.fetchone()[0], "Admin user was not demoted")

        # ensure nothing bad happens if we click twice
        adminClient.demoteUserFromAdmin(otherUserId)

        # ensure we can't demote the last admin
        self.assertRaises(AdminSelfDemotion, adminClient.demoteUserFromAdmin,
                          adminId)

    def testAutoGenerateMintAdminId(self):
        client, userId  = self.quickMintUser("testuser", "testpass")

        # test auto adding the group here
        mintAdminId = client.server._server.userGroups.getMintAdminId()

        # this should return the same value twice
        mintAdminId2 = client.server._server.userGroups.getMintAdminId()
        self.failUnlessEqual(mintAdminId, mintAdminId2)

    def testLastAdmin(self):
        client, userId = self.quickMintAdmin('foouser', 'foopass')
        # this should fail
        self.assertRaises(LastAdmin, client.removeUserAccount, userId)
        client, userId = self.quickMintAdmin('foouser1', 'foopass1')
        # this should succeed
        client.removeUserAccount(userId);

    def testLastAdmin2(self):
        client, userId = self.quickMintAdmin('foouser', 'foopass')
        client2, userId2 = self.quickMintUser('foouser1', 'foopass1')
        # this should succeed
        client.removeUserAccount(userId2);

    def testAdminNewUser(self):
        anonClient = self.openMintClient(("anonymous", "anonymous"))
        adminClient, adminId = self.quickMintAdmin("adminuser", "testpass")

        anonClient.registerNewUser("Foo", "Bar", "Foo Bar",
			                       "foo@localhost", "fooATlocalhost",
			                       "blah, blah", False)

        adminClient.registerNewUser("Foo2", "Bar2", "Foo Bar",
			                        "foo@localhost", "fooATlocalhost",
			                        "blah, blah", True)

        anonClient._cfg.adminNewUsers = True
        try:
            anonClient.registerNewUser("Foo3", "Bar3", "Foo Bar",
		    	                       "foo@localhost", "fooATlocalhost",
    			                       "blah, blah", False)
        except PermissionDenied:
            pass
        else:
            fail('New account created without admin approval')

        adminClient.registerNewUser("Foo3", "Bar3", "Foo Bar",
			                        "foo@localhost", "fooATlocalhost",
			                        "blah, blah", True)
        adminClient._cfg.adminNewUsers = False

    def testExternalModify(self):
        client, userId = self.quickMintAdmin('foouser', 'foopass')
        client2, userId2 = self.quickMintUser('foouser1', 'foopass1')

        projectId = self.newProject(client)
        project = client2.getProject(projectId)
        project.addMemberById(userId2, userlevels.USER)

        # record current acl's
        dbConn = client.server._server.projects.reposDB.getRepositoryDB( \
            project.getFQDN())
        db = dbstore.connect(dbConn[1], dbConn[0])
        rCu = db.cursor()
        rCu.execute('SELECT * FROM Permissions')
        acls = rCu.fetchall()

        # now make the project external
        cu = self.db.cursor()
        cu.execute('UPDATE Projects set external = 1')
        self.db.commit()

        # now switch to admin context and add the watcher
        project = client.getProject(projectId)
        project.addMemberById(userId2, userlevels.DEVELOPER)

        # now test that "external" project was not modified by this action

        rCu.execute('SELECT * FROM Permissions')
        self.failIf(acls != rCu.fetchall(),
                    "addMember attempted to change external project acl's")

        # now make the project external
        cu = self.db.cursor()
        cu.execute('UPDATE Projects set external = 0')
        self.db.commit()

        project.addMemberById(userId2, userlevels.DEVELOPER)

        # XXX: not sure why i have to reopen the database here for mysql
        db = dbstore.connect(dbConn[1], dbConn[0])
        rCu = db.cursor()
        rCu.execute('SELECT * FROM Permissions')
        self.failIf(acls == rCu.fetchall(),
                    "addMember didn't change internal project acl's")


if __name__ == "__main__":
    testsuite.main()
