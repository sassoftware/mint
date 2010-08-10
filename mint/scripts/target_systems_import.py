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
from catalogService import storage
from catalogService.rest.database import RestDatabase
from mint.lib import scriptlibrary

from mint import users
from mint.rest.db import authmgr

#from catalogService import handler
#from catalogService.rest.api.clouds import CloudTypeController, SUPPORTED_MODULES

class TargetSystemsImport(scriptlibrary.SingletonScript):
    cfgPath = config.RBUILDER_CONFIG
    logFileName = 'target_systems_import.log'
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
        
        db = database.Database(self.cfg)
        authToken = (self.cfg.authUser, self.cfg.authPass)
        mintAdminGroupId = db.userGroups.getMintAdminId()
        cu = db.cursor()
        cu.execute("SELECT MIN(userId) from userGroupMembers "
                   "WHERE userGroupId = ?", mintAdminGroupId)
        ret = cu.fetchall()
        userId = ret[0][0]
        mintAuth = users.Authorization(
                username=self.cfg.authUser, 
                token=authToken,
                admin=True,
                userId=userId)
        auth = authmgr.AuthenticationManager(self.cfg, db)
        auth.setAuth(mintAuth, authToken)
        restdb = RestDatabase(self.cfg, db)
        
        # do i need these?
        #db.auth = auth
        
        restdb.auth.userId = userId
        
        targetDrivers = self.loadTargetDrivers(restdb)
        for targetType, driver in targetDrivers:
            print "Processing target %s" % targetType
            print driver.getUserCredentials()
        #from mint.django_rest.rbuilder.inventory import systemdbmgr
        #system_manager = systemdbmgr.SystemDBManager()
        #system_manager.importTargetSystems()
        
    def loadTargetDrivers(self, restdb):
        storagePath = os.path.join(restdb.cfg.dataPath, 'catalog')
        storageConfig = storage.StorageConfig(storagePath=storagePath)
        drivers = []
        for driverName in [ 'ec2', 'vmware', 'vws', 'xenent' ]:
            driverClass = __import__('catalogService.rest.drivers.%s' % (driverName),
                                      {}, {}, ['driver']).driver
            driver = driverClass(storageConfig, driverName, db = restdb, userId="admin")
            drivers.append((driverClass.cloudType, driver))
        return drivers
        
    def usage(self):
        print >> sys.stderr, "Usage: %s [useLocalSettings]" % \
            sys.argv[0]
        sys.stderr.flush()
        sys.exit(1)