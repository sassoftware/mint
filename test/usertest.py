#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

import fixtures
from mint import mint_error, users
from mint.database import ItemNotFound

class UsersTest(fixtures.FixturedUnitTest):
    @fixtures.fixture("Full")
    def testDefaultNewsletter(self, db, data):
        # representative of an attention required setting
        client = self.getClient('user')
        user = client.getUser(data['user'])
        self.failIf(user.getDataValue('newsletter') != False,
                    "default newsletter value incorrect")

    @fixtures.fixture("Full")
    def testDefaultInsider(self, db, data):
        # representative of an attention required setting
        client = self.getClient('user')
        user = client.getUser(data['user'])
        self.failIf(user.getDataValue('insider') != False,
                    "default insider value incorrect")

    @fixtures.fixture("Full")
    def testDefaultSearchResults(self, db, data):
        # representative of a non-attention required setting
        client = self.getClient('user')
        user = client.getUser(data['user'])
        self.failIf(user.getDataValue('searchResultsPerPage') != 10,
                    "default searchResultsPerPage value incorrect")

    @fixtures.fixture("Full")
    def testSetNewsletter(self, db, data):
        client = self.getClient('user')
        user = client.getUser(data['user'])
        user.setDataValue('newsletter', True)

        cu = db.cursor()
        cu.execute("""SELECT value
                          FROM UserData
                          WHERE userId=? AND name='newsletter'""", user.id)
        self.failIf(cu.fetchone()[0] != '1',
                    'Failed to set newsletter to True')

        user.setDataValue('newsletter', False)
        cu.execute("""SELECT value
                          FROM UserData
                          WHERE userId=? AND name='newsletter'""", user.id)
        self.failIf(cu.fetchone()[0] != '0',
                    'Failed to set newsletter to False')

    @fixtures.fixture("Full")
    def testSetInsider(self, db, data):
        client = self.getClient('user')
        user = client.getUser(data['user'])
        user.setDataValue('insider', True)

        cu = db.cursor()
        cu.execute("""SELECT value
                          FROM UserData
                          WHERE userId=? AND name='insider'""", user.id)
        self.failIf(cu.fetchone()[0] != '1',
                    'Failed to set insider to True')

        user.setDataValue('insider', False)
        cu.execute("""SELECT value
                          FROM UserData
                          WHERE userId=? AND name='insider'""", user.id)
        self.failIf(cu.fetchone()[0] != '0',
                    'Failed to set insider to False')

    @fixtures.fixture("Full")
    def testSetSearchResults(self, db, data):
        client = self.getClient('user')
        user = client.getUser(data['user'])
        user.setDataValue('searchResultsPerPage', 5)

        cu = db.cursor()
        cu.execute("""SELECT value
                          FROM UserData
                          WHERE userId=? AND name='searchResultsPerPage'""",
                   user.id)
        self.failIf(cu.fetchone()[0] != '5',
                    'Failed to set searchResultsPerPage to 5')

        user.setDataValue('searchResultsPerPage', 10)
        cu.execute("""SELECT value
                          FROM UserData
                          WHERE userId=? AND name='searchResultsPerPage'""",
                   user.id)
        self.failIf(cu.fetchone()[0] != '10',
                    'Failed to set searchResultsPerPage to 10')

    @fixtures.fixture("Full")
    def testGetNewsletter(self, db, data):
        client = self.getClient('user')
        user = client.getUser(data['user'])
        for val in (False, True):
            user.setDataValue('newsletter', val)
            self.failIf(user.getDataValue('newsletter') != val,
                        "retrieving data value for newsletter failed for %r" \
                        % val)

    @fixtures.fixture("Full")
    def testGetInsider(self, db, data):
        client = self.getClient('user')
        user = client.getUser(data['user'])
        for val in (False, True):
            user.setDataValue('insider', val)
            self.failIf(user.getDataValue('insider') != val,
                        "retrieving data value for insider failed for %r" % \
                        val)

    @fixtures.fixture("Full")
    def testGetSearchResults(self, db, data):
        client = self.getClient('user')
        user = client.getUser(data['user'])
        for val in (5, 10):
            user.setDataValue('searchResultsPerPage', val)
            self.failIf(user.getDataValue('searchResultsPerPage') != val,
                        "retrieving data value for searchResultsPerPage " \
                        "failed for %r" % val)

    @fixtures.fixture("Full")
    def testDefaultedData(self, db, data):
        client = self.getClient('user')
        user = client.getUser(data['user'])

        template = user.getDataTemplate()
        for key in user.getDefaultedData():
            user.setDataValue(key, template[key][1])
            self.failIf(key in user.getDefaultedData(),
                        "%s was not removed from defaulted data when set"% key)

    @fixtures.fixture("Full")
    def testMissingSearchResults(self, db, data):
        client = self.getClient('user')
        user = client.getUser(data['user'])

        assert('searchResultsPerPage' not in user.getDefaultedData())
        user.setDataValue('searchResultsPerPage', 10)
        assert('searchResultsPerPage' not in user.getDefaultedData())

    @fixtures.fixture("Full")
    def testSetIllegalOption(self, db, data):
        client = self.getClient('user')
        user = client.getUser(data['user'])

        self.assertRaises(mint_error.ParameterError, user.setDataValue,
                          'notOnTheList', 0)

    @fixtures.fixture('Empty')
    def testUserDataCancelAcct(self, db, data):
        # this might more appropriately be under accounttest but that is not
        # yet fixtured.
        client = self.getClient('test')
        user = client.getUser(data['test'])

        user.setDataValue('newsletter', True)

        cu = db.cursor()
        cu.execute('SELECT * FROM UserData WHERE userId=?', user.id)

        self.failIf(not cu.fetchall(), "No user data")

        user.cancelUserAccount()
        cu.execute('SELECT * FROM UserData WHERE userId=?', user.id)
        self.failIf(cu.fetchall(), "User data not deleted when acct canceled.")

    @fixtures.fixture('Full')
    def testCancelUserAccount(self, db, data):
        # XXX: This test fails under sqlite.
        client = self.getClient('user')
        user = client.getUser(data['user'])

        self.assertRaises(users.LastOwner, user.cancelUserAccount)

    @fixtures.fixture('Full')
    def testUserDataDict(self, db, data):
        client = self.getClient('user')
        user = client.getUser(data['user'])

        baseDict = user.getDataDict()
        self.failIf(not isinstance(baseDict, dict))
        user.setDataValue('newsletter', True)
        newDict = user.getDataDict()
        assert(baseDict != newDict)
        assert(newDict['newsletter'] == True)

    @ fixtures.fixture('Full')
    def testGetUserPublic(self, db, data):
        client = self.getClient('user')
        user = client.getUser(data['user'])

        userPub = client.server._server.getUserPublic(user.id)

        assert(userPub['salt'] == '')
        assert(userPub['passwd'] == '')
        del userPub['salt']
        del userPub['passwd']
        for key, val in userPub.iteritems():
            assert val == user.__getattribute__(key)

    @fixtures.fixture('Full')
    def testMissingMintAuth(self, db, data):
        client = self.getClient('admin')
        assert client.server._server._isUserAdmin(data['admin'])
        cu = db.cursor()
        cu.execute("DELETE FROM UserGroups WHERE userGroup='MintAdmin'")
        db.commit()
        assert not client.server._server._isUserAdmin(data['admin'])

    @ fixtures.fixture('Full')
    def donttestProductionConfirmation(self, db, data):
        client = self.getClient('admin')
        debugMode = self.cfg.debugMode
        try:
            self.cfg.debugMode = False
            self.assertRaises(mint_error.PermissionDenied,
                              client.server._server.getConfirmation, 'admin')
        finally:
            self.cfg.debugMode = debugMode

    @fixtures.fixture('Full')
    def testNoConfirmation(self, db, data):
        client = self.getClient('admin')
        debugMode = self.cfg.debugMode
        try:
            self.cfg.debugMode = True
            self.assertRaises(ItemNotFound,
                              client.server._server.getConfirmation,
                              'Sir not appearing in this film')
        finally:
            self.cfg.debugMode = debugMode

    @fixtures.fixture('Full')
    def testDataPermission(self, db, data):
        client = self.getClient('nobody')
        user = client.getUser(data['owner'])
        self.assertRaises(mint_error.PermissionDenied,
                          user.setDataValue, 'foo', 'bar')
        self.assertRaises(mint_error.PermissionDenied,
                          user.getDataValue, 'foo')
        self.assertRaises(mint_error.PermissionDenied,
                          user.getDefaultedData)
        self.assertRaises(mint_error.PermissionDenied,
                          user.getDataDict)

    @fixtures.fixture('Full')
    def testAdminUserSearch(self, db, data):
        client = self.getClient('admin')
        sRes = client.getUserSearchResults('%%%')
        client.registerNewUser('unconfirmed', '123456', 'shadow',
                               'nothing@localhost', '', '', False)
        assert(client.getUserSearchResults('%%%') != sRes)
        client = self.getClient('owner')
        assert(client.getUserSearchResults('%%%') == sRes)


if __name__ == "__main__":
    testsuite.main()
