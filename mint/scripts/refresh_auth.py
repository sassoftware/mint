#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

import logging
from mint.config import MintConfig, RBUILDER_CONFIG
from mint.lib.scriptlibrary import SingletonScript
from mint.lib.siteauth import SiteAuthorization


class RefreshAuthScript(SingletonScript):
    logFileName = 'scripts.log'
    cfgPath = RBUILDER_CONFIG

    def action(self):
        cfg = MintConfig()
        cfg.read(self.cfgPath)
        auth = SiteAuthorization(cfg.siteAuthCfgPath)
        auth.update()
