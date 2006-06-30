#!/usr/bin/python2.4
#
# Copyright (c) 2006 rPath, Inc.
#
import os

import tempfile
import testsuite
import unittest
testsuite.setup()

import rephelp

from mint.cmdline import RBuilderMain
from mint.cmdline import products, users

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN

class CmdLineTest(unittest.TestCase):
    def checkRBuilder(self, cmd, fn, expectedArgs, cfgValues={},
                  returnVal=None, ignoreKeywords=False, **expectedKw):
        main = RBuilderMain()
        cmd += ' --skip-default-config'

        cfgFd, cfgFn = tempfile.mkstemp()
        try:
            cfgF = os.fdopen(cfgFd, "w")
            # this value doesn't really matter--just needs to be a parseable url
            cfgF.write("serverUrl http://testuser:testpass@mint.rpath.local/xmlrpc-private")
            cfgF.close()

            cmd += " --config-file=%s" % cfgFn
            return rephelp.RepositoryHelper.checkCommand(main.main, 'rbuilder ' + cmd, fn,
                                     expectedArgs, cfgValues, returnVal,
                                     ignoreKeywords, **expectedKw)
        finally:
            os.unlink(cfgFn)

    def testProductCreate(self):
        troveSpec = 'group-test=/testproject.%s@rpl:devel/1.0-1-1[is:x86]' % MINT_PROJECT_DOMAIN
        self.checkRBuilder('product-create testproject %s installable_iso' % troveSpec,
            'mint.cmdline.products.ProductCreateCommand.runCommand',
            [None, None, None, {}, ['product-create', 'testproject', troveSpec, 'installable_iso']])

        self.checkRBuilder('product-create testproject %s installable_iso --wait' % troveSpec,
            'mint.cmdline.products.ProductCreateCommand.runCommand',
            [None, None, None, {'wait': True}, ['product-create', 'testproject', troveSpec, 'installable_iso']])

    def testProductWait(self):
        self.checkRBuilder('product-wait 111',
            'mint.cmdline.products.ProductWaitCommand.runCommand',
            [None, None, None, {}, ['product-wait', '111']])

    def testUserCreate(self):
        self.checkRBuilder('user-create testuser test@example.com --password password',
            'mint.cmdline.users.UserCreateCommand.runCommand',
            [None, None, None, {'password': 'password'}, ['user-create', 'testuser', 'test@example.com']])


class CmdLineFuncTest(MintRepositoryHelper):
    def testProductCreate(self):
        client, userId = self.quickMintUser("test", "testpass")

        projectId = client.newProject("Foo", "testproject", MINT_PROJECT_DOMAIN)

        cmd = products.ProductCreateCommand()
        troveSpec = 'group-test=/testproject.%s@rpl:devel/1.0-1-1[is:x86]' % MINT_PROJECT_DOMAIN
        cmd.runCommand(client, None, {}, ['product-create', 'testproject', troveSpec, 'installable_iso'])

        project = client.getProject(projectId)
        product = project.getProducts()[0]
        assert(product.getTrove()[0] == 'group-test')
        assert(product.getJob())

    def testUserCreate(self):
        client, userId = self.quickMintAdmin("adminuser", "adminpass")

        cmd = users.UserCreateCommand()
        userId = cmd.runCommand(client, None, {'password': 'testpass'},
            ['user-create', 'testuser', 'test@example.com'])
        user = client.getUser(userId)
        assert(user.email == 'test@example.com')


if __name__ == "__main__":
    testsuite.main()
