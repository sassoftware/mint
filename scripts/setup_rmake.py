#!/usr/bin/python
#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#

from mint import config
from mint import scriptlibrary
from mint import rmake_setup
import os

class CreateRmakeProject(scriptlibrary.SingletonScript):
    cfgPath = config.RBUILDER_CONFIG
    rmakeCfgPath = config.RBUILDER_RMAKE_CONFIG

    def action(self):
        try:
            cfg = config.getConfig(self.cfgPath)
            rmake_setup.setupRmake(cfg, self.rmakeCfgPath)
        except Exception, e:
            try:
                print e
            except:
                pass
            os._exit(1)
        else:
            os._exit(0)

if __name__ == "__main__":
    create = CreateRmakeProject()
    os._exit(create.run())

