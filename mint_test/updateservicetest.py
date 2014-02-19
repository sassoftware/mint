#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#

from testutils import mock

from mint_rephelp import FQDN

from mint.mint_error import UpdateServiceNotFound
from conary.dbstore import sqlerrors
from conary.repository import transport

from mint.lib import database
from mint import helperfuncs
from mint import mint_error
from mint.lib import proxiedtransport
from mint.web.webhandler import HttpMoved

import StringIO

import fixtures
import xmlrpclib

STOCK_MIRROR_PASSWORD = 'thisisamirrorpassword'

class FakeUpdateServiceServerProxy:

    def __init__(self, url, *args, **kwargs):
        self.url = url
        self.mirrorusers = self
        self.MirrorUsers = self

    def addRandomUser(self, name):
        return STOCK_MIRROR_PASSWORD

    Network = mock.MockObject()
    Network.Network.index._mock.setDefaultReturn({'host_hostName':None})
    configure = Network
    rusconf = mock.MockObject()

usedProxy = False
def fake_proxy_request(self, *args, **kw):
    global usedProxy
    usedProxy = True
    return [[None, [STOCK_MIRROR_PASSWORD,]], None] 

def fake_proxy_parse_response(self, *args, **kw):
    global usedProxy
    usedProxy = True
    return STOCK_MIRROR_PASSWORD

