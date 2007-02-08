#
# Copyright (C) 2006, rPath, Inc.
# All rights reserved.
#

from raa.modules.raasrvplugin import rAASrvPlugin
import os


class InboundMirror(rAASrvPlugin):
    MIRROR_INBOUND_CMD = 'sudo -u apache /usr/share/rbuilder/scripts/mirror-inbound http://mintauth:mintpass@localhost/xmlrpc-private/'

    def doTask(self, schedId, execId):
        os.system(self.MIRROR_INBOUND_CMD)
