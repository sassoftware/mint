#!/usr/bin/python
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


"""
This script can be used to check for and handle current system inventory events
"""

import os
import sys
import logging

from mint import config
from mint.lib import scriptlibrary

class Script(scriptlibrary.SingletonScript):
    cfgPath = config.RBUILDER_CONFIG
    logFileName = 'system_events.log'
    newLogger = True
    
    def action(self):
        if sys.argv[0].startswith('--xyzzy='):
            self.cfgPath = sys.argv.pop(0).split('=')[1]
            print "Test mode using configuration from %s" % self.cfgPath
            
        quietMode = False
        if "-q" in sys.argv:
            quietMode = True
            
        self.loadConfig(cfgPath=self.cfgPath)
        self.resetLogging(quiet=quietMode, fileLevel=logging.INFO)
    
        settingsModule = "mint.django_rest.settings"
        if len(sys.argv) > 1 and sys.argv[1] == 'useLocalSettings':
            settingsModule = "mint.django_rest.settings_local"
            os.environ['MINT_LOCAL_DB'] = os.path.realpath("../mint/mint-local.db")

        os.environ['DJANGO_SETTINGS_MODULE'] = settingsModule

        from mint.django_rest.rbuilder.manager import rbuildermanager
        mgr = rbuildermanager.RbuilderManager()
        mgr.enterTransactionManagement()
        mgr.processSystemEvents()
        mgr.commit()
        return 0

    def usage(self):
        print >> sys.stderr, "Usage: %s [useLocalSettings]" % \
            sys.argv[0]
        sys.stderr.flush()
        sys.exit(1)
