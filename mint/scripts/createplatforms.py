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
from mint.lib import scriptlibrary

from mint.rest.db.database import Database as RestDatabase
from mint.rest.api.models.platforms import Platform
from mint.rest.modellib import converter

#from catalogService import handler
#from catalogService.rest.api.clouds import CloudTypeController, SUPPORTED_MODULES

class Script(scriptlibrary.SingletonScript):
    cfgPath = config.RBUILDER_CONFIG
    logFileName = 'platforms.log'
    newLogger = True
    
    PLATFORM_DIR = "/usr/share/rbuilder/platforms"
    def action(self):
        if sys.argv[0].startswith('--xyzzy='):
            self.cfgPath = sys.argv.pop(0).split('=')[1]
            print "Test mode using configuration from %s" % self.cfgPath
            
        quietMode = False
        if "-q" in sys.argv:
            quietMode = True

        self.loadConfig(cfgPath=self.cfgPath)
        self.resetLogging(quiet=quietMode, fileLevel=logging.INFO)

        db = database.Database(self.cfg)
        self.restdb = RestDatabase(self.cfg, db)

        self.createPlatforms()
        return 0

    def createPlatforms(self):
        onDiskPlatforms = set()
        for platformFile in self.listPlatforms():
            platformModel = self.loadPlatform(platformFile)
            self.restdb.createPlatform(platformModel, createPlatDef=False)
            onDiskPlatforms.add(platformModel.label)
        # Fetch all on-disk platforms from the db
        cu = self.restdb.db.cursor()
        cu.execute("select label from Platforms where isFromDisk=true")
        inDb = set(x[0] for x in cu)
        sql = "delete from Platforms where label = ?"
        for label in inDb - onDiskPlatforms:
            cu.execute(sql, (label, ))

    @classmethod
    def listPlatforms(cls):
        for fname in sorted(os.listdir(cls.PLATFORM_DIR)):
            if not fname.endswith('.xml'):
                continue
            fpath = os.path.join(cls.PLATFORM_DIR, fname)
            yield fpath

    def loadPlatform(self, fpath):
        contents = file(fpath).read()
        model = converter.fromText('xml', contents, Platform, None, None)
        model.isFromDisk = True
        return model

    def usage(self):
        print >> sys.stderr, "Usage: %s [useLocalSettings]" % \
            sys.argv[0]
        sys.stderr.flush()
        sys.exit(1)

if __name__ == '__main__':
    sys.exit(Script().run())
