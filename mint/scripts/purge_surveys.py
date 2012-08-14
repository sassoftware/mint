#!/usr/bin/python
#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

import logging
import sys

from mint import config
from mint.lib import scriptlibrary
from mint.django_rest.rbuilder.manager import rbuildermanager

class Script(scriptlibrary.SingletonScript):
    cfgPath = config.RBUILDER_CONFIG
    logFileName = 'scripts.log'
    newLogger = True

    def action(self):
        if sys.argv[0].startswith('--xyzzy='):
            self.cfgPath = sys.argv.pop(0).split('=')[1]
            print "Test mode using configuration from %s" % self.cfgPath

        self.loadConfig(cfgPath=self.cfgPath)
        self.resetLogging(fileLevel=logging.INFO)
        mgr = rbuildermanager.RbuilderManager()
        mgr.deleteRemovableSurveys(olderThanDays=self.cfg.surveyMaxAge)
        return 0

    def usage(self):
        print >> sys.stderr, "Usage: %s [older_than_days]" % \
            sys.argv[0]
        sys.stderr.flush()
        sys.exit(1)

if __name__ == "__main__":
    s = Script()
    s.run()

