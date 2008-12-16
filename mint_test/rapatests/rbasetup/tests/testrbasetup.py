#
# Copyright (C) 2006-2008 rPath, Inc.
# All rights reserved.
#

import os
import raapluginstest
import raatest
import raa.web
import tempfile

from raa.modules.raasrvplugin import rAASrvPlugin
from raa.lib import command
from raa.rpath_error import RestartWebException
from raaplugins.rbasetup.srv import rbasetup as rbasetup_srv

from mint import config

MINT_CONFIG_ROOT = """
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

# Default action that occurs when something is committed to a Conary
# repository
commitAction    /usr/lib/python2.4/site-packages/conary/commitaction --repmap='%(repMap)s' --build-label=%(buildLabel)s \
   --username=%(authUser)s --password=%(authPass)s \
   --module='/usr/lib/python2.4/site-packages/mint/rbuilderaction.py --user=%%(user)s --url=http://127.0.0.1/xmlrpc-private/'
commitActionEmail \
    --module='/usr/lib/python2.4/site-packages/conary/changemail.py --user=%%(user)s --from=%(commitFromEmail)s --email=%(commitEmail)s'

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
        self.oldinit = rbasetup_srv.rBASetup.__init__
        rbasetup_srv.rBASetup.__init__ = lambda *args: None
        self.rbasetup = rbasetup_srv.rBASetup()

        self.rootConfig = self._createTempfile()
        self.generatedConfig = self._createTempfile()

        # Write out our test root config
        f = open(self.rootConfig, 'w')
        f.write(MINT_CONFIG_ROOT % {'testGeneratedFile': self.generatedConfig}
        f.close()

        # Write out our test generated config
        f = open(self.generatedConfig, 'w')
        f.write("# This file is blank and waiting to be filled in")
        f.close()

        raaFramework = raapluginstest.webPluginTest()
        raaFramework.pseudoroot = raa.web.getWebRoot().rbasetup
        self.rbasetupweb = raa.web.getWebRoot().rbasetup
        self.root = raaFramework.pseudoroot
        self.rbasetupweb.server = self.rbasetupweb

        raatest.rAATest.setUp(self)

    def tearDown(self):
        rbasetup_srv.rBASetup.__init__ = self.oldinit

        # Cleanup our configuration files
        self._removeFile(self.rootConfig)
        self._removeFile(self.generatedConfig)

        raatest.rAATest.tearDown(self)

    def testIndex(self):
        # TODO: write web tests here
        pass

    def testGetConfig(self):
        # TODO: write service backend tests
        pass
