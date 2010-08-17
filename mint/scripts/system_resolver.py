#!/usr/bin/python
#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#
"""
This script can be used to resolve duplicates in the system inventory
"""

import os
import sys
import logging

from mint import config
from mint.lib import scriptlibrary

class SystemResolver(scriptlibrary.SingletonScript):
    cfgPath = config.RBUILDER_CONFIG
    logFileName = 'system_resolver.log'
    newLogger = True
    
    def run(self):        
        if sys.argv[0].startswith('--xyzzy='):
            self.cfgPath = sys.argv.pop(0).split('=')[1]
            print "Test mode using configuration from %s" % self.cfgPath
            
        quietMode = False
        if "-q" in sys.argv:
            quietMode = True
            
        self.loadConfig(cfgPath=self.cfgPath)
        self.resetLogging(quiet=quietMode, fileLevel=logging.INFO)
    
        # setup django access
        settingsModule = "mint.django_rest.settings"
        if len(sys.argv) > 1 and sys.argv[1] == 'useLocalSettings':
            settingsModule = "mint.django_rest.settings_local"
            os.environ['MINT_LOCAL_DB'] = os.path.realpath("../mint/mint-local.db")
        os.environ['DJANGO_SETTINGS_MODULE'] = settingsModule
        
        from mint.django_rest.rbuilder.inventory import systemdbmgr
        system_manager = systemdbmgr.SystemDBManager()
        system_manager.resolveSystems()

    def usage(self):
        print >> sys.stderr, "Usage: %s [useLocalSettings]" % \
            sys.argv[0]
        sys.stderr.flush()
        sys.exit(1)
