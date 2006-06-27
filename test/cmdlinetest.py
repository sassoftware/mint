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
from mint.cmdline import products

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN

# if RepositoryHelper.checkCommand were a classmethod, this test
# wouldn't have to be a RepositoryHelper class and could be faster.
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


if __name__ == "__main__":
    testsuite.main()
