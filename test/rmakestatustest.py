#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

import sys
import xmlrpclib

import fixtures
from conary import versions
from mint import database
from mint import mint_error

from mint_rephelp import WebRepositoryHelper
from mint_rephelp import MINT_PROJECT_DOMAIN

from mint.rmakeconstants import buildjob, buildtrove, currentApi

class rMakeStatusApiOneTest(WebRepositoryHelper):
    def _jobStateUpdated(self, uri, jobId, status, statusMessage):
        serverProxy = xmlrpclib.ServerProxy(uri)
        event = [['JOB_STATE_UPDATED', status], [jobId, status, statusMessage]]
        serverProxy.receiveEvents(1, [event])

    def _jobLogUpdated(self, uri, jobId, status, statusMessage):
        serverProxy = xmlrpclib.ServerProxy(uri)
        event = [['JOB_LOG_UPDATED', ''], [jobId, status, statusMessage]]
        serverProxy.receiveEvents(1, [event])

    def _jobTrovesSet(self, uri, jobId, troveSet):
        serverProxy = xmlrpclib.ServerProxy(uri)
        event = [['JOB_TROVES_SET', buildjob.JOB_STATE_STARTED],
                 [jobId, troveSet]]
        serverProxy.receiveEvents(1, [event])

    def _jobCommitted(self, uri, jobId, troveSet):
        serverProxy = xmlrpclib.ServerProxy(uri)
        event = [['JOB_COMMITTED', buildjob.JOB_STATE_COMMITTED],
                 [jobId, troveSet]]
        serverProxy.receiveEvents(1, [event])

    def _troveStateUpdated(self, uri, jobId, troveTuple, status,
                           statusMessage):
        serverProxy = xmlrpclib.ServerProxy(uri)
        event = [['TROVE_STATE_UPDATED', status],
                 [[jobId, troveTuple], status, statusMessage]]
        serverProxy.receiveEvents(1, [event])

    def _troveLogUpdated(self, uri, jobId, troveTuple, status,
                           statusMessage):
        serverProxy = xmlrpclib.ServerProxy(uri)
        event = [['TROVE_LOG_UPDATED', ''],
                 [[jobId, troveTuple], status, statusMessage]]
        serverProxy.receiveEvents(1, [event])

    def testJobId(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]
        jobId = 14
        self._jobStateUpdated(uri, jobId,
                              buildjob.JOB_STATE_STARTED, 'starting')

        cu = self.db.cursor()
        cu.execute('SELECT jobId FROM rMakeBuild')
        self.failIf(cu.fetchone()[0] != jobId,
                    "Starting a job failed to update jobId")

    def testJobIdUUID(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]
        uri = '/'.join(uri.split('/')[:-1]) + '/' + (32 * '0')
        jobId = 36
        self._jobStateUpdated(uri, jobId,
                              buildjob.JOB_STATE_STARTED, 'starting')

        cu = self.db.cursor()
        cu.execute('SELECT jobId FROM rMakeBuild')
        self.failIf(cu.fetchone()[0] != None,
                    "Bad UUID updated job")

    def testCommittingTranslation(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]

        self._jobStateUpdated(uri, 27,
                              buildjob.JOB_STATE_COMMITTING, '')

        cu = self.db.cursor()
        cu.execute('SELECT statusMessage FROM rMakeBuild')

        self.failIf(cu.fetchone()[0] != 'Committing...',
                    "Committing status doesn't have sane message")

    def testCommittingUUID(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]
        uri = '/'.join(uri.split('/')[:-1]) + '/' + (32 * '0')

        self._jobStateUpdated(uri, 44,
                              buildjob.JOB_STATE_COMMITTING, '')

        cu = self.db.cursor()
        cu.execute('SELECT statusMessage FROM rMakeBuild')

        self.failIf(cu.fetchone()[0] == 'Committing...',
                    "Committing status wrongly updated")

    def testCommittedTranslation(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]

        self._jobStateUpdated(uri, 5,
                              buildjob.JOB_STATE_COMMITTED, '')

        cu = self.db.cursor()
        cu.execute('SELECT statusMessage FROM rMakeBuild')

        self.failIf(cu.fetchone()[0] != 'Successfully Committed',
                    "Committed status doesn't have sane message")

    def testCommittedUUID(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]
        uri = '/'.join(uri.split('/')[:-1]) + '/' + (32 * '0')

        self._jobStateUpdated(uri, 2,
                              buildjob.JOB_STATE_COMMITTED, '')

        cu = self.db.cursor()
        cu.execute('SELECT statusMessage FROM rMakeBuild')

        self.failIf(cu.fetchone()[0] == 'Successfully Committed',
                    "Committed status illegally updated")

    def testJobLog(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]

        self._jobLogUpdated(uri, 10, buildjob.JOB_STATE_BUILD, 'building')

        cu = self.db.cursor()
        cu.execute('SELECT status, statusMessage FROM rMakeBuild')
        self.failIf(cu.fetchone() != (4, 'building'),
                    'log status had no effect')

    def testJobLogUUID(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]
        uri = '/'.join(uri.split('/')[:-1]) + '/' + (32 * '0')

        self._jobLogUpdated(uri, 4, buildjob.JOB_STATE_BUILD, 'building')

        cu = self.db.cursor()
        cu.execute('SELECT status, statusMessage FROM rMakeBuild')
        self.failIf(cu.fetchone() != \
                    (buildjob.JOB_STATE_QUEUED, 'Waiting for rMake Server'),
                    'log status allowed to be set by wrong UUID')

    def testTroveSet(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]

        self._jobTrovesSet( \
            uri, 44, [['foo', '/test.rpath.local@rpl:devel/0.0:1.0.0-1', '']])
        cu = self.db.cursor()
        cu.execute("SELECT status,statusMessage FROM rMakeBuildItems")

        self.failIf(cu.fetchone() != \
                    (buildtrove.TROVE_STATE_INIT,
                     'foo=/test.rpath.local@rpl:devel/1.0.0-1[]'),
                    "trove status not set")

    def testTroveSetUUID(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]
        uri = '/'.join(uri.split('/')[:-1]) + '/' + (32 * '0')

        self._jobTrovesSet( \
            uri, 76, [['foo', '/test.rpath.local@rpl:devel/0.0:1.0.0-1', '']])
        cu = self.db.cursor()
        cu.execute("SELECT status,statusMessage FROM rMakeBuildItems")

        self.failIf(cu.fetchone() != (0, None),
                    "trove status illegally set")

    def testJobCommitted(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]

        self._jobCommitted( \
            uri, 15, [['foo', '/test.rpath.local@rpl:devel/0.0:1.0.0-1-1',
                       '']])
        cu = self.db.cursor()
        cu.execute("SELECT status,statusMessage FROM rMakeBuildItems")

        self.failIf(cu.fetchone() != \
                    (buildtrove.TROVE_STATE_BUILT,
                     'foo=/test.rpath.local@rpl:devel/1.0.0-1-1[]'),
                    "trove status not set to built")

    def testJobCommittedUUID(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]
        uri = '/'.join(uri.split('/')[:-1]) + '/' + (32 * '0')

        self._jobCommitted( \
            uri, 8, [['foo', '/test.rpath.local@rpl:devel/0.0:1.0.0-1-1',
                       '']])
        cu = self.db.cursor()
        cu.execute("SELECT status,statusMessage FROM rMakeBuildItems")

        self.failIf(cu.fetchone() != (0, None),
                    "trove status illegally set to built")

    def testTroveState(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]

        self._troveStateUpdated( \
            uri, 35, ['foo', '/test.rpath.local@rpl:devel/0.0:1.0.0-1', ''],
            buildtrove.TROVE_STATE_BUILDING, 'building')

        cu = self.db.cursor()
        cu.execute("SELECT status, statusMessage FROM rMakeBuildItems")
        self.failIf(cu.fetchone() != \
                    (buildtrove.TROVE_STATE_BUILDING, 'building'),
                    "trove status not set for status")

    def testTroveStateUUID(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]
        uri = '/'.join(uri.split('/')[:-1]) + '/' + (32 * '0')

        self._troveStateUpdated( \
            uri, 96, ['foo', '/test.rpath.local@rpl:devel/0.0:1.0.0-1', ''],
            buildtrove.TROVE_STATE_BUILDING, 'building')

        cu = self.db.cursor()
        cu.execute("SELECT status, statusMessage FROM rMakeBuildItems")
        self.failIf(cu.fetchone() != (0, None),
                    "trove status illegally set for status")

    def testTroveLog(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]

        self._troveLogUpdated( \
            uri, 3, ['foo', '/test.rpath.local@rpl:devel/0.0:1.0.0-1', ''],
            buildtrove.TROVE_STATE_BUILDING, 'blah blah')

        cu = self.db.cursor()
        cu.execute("SELECT status, statusMessage FROM rMakeBuildItems")
        self.failIf(cu.fetchone() != \
                    (buildtrove.TROVE_STATE_BUILDING, 'blah blah'),
                    "trove status not set for log")

    def testTroveLogUUID(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        self.moveToServer(project, 1)
        rMakeBuild = client.createrMakeBuild('foo')

        trvName = 'foo'
        trvLabel = 'test.rpath.local@rpl:devel'

        rMakeBuild.addTrove(trvName, trvLabel)
        xml = rMakeBuild.getXML('build')

        uri = xml.split('rBuilder xmlrpc ')[1].split('<')[0]
        uri = '/'.join(uri.split('/')[:-1]) + '/' + (32 * '0')

        self._troveLogUpdated( \
            uri, 88, ['foo', '/test.rpath.local@rpl:devel/0.0:1.0.0-1', ''],
            buildtrove.TROVE_STATE_BUILDING, 'blah blah')

        cu = self.db.cursor()
        cu.execute("SELECT status, statusMessage FROM rMakeBuildItems")

        self.failIf(cu.fetchone() != (0, None),
                    "trove status illegally set for log")

    def testBadApi(self):
        uri = 'http://%s:%s/rmakesubscribe/BOGUS_UUID' % \
              (self.server, self.port)

        serverProxy = xmlrpclib.ServerProxy(uri)

        apiVer = 9999999
        self.assertRaises(xmlrpclib.ProtocolError,
                          serverProxy.receiveEvents, apiVer, [])
        try:
            serverProxy.receiveEvents(apiVer, [])
        except xmlrpclib.ProtocolError, e:
            # giving a bad API version yields bad request
            self.failIf(e.errcode != 400)

    def testBadMethod(self):
        uri = 'http://%s:%s/rmakesubscribe/BOGUS_UUID' % \
              (self.server, self.port)

        serverProxy = xmlrpclib.ServerProxy(uri)

        self.assertRaises(xmlrpclib.ProtocolError, serverProxy.badMethod)
        try:
            serverProxy.badMethod
        except xmlrpclib.ProtocolError, e:
            # giving a bad method yields bad method
            self.failIf(e.errcode != 405)

    def testFetch(self):
        self.fetch('/rmakesubscribe/BOGUS_UUID', ok_codes = [405])
        try:
            self.fetch('/rmakesubscribe/BOGUS_UUID')
        except:
            ec, e, bt = sys.exc_info()
            # using a get request results in http: bad request (must be post)
            self.failIf(e.response.code != 405)

    def testXmlContent(self):
        try:
            self.post('/rmakesubscribe/BOGUS_UUID', {})
        except:
            ec, e, bt = sys.exc_info()
            # using a post request results in assertion error (must be xml)
            self.failIf('405' not in str(e),
                        "posting non-xml content didn't result in bad request")


if __name__ == "__main__":
    testsuite.main()
