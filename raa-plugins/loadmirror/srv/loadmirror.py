#
# Copyright (C) 2006, rPath, Inc.
# All rights reserved.
#

from raa.modules.raasrvplugin import rAASrvPlugin
from mint import loadmirror

class LoadMirror(rAASrvPlugin):
    def doTask(self, schedId, execId):
        cmd = self.server.getCommand(schedId)

        if cmd == "mount":
            loadmirror.mountMirrorLoadDrive()
        return True
