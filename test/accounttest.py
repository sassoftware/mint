#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint import userlevels
from mint.mint_error import PermissionDenied
from mint.users import LastOwner, UserInduction
from mint.database import DuplicateItem
from repository.netclient import UserNotFound

class AccountTest(MintRepositoryHelper):

    # this function MUST be shortcutted since we should not make an xmlrpc
    # call for it
    def _getConfirmation(self, userId):
        cu = self.db.cursor()
        r = cu.execute("SELECT confirmation FROM Confirmations WHERE userId=?", userId)
        try:
            return r.fetchone()[0]
        except TypeError:
            return None

    # this function is shortcutted simply because there isn't a need for an
    # xmlrpc call. if there ever is in the future, consider dropping this func.
    def _userActive(self, userId):
        cu = self.db.cursor()
        r = cu.execute("SELECT active FROM Users WHERE userId=?", userId)
        return r.fetchone()[0]

    def testAccountConfirmation(self):
        client = self.openMintClient()
        # ignore the userId and make a new one that's not registered...
        userId = client.registerNewUser("newuser", "memberpass", "Test Member",
                                        "test@example.com", "test at example.com", "", active=False)
        # now check that it is indeed not active.
        assert(not self._userActive(userId))
        # retrieve the confirmations entry so we can confirm it.
        conf = self._getConfirmation(userId)
        # confirm it.
        client.confirmUser(conf)
        # check confs entry doesn't exist
        assert (self._getConfirmation(userId) is None)
        # test to see status of active flag
        assert(self._userActive(userId))
        # make it stagnant
        # there's no xmlrpc call for this due to the fact that it's generally
        # something the server decides arbitrarily to do to an acct...
        self.mintServer.users.invalidateUser(userId)
        # test to confirm active flag is still set
        assert(self._userActive(userId))
        # retrieve confirmations entry
        conf = self._getConfirmation(userId)
        # confirm it.
        client.confirmUser(conf)
        # test to confirm active flag is still set
        assert(self._userActive(userId))
        # check confs entry doesn't exist
        assert (self._getConfirmation(userId) is None)

    def testWatchProjects(self):
        # test watching projects in various ways

        client = self.openMintClient()

        ownerClient, ownerId = self.quickMintUser("owner", "foo")
        readerClient, readerId = self.quickMintUser("reader", "foo")

        projectId = ownerClient.newProject("Foo", "foo", "rpath.org")

        project = readerClient.getProject(projectId)

        # add by user name
        project.addMemberByName("reader", userlevels.USER)
        assert(project.getUserLevel(readerId) == userlevels.USER)

        project.delMemberById(readerId)
        
        # add by user id
        project.addMemberById(readerId, userlevels.USER)
        assert(project.getUserLevel(readerId) == userlevels.USER)

    def testOrphanProjects(self):
        # owner tries to quit in various ways

        client = self.openMintClient()
        ownerClient, ownerId = self.quickMintUser("ownerAcct","foo")
        develClient, develId = self.quickMintUser("develAcct","foo")
        readerClient, readerId = self.quickMintUser("readerAcct", "foo")

        projectId = ownerClient.newProject("Foo", "foo", "rpath.org")
        project = ownerClient.getProject(projectId)

        readerProject = readerClient.getProject(projectId)

        try:
            project.updateUserLevel(ownerId, userlevels.USER)
            self.fail('Project allowed changing owner status to user status')
        except LastOwner:
            pass

        for i in range(2):
            assert(not project.lastOwner(ownerId))
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

if __name__ == "__main__":
    testsuite.main()
