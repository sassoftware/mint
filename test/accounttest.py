#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rpath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint import userlevels
from mint.mint_error import PermissionDenied
from mint.users import LastOwner

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

    def testOrphanProjects(self):
        # owner tries to quit in various ways

        client = self.openMintClient()
        ownerClient, ownerId = self.quickMintUser("ownerAcct","foo")
        develClient, develId = self.quickMintUser("develAcct","foo")

        projectId = ownerClient.newProject("Foo", "foo", "rpath.org")
        project = ownerClient.getProject(projectId)

        assert(not project.lastOwner(ownerId))
        assert(project.onlyOwner(ownerId))

        try:
            project.updateUserLevel(ownerId, userlevels.DEVELOPER)
            self.fail("Project allowed demotion of single owner")
        except LastOwner:
            pass

        project.addMemberById(develId, userlevels.DEVELOPER)

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

if __name__ == "__main__":
    testsuite.main()
