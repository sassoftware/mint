#
# Copyright (C) 2006-2008 rPath, Inc.
# All rights reserved.
#

import raa.web
import os
import pwd
import raapluginstest
import raatest
import tempfile
from testutils import mock
from testrunner import resources

from raa.modules.raasrvplugin import rAASrvPlugin
from raa.lib import command
from raa.rpath_error import RestartWebException
from rPath.rbasetup.srv import rbasetup as rbasetup_srv

from mint import config
from mint import helperfuncs
from mint import mint_error
from mint import shimclient
from mint import rmake_setup

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

FAKE_GENERATED_CONFIG = """
configured                True
hostName                  justified
siteDomainName            mumu.com
companyName               Trancentral
corpSite                  http://www.mumu.com/
namespace                 klf
projectDomainName         mumu.com
externalDomainName        mumu.com
SSL                       True
secureHost                justified.mumu.com
bugsEmail                 klfisgonnarocku@mumu.com
adminMail                 klfisgonnarocku@mumu.com
requireSigs               False
authPass                  lasttraintotrancentral
reposDBDriver             sqlite
reposDBPath               /what/time/is/%s/love
"""

DEFAULT_STARTING_CONFIG = dict(hostName='justified',
                               siteDomainName='mumu.com',
                               namespace='yournamespace',
                               requireSigs=False,
                               )

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

        # Mock out a ton of crap by default
        self.mockOSSystem = mock.MockObject()
        self.mockOSSetUID = mock.MockObject()
        self.mockOSSetGID = mock.MockObject()
        self.mockOSSetGroups = mock.MockObject()
        self.mockOSFork = mock.MockObject()
        self.mockOS_exit = mock.MockObject()
        self.mockOSwaitpid = mock.MockObject()
        self.mockpwdGetPwNam = mock.MockObject()
        self.mockShimMintClient = mock.MockObject()
        self.mock(os, 'system', self.mockOSSystem)
        self.mock(os, 'setuid', self.mockOSSetUID)
        self.mock(os, 'setgid', self.mockOSSetGID)
        self.mock(os, 'setgroups', self.mockOSSetGroups)
        self.mock(os, 'fork', self.mockOSFork)
        self.mock(os, '_exit', self.mockOS_exit)
        self.mock(os, 'waitpid', self.mockOSwaitpid)
        self.mock(pwd, 'getpwnam', self.mockpwdGetPwNam)
        self.mock(shimclient, 'ShimMintClient', self.mockShimMintClient)

        # Make fork always pretend to be a child
        self.mockOSFork._mock.setDefaultReturn(0)

        # Make sure getpwname returns something stable
        self.mockpwdGetPwNam._mock.setReturn(
                ('apache', 'x', 48, 48, 'Apache', '/var/www', '/sbin/nologin'),
                'apache')

        rbasetup_srv.rBASetup.__init__ = lambda *args: None
        self.rbasetupsrv = rbasetup_srv.rBASetup()

        # Create some default configurations to work with for the sake of testing
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
        raaFramework.pseudoroot = raa.web.getWebRoot().rbasetup.rBASetup
        self.rbasetupweb = raa.web.getWebRoot().rbasetup.rBASetup
        self.root = raaFramework.pseudoroot
        self.rbasetupweb.server = self.rbasetupweb

        # Get the initial canned data (can be modified in any test)
        _ignored, self.initialConfigurableOptions = \
                raapluginstest.backendCaller(self.rbasetupsrv.getRBAConfiguration)

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

    def test_web_Index(self):
        """
        Make sure that the initial index page renders.
        """
        ret = None
        oldCallBackend = self.root.callBackend
        try:
            self.root.callBackend = raatest.backendFactory((False, self.initialConfigurableOptions))
            ret = self.callWithIdent(self.root.index)
        finally:
            self.root.callBackend = oldCallBackend
        self.failIf(ret['configured'],
                "Initially, the configuration should be marked as unconfigured.")
        self.failUnless(ret['allowNamespaceChange'],
                "Initially, the configuration's namespace should be changeable.")

    def test_web_IndexConfigured(self):
        """
        Make sure the configured flag is set when the backend sends it.
        """
        ret = None
        oldCallBackend = self.root.callBackend
        try:
            self.root.callBackend = raatest.backendFactory((True, self.initialConfigurableOptions))
            ret = self.callWithIdent(self.root.index)
        finally:
            self.root.callBackend = oldCallBackend
        self.failUnless(ret['isConfigured'],
                "The configuration should be marked as configured.")
        self.failUnless(ret['allowNamespaceChange'],
                "The configuration's namespace option still should be changeable.")

    def test_web_IndexNoNamespaceChange(self):
        """
        Make sure that the namespace is non-changable after it's been set.
        """
        self.initialConfigurableOptions['namespace'] = 'klf'
        ret = None
        oldCallBackend = self.root.callBackend
        try:
            self.root.callBackend = raatest.backendFactory((True, self.initialConfigurableOptions))
            ret = self.callWithIdent(self.root.index)
        finally:
            self.root.callBackend = oldCallBackend
        self.failUnless(ret['isConfigured'],
                "The configuration should be marked as configured.")
        self.failIf(ret['allowNamespaceChange'],
                "The configuration's namespace option should be frozen now.")

    def test_srv_GetConfig(self):
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

    def test_srv_UpdateConfig(self):
        """
        Verify that a configuration can be written by the backend.
        Make sure it has only the keys we expect.
        """

        # Pass in a dict that has some values we may receive from the
        # web frontend. This dict will have some values that should
        # not be saved in the generated config.
        newValues = dict(hostName="justified",
                         siteDomainName="mumu.org",
                         companyName="The JAMMs",
                         new_username="King Boy D",
                         new_password="Rockman Rock",
                         new_email="icecreamvan@mumu.org",
                         waddle="frob")

        # return userId = 1 when registerNewUser called
        self.mockShimMintClient().registerNewUser._mock.setDefaultReturn(1)

        # Call the backend function
        ret = raapluginstest.backendCaller(self.rbasetupsrv.updateRBAConfig,
                newValues)

        # Make sure return is OK
        self.failUnlessEqual(ret, True,
                "Expected return of True from backend call")

        # Make sure we regsitered a new user and promoted it
        self.mockShimMintClient().registerNewUser._mock.assertCalled(
                newValues['new_username'], newValues['new_password'],
                "Administrator", newValues['new_email'], "", "", active=True)
        self.mockShimMintClient().promoteUserToAdmin._mock.assertCalled(1)

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
            try:
                self.assertEqual(newCfg[k], newValues[k])
            except KeyError:
                # ignore things that aren't in either list
                pass

        # And now, let's use the backend to get the config, too
        isConfigured, configurableOptions = \
                raapluginstest.backendCaller(self.rbasetupsrv.getRBAConfiguration)

        # We should be configured now
        self.failUnless(isConfigured,
                "We should be configured now (backend call missed it)")

        # Final check
        for k in newValues:
            try:
                self.assertEqual(configurableOptions[k], newValues[k])
            except KeyError:
                # ignore things that aren't in either list
                pass

    def test_srv_RestartApache(self):
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

    def test_srv_setupRMakeChildSuccess(self):
        """
        Exercises the setup and restart rMake code, and assumes everything
        worked. (Success case)
        """
        # Write a new generated config
        f = open(config.RBUILDER_GENERATED_CONFIG, 'w')
        f.write(FAKE_GENERATED_CONFIG)
        f.close()

        # Mock out _writeRmakeConfig, also
        mock_writeRmakeConfig = mock.MockObject()
        self.mock(rmake_setup, '_writeRmakeConfig', mock_writeRmakeConfig)

        # and the helperfuncs.genPassword to return something we know
        fakeGeneratedPassword = 'lasttraintotranscentral'
        mockGenPassword = mock.MockObject()
        self.mock(helperfuncs, 'genPassword', mockGenPassword)
        mockGenPassword._mock.setDefaultReturn(fakeGeneratedPassword)

        self.mockShimMintClient().getProjectByHostname._mock.raiseErrorOnAccess(mint_error.ItemNotFound)
        self.mockShimMintClient().newProject._mock.setDefaultReturn(1)

        # Call the darn thing
        ret = raapluginstest.backendCaller(self.rbasetupsrv.setupRMake)

        # Check ourselves out
        mock_writeRmakeConfig._mock.assertCalled(config.RBUILDER_RMAKE_CONFIG,
                'rmake-repository-user', fakeGeneratedPassword,
                'https://justified.mumu.com',
                'rmake-repository.mumu.com',
                'https://justified.mumu.com/repos/rmake-repository')
        self.mockOS_exit._mock.assertCalled(0)


    def test_srv_setupRMakeParentSuccess(self):
        """
        Just like test_srv_RMakeChildSuccess, except we are the parent
        process.
        """

        # Set the mocked stuff to return useful values
        self.mockOSFork._mock.setDefaultReturn(23)
        self.mockOSwaitpid._mock.setDefaultReturn((23, 0))
        self.mockOSSystem._mock.setReturn(0, "/sbin/service rmake restart")
        self.mockOSSystem._mock.setReturn(0, "/sbin/service rmake-node restart")

        # Call the darn thing
        ret = raapluginstest.backendCaller(self.rbasetupsrv.setupRMake)

        # Make sure we restarted rMake!
        self.mockOSSystem._mock.assertCalled('/sbin/service rmake restart')
        self.mockOSSystem._mock.assertCalled('/sbin/service rmake-node restart')




