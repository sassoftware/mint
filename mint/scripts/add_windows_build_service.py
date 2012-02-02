#!/usr/bin/python
#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#
"""
This script can be used to add a new windows build service
"""

import os
import sys
import logging

from mint import config
from mint.lib import scriptlibrary

class Script(scriptlibrary.SingletonScript):
    cfgPath = config.RBUILDER_CONFIG
    logFileName = 'add_windows_build_service.log'
    newLogger = True
    
    def action(self):
        if sys.argv[0].startswith('--xyzzy='):
            self.cfgPath = sys.argv.pop(0).split('=')[1]
            print "Test mode using configuration from %s" % self.cfgPath
                        
        self.loadConfig(cfgPath=self.cfgPath)
        self.resetLogging(fileLevel=logging.INFO)
        
        name = None
        description = None
        network_address = None
        if len(sys.argv) < 4:
            self.usage()
        else:
            name = sys.argv[1]
            description = sys.argv[2]
            network_address = sys.argv[3]
                
        settingsModule = "mint.django_rest.settings"
        if len(sys.argv) > 4 and sys.argv[4] == 'useLocalSettings':
            settingsModule = "mint.django_rest.settings_local"
            os.environ['MINT_LOCAL_DB'] = os.path.realpath("../mint/mint-local.db")

        os.environ['DJANGO_SETTINGS_MODULE'] = settingsModule

        from mint.django_rest.rbuilder.inventory import manager
        mgr = manager.Manager()
        mgr.addWindowsBuildService(name, description, network_address)
        return 0

    def usage(self):
        print >> sys.stderr, "Usage: %s <name> <description> <network address> [useLocalSettings]" % \
            sys.argv[0]
        sys.stderr.flush()
        sys.exit(1)
