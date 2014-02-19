#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#


import fixtures

from mint_rephelp import MINT_PROJECT_DOMAIN

from mint import userlevels
from mint.mint_error import *
from mint.lib import maillib

from conary import versions
from conary.conaryclient import ConaryClient
from conary.repository.netclient import UserNotFound
from conary import dbstore
from testrunner import testhelp
from testutils import mock

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

    @testhelp.context("quick")
    @fixtures.fixture('Empty')
    def testBasicAttributes(self, db, data):
        client, userId = self.getClient('test'), data['test']
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

        client = self.getClient('test', 'passtest')

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
            oldChecks = maillib.sendMailWithChecks
            maillib.sendMailWithChecks = lambda *args, **kwargs: True

            client.server.validateNewEmail(userId, eMail)
        finally:
            maillib.sendMailWithChecks = oldChecks
        try:
            maillib.validateEmailDomain(eMail)
            self.fail('Did not catch bad e-mail domain')
        except MailError:
            pass

    @fixtures.fixture('Empty')
    def testConfirmedTwice(self, db, data):
        '''Confirm an account twice'''
        mock.mock(maillib, 'sendMailWithChecks')
        self.cfg.sendNotificationEmails = True

        client = self.getAnonymousClient()
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

        client = self.getAnonymousClient()
        self.assertRaises(PermissionDenied, client.registerNewUser, *regInfo)

        client = self.getAdminClient()
        client.registerNewUser(*regInfo)

        self.assertRaises(ItemNotFound,
            client.server._server.getConfirmation, 'testuser')

    @fixtures.fixture('Empty')
    def testAccountConfirmation(self, db, data):
        '''Ensure that accounts can be activated after registration'''
        mock.mock(maillib, 'sendMailWithChecks')
        self.cfg.sendNotificationEmails = True

        client = self.getAnonymousClient()
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

        owner = self.getClient('owner')
        user = self.getClient('nobody')

        projectId = data['projectId']
        project = user.getProject(projectId)

        # add by user name
        userId = data['nobody']
        project.addMemberByName('nobody', userlevels.USER)
        self.failUnlessEqual(project.getUserLevel(userId), userlevels.USER)
        project.delMemberById(userId)

        # add by user id
        project.addMemberById(userId, userlevels.USER)
        self.failUnlessEqual(project.getUserLevel(userId), userlevels.USER)
        project.delMemberById(userId)

    @fixtures.fixture('Full')
    def testOrphanProjects(self, db, data):
        '''Try to quit projects in various ways'''

        owner, ownerId = self.getClient('owner'), data['owner']
        user, userId = self.getClient('user'), data['user']
        develId = data['developer']

        projectId = data['projectId']
        ownerProject = owner.getProject(projectId)
        userProject = user.getProject(projectId)

        # The fixture already made developer a member of the project, but
        # we need him not to be.
        ownerProject.delMemberById(develId)

        self.failUnlessRaises(LastOwner, ownerProject.updateUserLevel,
            ownerId, userlevels.USER)

        for i in range(2):
            # Make sure owner is the only owner, but can still quit
            self.failIf(ownerProject.lastOwner(ownerId))
            self.failUnless(ownerProject.onlyOwner(ownerId))

            # Try to demote owner to a developer
            try:
                ownerProject.updateUserLevel(ownerId, userlevels.DEVELOPER)
                self.fail("Project allowed demotion of single owner")
            except LastOwner:
                pass

            # Add developer as a developer
            try:
                ownerProject.addMemberById(develId, userlevels.DEVELOPER)
            except DuplicateItem:
                pass

            ## Now that there is a developer ...

            # Make sure owner is still the only owner
            self.failUnless(ownerProject.lastOwner(ownerId))
            self.failIf(ownerProject.lastOwner(develId))
            self.failIf(ownerProject.lastOwner(0))

            # Try to remove owner from the project
            try:
                ownerProject.delMemberById(ownerId)
                self.fail("Project allowed deletion of single owner in a "
                    "project with developers")
            except LastOwner:
                pass

            # Try to demote owner to a developer
            try:
                ownerProject.updateUserLevel(ownerId, userlevels.DEVELOPER)
                self.fail("Project allowed demotion of single owner")
            except LastOwner:
                pass

            # Try to cancel account with an unorphanable project
            user = owner.getUser(ownerId)
            try:
                user.cancelUserAccount()
                self.fail("Project allowed owner to cancel account while orphaning a project with developers")
            except LastOwner:
                pass

            # Stop watching the project (second pass)
            try:
                userProject.delMemberById(userId)
            except UserNotFound:
                pass

            # Add back the user
            userProject.addMemberById(userId, userlevels.USER)

            ownerProject.delMemberById(develId)

        userProject.delMemberById(userId)

    # one could argue that this test could go here or in searchtest. we put it
    # here so we can use the _getConfirmation shortcut...
    @fixtures.fixture('Full')
    def testSearchUnconfUsers(self, db, data):
        raise testhelp.SkipTestException("relocate me")
        client, userId = self.quickMintUser("testuser", "testpass")

        newUserId = client.registerNewUser("newuser", "memberpass", "Test Member",
                                        "test@example.com", "test at example.com", "", active=False)

        if client.getUserSearchResults('newuser') != ([], 0):
            self.fail("Allowed to search for an unconfirmed user")

        conf = self._getConfirmation(newUserId)

        client.confirmUser(conf)

        if client.getUserSearchResults('newuser') == ([], 0):
            self.fail("Failed a search for a newly confirmed user")

    @fixtures.fixture('Empty')
    def testIllegalCancel(self, db, data):
        '''Try to cancel another user's account'''

        client, userId = self.getClient('test'), data['test']
        client2, userId2 = self.getClient('admin'), data['admin']
        self.failUnlessRaises(PermissionDenied,
            client.server.cancelUserAccount, userId2)
        self.failUnlessRaises(PermissionDenied,
            client.server.removeUserAccount, userId2)

    @fixtures.fixture('Full')
    def testChangePassword(self, db, data):
        '''Check repository access after changing a user's password'''

        raise testhelp.SkipTestException("Can't be ported without "
            "repository fixture")

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

    @fixtures.fixture('Empty')
    def testPasswordPermissions(self, db, data):
        '''Try to change a user's password as various roles'''

        client, userId = self.getClient('test'), data['test']
        admin, adminId = self.getClient('admin'), data['admin']

        # user changes own password
        user = client.getUser(userId)
        user.setPassword('newpass')
        client = self.getClient('user', 'newpass')

        # user attempts to change other user's password--should fail
        user = client.getUser(adminId)
        self.assertRaises(PermissionDenied, user.setPassword, 'newpass')

        # admin changes user's password
        user = admin.getUser(userId)
        user.setPassword('testpass')

    @fixtures.fixture('Empty')
    def testLastAdmin(self, db, data):
        '''Ensure that the last admin cannot demote themselves'''

        client1, userId1 = self.getClient('admin'), data['admin']
        client2, userId2 = self.getClient('test'), data['test']

        self.assertRaises(LastAdmin, client1.removeUserAccount, userId1)

        client1.promoteUserToAdmin(userId2)
        client1.removeUserAccount(userId1)

    @fixtures.fixture('Empty')
    def testLastAdmin2(self, db, data):
        '''Ensure that the last admin can delete the last non-admin user'''
        admin = self.getClient('admin')
        userId = data['test']
        admin.removeUserAccount(userId)

    @fixtures.fixture('Empty')
    def testAdminNewUser(self, db, data):
        '''Check creation of accounts by admin and restricted creation'''
        anonClient = self.getAnonymousClient()
        adminClient = self.getClient('admin')

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

    @fixtures.fixture('Full')
    def testExternalModify(self, db, data):
        raise testhelp.SkipTestException("Can't be ported without "
            "repository fixture")
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
        cu.execute('UPDATE Projects set external = true')
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


