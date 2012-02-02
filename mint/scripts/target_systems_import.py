#!/usr/bin/python
#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#
"""
This script can be used to import running systems from predefined targets
"""

import os
import sys
import logging

from mint.db import database

from mint import config
from catalogService.rest.database import RestDatabase
from mint.lib import scriptlibrary

from mint.django_rest.rbuilder.manager import rbuildermanager

from mint import users
from mint.rest.db import authmgr

class Script(scriptlibrary.SingletonScript):
    cfgPath = config.RBUILDER_CONFIG
    logFileName = 'target_systems_import.log'
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
    
        #############################################################
        # setup django access

        settingsModule = "mint.django_rest.settings"
        if len(sys.argv) > 1 and sys.argv[1] == 'useLocalSettings':
            settingsModule = "mint.django_rest.settings_local"
            os.environ['MINT_LOCAL_DB'] = os.path.realpath("../mint/mint-local.db")
        os.environ['DJANGO_SETTINGS_MODULE'] = settingsModule
        
        db = database.Database(self.cfg)
        authToken = (self.cfg.authUser, self.cfg.authPass)
        cu = db.cursor()
        cu.execute("SELECT MIN(userId) FROM Users WHERE is_admin = true")
        ret = cu.fetchall()
        userId = ret[0][0]
        mintAuth = users.Authorization(
                username=self.cfg.authUser, 
                token=authToken,
                admin=True,
                userId=userId,
                authorized=True)
        auth = authmgr.AuthenticationManager(self.cfg, db)
        auth.setAuth(mintAuth, authToken)
        restdb = RestDatabase(self.cfg, db)
        
        # do i need these?
        restdb.auth.userId = userId
        restdb.auth.setAuth(mintAuth, authToken)

        mgr = rbuildermanager.RbuilderManager()
        mgr.enterTransactionManagement()
        mgr.importTargetSystems()
        mgr.commit()
        return 0

    def usage(self):
        print >> sys.stderr, "Usage: %s [useLocalSettings]" % \
            sys.argv[0]
        sys.stderr.flush()
        sys.exit(1)

if __name__ == "__main__":
    s = Script()
    s.run()

