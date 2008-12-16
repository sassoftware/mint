#
# Copyright (C) 2006-2008 rPath, Inc.
# All rights reserved.
#

import raa.web
import os
import raapluginstest
import raatest
import tempfile
import mock
from testrunner import resources

from raa.modules.raasrvplugin import rAASrvPlugin
from raa.lib import command
from raa.rpath_error import RestartWebException
from rPath.rbasetup.srv import rbasetup as rbasetup_srv

from mint import config

MINT_CONFIG_ROOT="""
# A file that approxiamates what the setup plugin will read.

# This is rBuilder
productName             rBuilder

# Use SQLite backend
dbDriver                sqlite
dbPath                  /srv/rbuilder/data/db

# Conary repository paths
reposPath               /srv/rbuilder/repos/
reposContentsDir        /srv/rbuilder/repos/%s/contents/

# Base directory (as seen by webserver)
basePath                /

# Support contact information
supportContactTXT       your local system administrator
supportContactHTML      <p>your local system administrator</p>

# Group template label
groupApplianceLabel     rap.rpath.com@rpath:linux-1

# This gets overridden by the rBuilder-generated configuration
configured              False
companyName             Your Company Name Here
corpSite                http://www.example.com/
defaultBranch           yournamespace:yourtag
namespace               yournamespace

# Miscellany
authUser                mintauth
authPass                mintpass
debugMode               False

# Buildtypes that are not supported (remove and use at your own risk)
excludeBuildTypes       STUB_IMAGE
excludeBuildTypes       NETBOOT_IMAGE
excludeBuildTypes       PARALLELS
excludeBuildTypes       AMI

# Activate Internal Conary Proxy for rBuilder
useInternalConaryProxy  True

# include our "generated" file; to be replaced when loading
includeConfigFile %(testGeneratedFile)s
"""