class UpdateServiceTest(fixtures.FixturedUnitTest):

    def setUp(self):
        fixtures.FixturedUnitTest.setUp(self)
        self._oldServerProxy = xmlrpclib.ServerProxy
        xmlrpclib.ServerProxy = FakeUpdateServiceServerProxy

    def tearDown(self):
        fixtures.FixturedUnitTest.tearDown(self)
        xmlrpclib.ServerProxy = self._oldServerProxy

    @testsuite.context("quick")
    @fixtures.fixture("Full")
    def testCreateUpdateService(self, db, data):
        adminClient = self.getClient("admin")
        us1 = ['foo.example.com',
                helperfuncs.generateMirrorUserName(FQDN, 'foo.example.com'),
                STOCK_MIRROR_PASSWORD, 'Foo 1']
        us1Id = adminClient.addUpdateService(*us1)

        self.failUnless(us1Id,
                "Expecting an id to be returned from addUpdateService,"
                " got %s" % us1Id)

    @testsuite.context("quick")
    @fixtures.fixture("Full")
    def testCreateUpdateServiceWithProxy(self, db, data):
        raise testsuite.SkipTestException('Skip this test due to mocking problems with transport.Transport on bamboo.')
        xmlrpclib.ServerProxy = self._oldServerProxy
        self.cfg.proxy = {'http' : 'http://proxyuser:proxypass@proxy.foo.com:3128',
                          'https' : 'https://proxyuser:proxypass@proxy.foo.com:3128'}
        oldRequest = transport.Transport.request
        oldParseResponse = transport.Transport.parse_response
        transport.Transport.request = fake_proxy_request
        transport.Transport.parse_response = fake_proxy_parse_response

        adminClient = self.getClient("admin")
        us1 = ['foo.example.com',
                helperfuncs.generateMirrorUserName(FQDN, 'foo.example.com'),
                STOCK_MIRROR_PASSWORD, 'Foo 1']
        us1Id = adminClient.addUpdateService(*us1)

        self.failUnless(us1Id,
                "Expecting an id to be returned from addUpdateService,"
                " got %s" % us1Id)
        global usedProxy
        self.assertTrue(usedProxy)

        self.cfg.proxy = {}
        xmlrpclib.ServerProxy = FakeUpdateServiceServerProxy
        transport.Transport.request = oldRequest
        transport.Transport.parse_response = oldParseResponse
        usedProxy = False

    @testsuite.context("quick")
    @fixtures.fixture("Full")
    def testCreateDuplicateUpdateService(self, db, data):
        adminClient = self.getClient("admin")
        us1 = ['foo.example.com',
                helperfuncs.generateMirrorUserName(FQDN, 'foo.example.com'),
                STOCK_MIRROR_PASSWORD, 'Foo 1']
        us1Id = adminClient.addUpdateService(*us1)

        # This should fail
        self.failUnlessRaises(mint_error.DuplicateItem,
                adminClient.addUpdateService, *us1)

    @fixtures.fixture("Full")
    def testEditUpdateService(self, db, data):
        adminClient = self.getClient("admin")
        us1 = ['foo.example.com',
                helperfuncs.generateMirrorUserName(FQDN, 'foo.example.com'),
                STOCK_MIRROR_PASSWORD, 'Foo 1']

        # add the first version of the updateservice
        us1Id = adminClient.addUpdateService(*us1)

        # attempt to modify the description and check results
        adminClient.editUpdateService(us1Id, 'Baz 1')
        us1Returned2 = adminClient.getUpdateService(us1Id)
        self.failUnlessEqual('Baz 1', us1Returned2['description'],
            "Editing description didn't work")

    @fixtures.fixture("Full")
    def testDeleteUpdateService(self, db, data):
        adminClient = self.getClient("admin")
        us1 = ['foo.example.com',
                helperfuncs.generateMirrorUserName(FQDN, 'foo.example.com'),
                STOCK_MIRROR_PASSWORD, 'Foo 1']

        # Should be empty
        assert(not adminClient.getUpdateServiceList())

        # Add the first version of the updateservice
        us1Id = adminClient.addUpdateService(*us1)
        assert(len(adminClient.getUpdateServiceList()) == 1)

        # Now whack it
        adminClient.delUpdateService(us1Id)

        # Expect an empty list
        self.failUnlessEqual(len(adminClient.getUpdateServiceList()), 0,
                "Should be zero update services in the database "
                "after deletion")

    @fixtures.fixture("Full")
    def testFetchNonExistentUpdateService(self, db, data):
        # Expect an exception if it we attempt to retrieve it
        adminClient = self.getClient("admin")
        self.failUnlessRaises(UpdateServiceNotFound,
                adminClient.getUpdateService, 34343)

    @fixtures.fixture("Full")
    def testGetUpdateServiceList(self, db, data):
        adminClient = self.getClient("admin")

        us1 = ['foo.example.com',
                helperfuncs.generateMirrorUserName(FQDN, 'foo.example.com'),
                STOCK_MIRROR_PASSWORD, 'Foo 1']

        us2 = ['bar.example.com',
                helperfuncs.generateMirrorUserName(FQDN, 'bar.example.com'),
                STOCK_MIRROR_PASSWORD, 'Bar 1']

        # Expect an empty list
        self.failUnlessEqual(len(adminClient.getUpdateServiceList()), 0,
                "Should be zero update services in the database "
                "after deletion")

        # add an update service
        us1Id = adminClient.addUpdateService(*us1)

        # Check list
        list1 = adminClient.getUpdateServiceList()
        self.failUnlessEqual(len(list1), 1, "Expected one update service "
                "record in the list")
        self.failUnlessEqual(list1, [ [us1Id] + us1 ],
                "List contents incorrect")

        # add an update service
        us2Id = adminClient.addUpdateService(*us2)

        # Check list
        list2 = adminClient.getUpdateServiceList()
        self.failUnlessEqual(len(list2), 2, "Expected two update service "
                "records in the list")
        self.failUnlessEqual(list2, [ [us1Id] + us1, [us2Id] + us2 ],
                "List contents incorrect")

    @fixtures.fixture("Full")
    def testGetUpdateService(self, db, data):
        adminClient = self.getClient("admin")

        us1 = ['foo.example.com',
                helperfuncs.generateMirrorUserName(FQDN, 'foo.example.com'),
                STOCK_MIRROR_PASSWORD, 'Foo 1']

        # add an update service
        us1Id = adminClient.addUpdateService(*us1)

        # Check list
        us1Returned = adminClient.getUpdateService(us1Id)
        self.failUnlessEqual(us1[0], us1Returned['hostname'])
        self.failUnlessEqual(us1[2], us1Returned['mirrorPassword'])
        self.failUnlessEqual(us1[3], us1Returned['description'])


    @fixtures.fixture("Full")
    def testOutboundMirror(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])
        usid = adminClient.addUpdateService("www.example.com", "adminuser",
                "adminpass", "This is mah mirror!")
        adminClient.setOutboundMirrorTargets(omid, [usid])

        # not using releases
        self.assertFalse(adminClient.isProjectMirroredByRelease(projectId))

        labels = adminClient.getOutboundMirrors()
        self.failUnlessEqual(labels,
            [[1, projectId, sourceLabel, False, False, [], 0, True, False]])

        adminClient.delOutboundMirror(1)
        labels = adminClient.getOutboundMirrors()
        self.failUnlessEqual(labels, [])

    @fixtures.fixture("Full")
    def testOutboundMirrorUseReleases(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel], 
            useReleases=True)
        usid = adminClient.addUpdateService("www.example.com", "adminuser",
                "adminpass", "This is mah mirror!")
        adminClient.setOutboundMirrorTargets(omid, [usid])

        # using releases
        self.assertTrue(adminClient.isProjectMirroredByRelease(projectId))

        labels = adminClient.getOutboundMirrors()
        self.failUnlessEqual(labels,
            [[1, projectId, sourceLabel, False, False, [], 0, True, True]])

        adminClient.delOutboundMirror(1)
        labels = adminClient.getOutboundMirrors()
        self.failUnlessEqual(labels, [])


    @fixtures.fixture("Full")
    def testOutboundMirrorAllLabels(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])
        usid = adminClient.addUpdateService("www.example.com", "adminuser",
                "adminpass", "This is mah mirror!")
        adminClient.setOutboundMirrorTargets(omid, [usid])

        assert(adminClient.getOutboundMirrors()[0][3] is False)
        cu = db.cursor()
        cu.execute("UPDATE OutboundMirrors SET allLabels = 1")
        db.commit()
        assert(adminClient.getOutboundMirrors()[0][3] is True)

        cu.execute("DELETE FROM OutboundMirrors")
        db.commit()

        omid = adminClient.addOutboundMirror(projectId, [sourceLabel], allLabels = True)
        assert(adminClient.getOutboundMirrors()[0][3] is True)

    @fixtures.fixture("Full")
    def testOutboundMirrorRecurse(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])
        usid = adminClient.addUpdateService("www.example.com", "adminuser",
                "adminpass", "This is mah mirror!")
        adminClient.setOutboundMirrorTargets(omid, [usid])

        assert(adminClient.getOutboundMirrors()[0][4] is False)
        cu = db.cursor()
        cu.execute("UPDATE OutboundMirrors SET recurse = 1")
        db.commit()
        assert(adminClient.getOutboundMirrors()[0][4] is True)

        cu.execute("DELETE FROM OutboundMirrors")
        db.commit()

        omid = adminClient.addOutboundMirror(projectId, [sourceLabel], recurse = True)
        assert(adminClient.getOutboundMirrors()[0][4] is True)

    @fixtures.fixture("Full")
    def testOutboundMatchInitial(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])

        # ensure this doesn't raise ItemNotFound
        self.failUnlessEqual(adminClient.getOutboundMirrorMatchTroves(omid), [],
                    "Listing empty matchTroves failed")

        # however, this should raise
        self.assertRaises(database.ItemNotFound, adminClient.getOutboundMirrorMatchTroves, 2)

    @fixtures.fixture("Full")
    def testOutboundMatchBasic(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])
        adminClient.setOutboundMirrorMatchTroves(omid, ["-.*:source$"])
        self.failUnlessEqual(adminClient.getOutboundMirrorMatchTroves(1),
                ["-.*:source$"])

    @fixtures.fixture("Full")
    def testOutboundMatchComposite(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])
        usid = adminClient.addUpdateService("www.example.com", "adminuser",
                "adminpass", "This is mah mirror!")
        adminClient.setOutboundMirrorTargets(omid, [usid])
        adminClient.setOutboundMirrorMatchTroves(omid, ['-.*:source$', '-.*:debuginfo$'])
        self.failUnlessEqual(adminClient.getOutboundMirrorMatchTroves(omid),
               ['-.*:source$', '-.*:debuginfo$'])

    @fixtures.fixture("Full")
    def testOutboundMatchReordered(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])
        usid = adminClient.addUpdateService("www.example.com", "adminuser",
                "adminpass", "This is mah mirror!")
        adminClient.setOutboundMirrorTargets(omid, [usid])

        adminClient.setOutboundMirrorMatchTroves(omid,
                                           ['-.*:source$', '-.*:debuginfo$'])
        assert(adminClient.getOutboundMirrorMatchTroves(omid) == \
               ['-.*:source$', '-.*:debuginfo$'])

        adminClient.setOutboundMirrorMatchTroves(omid,
                                           ['-.*:debuginfo$', '-.*:source$' ])
        assert(adminClient.getOutboundMirrorMatchTroves(1) == \
               ['-.*:debuginfo$', '-.*:source$'])


    @fixtures.fixture("Full")
    def testOutboundMatchParams(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])
        usid = adminClient.addUpdateService("http://www.example.com/conary/", "mirror", "mirrorpass", "This is mah mirror!")
        adminClient.setOutboundMirrorTargets(omid, [usid])

        self.assertRaises(mint_error.ParameterError,
                          adminClient.setOutboundMirrorMatchTroves,
                          omid, 'wrong')

        self.assertRaises(mint_error.ParameterError,
                          adminClient.setOutboundMirrorMatchTroves,
                          omid, ['also_wrong'])

        for matchStr in ('+right', '-right'):
            # ensure no error is raised for properly formed params
            adminClient.setOutboundMirrorMatchTroves(omid, [matchStr])

    @fixtures.fixture("Full")
    def testOutboundMirrorOrdering(self, db, data):
        adminClient = self.getClient("admin")

        def _build(idList, orderList):
            cu = db.cursor()
            cu.execute("DELETE FROM OutboundMirrors")

            for id, order in zip(idList, orderList):
                cu.execute("""INSERT INTO OutboundMirrors
                    (outboundMirrorId, mirrorOrder, sourceProjectId, targetLabels)
                    VALUES(?, ?, ?, "abcd")""", id, order, data['projectId'])
            db.commit()

        def _getOrder():
            cu = db.cursor()
            cu.execute("SELECT outboundMirrorId, mirrorOrder FROM OutboundMirrors ORDER BY mirrorOrder")
            return [(x[0], x[1]) for x in cu.fetchall()]

        _build([0, 1, 2, 3], [0, 1, 2, 3])

        adminClient.delOutboundMirror(1)
        self.failUnlessEqual(_getOrder(), [(0, 0), (2, 1), (3, 2)])

        adminClient.server._server.setOutboundMirrorOrder(2, 0)
        self.failUnlessEqual(_getOrder(), [(2, 0), (0, 1), (3, 2)])

        adminClient.server._server.setOutboundMirrorOrder(3, 3)
        self.failUnlessEqual(_getOrder(), [(2, 0), (0, 1), (3, 2)])

        newId = adminClient.addOutboundMirror(data['projectId'], ['frob'])

        self.failUnlessEqual(_getOrder(), [(2, 0), (0, 1), (3, 2), (newId, 3)])

    @fixtures.fixture("Full")
    def testOutboundMirrorTargets(self, db, data):
        projectId = data['projectId']
        adminClient = self.getClient("admin")
        project = adminClient.getProject(projectId)
        sourceLabel = project.getLabel()
        omid = adminClient.addOutboundMirror(projectId, [sourceLabel])

        target1 = ['target1.example.com',
                helperfuncs.generateMirrorUserName(FQDN,
                    'target1.example.com'),
                STOCK_MIRROR_PASSWORD, 'Target One']
        target2 = ['target2.example.com',
                helperfuncs.generateMirrorUserName(FQDN,
                    'target2.example.com'),
                STOCK_MIRROR_PASSWORD, 'Target Two']

        # add Update Services
        rus1Id = adminClient.addUpdateService(*target1)
        rus2Id = adminClient.addUpdateService(*target2)

        # add a target
        targetSet = adminClient.setOutboundMirrorTargets(omid, [rus1Id])

        # verify it got put in
        self.failUnlessEqual(targetSet, [rus1Id])
        self.failUnlessEqual(adminClient.getOutboundMirrorTargets(omid),
                [ [ rus1Id ] + target1 ])

        # add another target
        targetSet = adminClient.setOutboundMirrorTargets(omid, [rus1Id, rus2Id])

        # verify it got put in, also
        self.failUnlessEqual(targetSet, [rus1Id, rus2Id])
        self.failUnlessEqual(adminClient.getOutboundMirrorTargets(omid),
                [ [ rus1Id ] + target1, [ rus2Id ] + target2 ])

        # delete the first target
        targetSet = adminClient.setOutboundMirrorTargets(omid, [rus2Id])

        # verify it got deleted
        self.failUnlessEqual(targetSet, [rus2Id])
        self.failUnlessEqual(adminClient.getOutboundMirrorTargets(omid),
                [ [ rus2Id ] + target2 ])

        # now delete the whole mirror
        adminClient.delOutboundMirror(omid)

        self.assertRaises(database.ItemNotFound,
                adminClient.getOutboundMirror, omid)

        # make sure cascading deletes worked
        self.failUnlessEqual([], adminClient.getOutboundMirrorTargets(omid))


