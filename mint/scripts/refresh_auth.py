#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

import logging
import os
from conary import conarycfg
from mint.config import MintConfig, RBUILDER_CONFIG
from mint.lib.scriptlibrary import SingletonScript
from mint.lib.siteauth import SiteAuthorization


class RefreshAuthScript(SingletonScript):
    logFileName = 'scripts.log'
    cfgPath = RBUILDER_CONFIG

    def __init__(self):
        self.cfg = MintConfig()
        self.cfg.read(self.cfgPath)
        self.conaryCfg = conarycfg.ConaryConfiguration(True)
        self.logPath = os.path.join(self.cfg.logPath, self.logFileName)
        SingletonScript.__init__(self)

    def action(self):
        auth = SiteAuthorization(self.cfg.siteAuthCfgPath, self.conaryCfg)
        auth.update()