class rBASetupTest(raatest.rAATest):

    def _createTempfile(self):
        fd, tmpfilename = tempfile.mkstemp()
        os.close(fd)
        return tmpfilename

    def _removeFile(self, fn):
        if fn:
            try:
                os.unlink(fn)
            except Exception, e:
                print "Failed to unlink %s during test (reason: %s)" % \
                        (self.testconfigfile, str(e))

    def setUp(self):
        # Save for later
        self.oldinit = rbasetup_srv.rBASetup.__init__
        self.oldConfig = config.RBUILDER_CONFIG
        self.oldGeneratedConfig = config.RBUILDER_GENERATED_CONFIG
        self.mockOSSystem = mock.MockObject()
        self.mock(os, 'system', self.mockOSSystem)


        rbasetup_srv.rBASetup.__init__ = lambda *args: None
        self.rbasetupsrv = rbasetup_srv.rBASetup()

        config.RBUILDER_CONFIG = self._createTempfile()
        config.RBUILDER_GENERATED_CONFIG = self._createTempfile()

        # Write out our test rbuilder config
        f = open(config.RBUILDER_CONFIG, 'w')
        f.write(MINT_CONFIG_ROOT % {'testGeneratedFile': config.RBUILDER_GENERATED_CONFIG})
        f.close()

        # Write out our test rbuilder generated config
        f = open(config.RBUILDER_GENERATED_CONFIG, 'w')
        f.write("# This file is blank and waiting to be filled in")
        f.close()

        raaFramework = raapluginstest.webPluginTest()
        raaFramework.pseudoroot = raa.web.getWebRoot().rbasetup
        self.rbasetupweb = raa.web.getWebRoot().rbasetup
        self.root = raaFramework.pseudoroot
        self.rbasetupweb.server = self.rbasetupweb

        raatest.rAATest.setUp(self)

    def tearDown(self):
        # Cleanup our configuration files
        self._removeFile(config.RBUILDER_CONFIG)
        self._removeFile(config.RBUILDER_GENERATED_CONFIG)

        # Reset
        rbasetup_srv.rBASetup.__init__ = self.oldinit
        config.RBUILDER_CONFIG = self.oldConfig
        config.RBUILDER_GENERATED_CONFIG = self.oldGeneratedConfig

        raatest.rAATest.tearDown(self)

    def testIndex(self):
        # TODO: write web tests here
        pass

    def testGetConfig(self):
        """
        Make sure that the get configuration path can:
        1. Read a configuration.
        2. Return a dict that contains only the subset of items
           required for generating an rBuilder config.
        3. isConfigured is False at the start.
        4. Make sure return types are as we expect:
           a. values of configurable options are doubles
           b. NoneType is not present in the results (for XML-RPC's sake)
        """

        # Call the backend function
        isConfigured, configurableOptions = \
                raapluginstest.backendCaller(self.rbasetupsrv.getRBAConfiguration)

        # Make sure that we are *not* configured now
        self.failIf(isConfigured, "Initial setup should not be configured")

        # Check expected keys.
        for k in configurableOptions.keys():
            if k in config.keysForGeneratedConfig:
                v = configurableOptions[k]
                self.assertNotEqual(v, None, "None should not be present")
                configurableOptions.pop(k)

        # Configurable options should be empty, unless we
        # got extraneous stuff
        self.failIf(configurableOptions, "Too many configurable options returned")

    def testUpdateConfig(self):
        """
        Verify that a configuration can be written by the backend.
        Make sure it has only the keys we expect.
        """

        # Pass in a dict that has some values we may receive from the
        # web frontend. This dict will have some values that should
        # not be saved in the generated config.
        newValues = dict(hostName="justified",
                         siteDomainName="mumu.org",
                         secureHost="ancient.mumu.org",
                         companyName="The JAMMs",
                         bugsEmail="icecreamvan@mumu.org",
                         waddle="frob")

        # Call the backend function
        ret = raapluginstest.backendCaller(self.rbasetupsrv.updateRBAConfig,
                newValues)

        # Make sure return is OK
        self.failUnlessEqual(ret, True,
                "Expected return of True from backend call")

        # Read the generated config back
        cfgfile = file(config.RBUILDER_GENERATED_CONFIG, 'r').read()

        # Check for rogue elements
        self.failIf("waddle" in cfgfile,
            "Unexpected keys have infiltrated the generated config!")

        # We have no need for this guy anymore
        newValues.pop("waddle")

        # Merge values written into a config, check
        newCfg = config.MintConfig()
        newCfg.read(config.RBUILDER_GENERATED_CONFIG)

        # Check values
        for k in newValues:
            self.assertEqual(newCfg[k], newValues[k])

        # And now, let's use the backend to get the config, too
        isConfigured, configurableOptions = \
                raapluginstest.backendCaller(self.rbasetupsrv.getRBAConfiguration)

        # We should be configured now
        self.failUnless(isConfigured,
                "We should be configured now (backend call missed it)")

        # Final check
        for k in newValues:
            self.assertEqual(configurableOptions[k], newValues[k])

    def testRestartApache(self):
        """
        Exercises the Apache restart option.
        """

        # Call the backend function (note: setUp has mocked os.system)
        self.mockOSSystem._mock.setReturn(0, "/sbin/service httpd restart")
        ret = raapluginstest.backendCaller(self.rbasetupsrv.restartApache)

        # Make sure the right things happened
        self.mockOSSystem._mock.assertCalled("/sbin/service httpd restart")
        self.failUnless(ret, "Expected a successful return in the normal case")

        # Now, simulate an error
        self.mockOSSystem._mock.setReturn(256, "/sbin/service httpd restart")
        ret = raapluginstest.backendCaller(self.rbasetupsrv.restartApache)

        # Check error path
        self.mockOSSystem._mock.assertCalled("/sbin/service httpd restart")
        self.failIf(ret, "Expected a failed return in the error case")

        # Finally, simulate an exception
        self.mockOSSystem._mock.raiseErrorOnAccess(OSError)
        ret = raapluginstest.backendCaller(self.rbasetupsrv.restartApache)

        # Check exception path
        self.mockOSSystem._mock.assertCalled("/sbin/service httpd restart")
        self.failIf(ret, "Expected a failed return in the exception case")

