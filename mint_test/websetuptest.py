#!/usr/bin/python2.4
#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

import base64
import testsuite
testsuite.setup()

import copy
import os
import time

from mint import config

from mint.web import setup, hooks
from mint.web.webhandler import HttpForbidden, HttpNotFound, HttpMoved

import fixtures
import mint_rephelp
from mint_rephelp import FakeRequest


class MintTest(mint_rephelp.WebRepositoryHelper):
    def testFirstTimeSetupRedirect(self):
        raise testsuite.SkipTestException("this test needs to be re-done")
        self.mintCfg.configured = False
        self.resetRepository()

        page = self.assertCode('/', code = 302)
        assert(page.headers['Location'] == '/setup/')

        page = self.assertContent('/setup/', ok_codes = [302],
            content = "Please create a file called")

        sid = self.cookies.items()[0][1]['/']['pysid'].value
        secureFile = self.mintCfg.dataPath + "/" + sid + ".txt"

        f = file(secureFile, 'w')
        f.close()

        page = self.assertContent('/setup/', ok_codes = [200],
            content = "rBuilder Build Setup")

        # set site back to configured
        self.mintCfg.configured = True

class SetupHandlerTest(fixtures.FixturedUnitTest):

    def __system(*args):
        return 0

    def __sleep(*args):
        return 0

    def __ShimMintClient(*args):
        return FakeMintClient(*args)

    def setUp(self):
        fixtures.FixturedUnitTest.setUp(self)
        self.sh = setup.SetupHandler()
        self.sh.cfg = config.MintConfig()
        self.sh.cfg.hostname = 'foo'
        self.sh.cfg.externalDomainName = 'test.local'
        self.sh.cfg.siteDomainName = 'test.local'
        self.sh.cfg.configured = False

        self.oldsystem = os.system
        os.system = self.__system

        self.oldsleep = time.sleep
        time.sleep = self.__sleep

    def tearDown(self):
        fixtures.FixturedUnitTest.tearDown(self)
        os.system = self.oldsystem
        time.sleep = self.oldsleep

    @testsuite.context("more_cowbell")
    @fixtures.fixture("Full")
    def testSetup(self, db, data):
        self.sh.req = FakeRequest('foo.test.local', 'GET', '/setup')
        client = self.getClient('admin')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': '', 'client': client}
        func = self.sh.handle(context)
        
        # test with terms of service accepted
        ret = func(auth, True)
        self.failUnless('<h1>rBuilder Configuration</h1>' in ret)
        
        # test with terms of service not accepted
        ret = func(auth, False)
        self.failUnless('<h1>rBuilder Terms of Service</h1>' in ret)

    @testsuite.context("more_cowbell")
    @fixtures.fixture("Full")
    def testSetupBadRequest(self, db, data):
        """ Test failure (hostname is not FQDN) """
        self.sh.req = FakeRequest('foo', 'GET', '/setup')
        client = self.getClient('admin')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': '', 'client': client}
        func = self.sh.handle(context)
        ret = func(auth)
        self.failUnless('You must access the rBuilder server as a fully-qualified domain name' in ret)

    @testsuite.context("more_cowbell")
    @fixtures.fixture("Full")
    def testSetupNonAdmin(self, db, data):
        """ Test failure (user is non-admin) """
        self.sh.req = FakeRequest('foo.test.local', 'GET', '/setup')
        self.sh.cfg.configured = True

        client = self.getClient('user')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': '', 'client': client}
        self.assertRaises(HttpForbidden, self.sh.handle, context)

    @testsuite.context("more_cowbell")
    @fixtures.fixture("Full")
    def testSetupBadCommand(self, db, data):
        """ Test failure (bad command given) """
        self.sh.req = FakeRequest('foo.test.local', 'GET', '/setup')

        client = self.getClient('user')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': 'zxcvb', 'client': client}
        self.assertRaises(HttpNotFound, self.sh.handle, context)

    @testsuite.context("more_cowbell")
    @fixtures.fixture("Empty")
    def testProcessSetupAndRestart(self, db, data):
        """ Test process setup"""
        fields = { 'hostName': 'foo',
                   'siteDomainName': 'rpath.local',
                   'corpSite': 'http://foo.bar.baz',
                   'defaultBranch': 'foo:bar',
                   'namespace': 'foospace',
                   'new_username': 'fooadmin',
                   'new_email': 'fooadmin@rpath.local',
                   'new_password': 'foopass',
                   'new_password2': 'foopass',
                   'allowNamespaceChange': False }

        generatedConfigFilePath = os.path.join(self.cfg.dataPath, 'rbuilder-generated.conf')
        rmakeClientConfigFilePath = os.path.join(self.cfg.dataPath, 'rmake-client.conf')
        rmakeConfigFilePath = os.path.join(self.cfg.dataPath, 'rmake.conf')
        self.sh.req = FakeRequest('foo.rpath.local', 'POST', '/processSetup')
        self.sh.req.options = {'generatedConfigFile':generatedConfigFilePath,
            'rmakeClientConfigFilePath':rmakeClientConfigFilePath,
            'rmakeConfigFilePath':rmakeConfigFilePath}
        self.sh.cfg = copy.deepcopy(self.cfg)
        self.sh.cfg.configured = False
        client = self.getClient('admin')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': 'processSetup', 'client': client, 'fields': fields}
        func = self.sh.handle(context)
        ret = func(auth = auth, **fields)
        self.failUnless('<h1>rBuilder Configuration Complete</h1>' in ret)

        # fake the include file here
        newCfg = copy.deepcopy(self.cfg)
        newCfg.includeConfigFile(generatedConfigFilePath)
        self.sh.cfg = newCfg
        context = {'auth': auth, 'cmd': 'restart', 'client': client}
        func = self.sh.handle(context)
        self.assertRaises(HttpMoved, func, auth)

        del newCfg

        self.failUnless(os.path.exists(generatedConfigFilePath))
        newCfg = config.MintConfig()
        newCfg.read(generatedConfigFilePath)

        # check stuff
        self.assertEqual(newCfg.configured, True)
        self.assertEqual(newCfg.hostName, 'foo')
        self.assertEqual(newCfg.siteDomainName, 'rpath.local')
        self.assertEqual(newCfg.corpSite, 'http://foo.bar.baz')
        self.assertEqual(newCfg.namespace, 'foospace')
        self.assertEqual(newCfg.defaultBranch, self.cfg.defaultBranch)
        self.assertTrue(len(newCfg.authPass) == 32)
        for x in newCfg.authPass:
            self.assertTrue(x in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
        oldPass = newCfg.authPass

        # rerun process setup again.
        fields = { 'hostName': 'foo',
                   'siteDomainName': 'rpath.local',
                   'corpSite': 'http://foo.bar.baz',
                   'defaultBranch': 'foo:bam',
                   'namespace': 'changed',
                   'allowNamespaceChange': False }

        context = {'auth': auth, 'cmd': 'processSetup', 'client': client, 'fields': fields}
        self.sh.cfg.configured = True
        func = self.sh.handle(context)
        ret = func(auth = auth, **fields)
        newCfg = config.MintConfig()
        newCfg.read(generatedConfigFilePath)
        # make sure that our update took
        assert(newCfg.namespace == 'changed')
        # but don't update the password!
        assert(newCfg.authPass == oldPass)

    @testsuite.context("more_cowbell")
    @fixtures.fixture("Empty")
    def testProcessSetupBadPasswords(self, db, data):
        """ Test password mismatch """
        fields = { 'hostName': 'foo',
                   'siteDomainName': 'rpath.local',
                   'new_username': 'fooadmin',
                   'new_email': 'fooadmin@rpath.local',
                   'new_password': 'foopass',
                   'new_password2': 'foopass43',
                   'namespace': 'rpl',
                   'allowNamespaceChange': False }

        self.sh.req = FakeRequest('foo.rpath.local', 'POST', '/processSetup')
        self.sh.cfg = self.cfg
        self.sh.cfg.configured = False
        client = self.getClient('admin')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': 'processSetup', 'client': client, 'fields': fields}
        func = self.sh.handle(context)
        ret = func(auth = auth, **fields)
        self.failUnless('<h1>rBuilder Configuration</h1>' in ret)

    @testsuite.context("more_cowbell")
    @fixtures.fixture("Empty")
    def testProcessSetupBlank(self, db, data):
        """ Test password mismatch """
        fields = { 'hostName': '',
                   'siteDomainName': '',
                   'new_username': '',
                   'new_email': '',
                   'new_password': '',
                   'new_password2': '',
                   'namespace': 'rpl',
                   'allowNamespaceChange': False }

        self.sh.req = FakeRequest('foo.rpath.local', 'POST', '/processSetup')
        self.sh.cfg = self.cfg
        self.sh.cfg.configured = False
        client = self.getClient('admin')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': 'processSetup', 'client': client, 'fields': fields}
        func = self.sh.handle(context)
        ret = func(auth = auth, **fields)
        self.failUnless('<h1>rBuilder Configuration</h1>' in ret)
        
    @testsuite.context("more_cowbell")
    @fixtures.fixture("Empty")
    def testProcessSetupBadNamespace(self, db, data):
        """ Test password mismatch """
        fields = { 'hostName': 'foo',
                   'siteDomainName': 'rpath.local',
                   'new_username': 'fooadmin',
                   'new_email': 'fooadmin@rpath.local',
                   'new_password': 'foopass',
                   'new_password2': 'foopass',
                   'namespace': 'rpl:1',
                   'allowNamespaceChange': True }

        self.sh.req = FakeRequest('foo.rpath.local', 'POST', '/processSetup')
        self.sh.cfg = self.cfg
        self.sh.cfg.configured = False
        client = self.getClient('admin')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': 'processSetup', 'client': client, 'fields': fields}
        func = self.sh.handle(context)
        ret = func(auth = auth, **fields)
        self.failUnless('<h1>rBuilder Configuration</h1>' in ret)

    @fixtures.fixture("Empty")
    def testBlockedCommit(self, db, data):
        # make sure anything by mintauth is localhost-only
        raise testsuite.SkipTestException("test skipped because commits aren't blocked anymore: needed for external group builder jobslaves")
        req = FakeRequest('foo.rpath.local', 'POST', '/blah')
        req.connection.remote_ip = '192.168.1.10'
        req.headers_in['Authorization'] = "Basic " + base64.encodestring("mintauth:randompass")

        ret = hooks.conaryHandler(req, self.cfg, '/')
        self.failUnlessEqual(ret, 403) # assert 403, permission denied


if __name__ == '__main__':
    testsuite.main()

