#
# Copyright (C) 2006, rPath, Inc.
# All rights reserved.
#

from raa.modules.raasrvplugin import rAASrvPlugin
import os


class InboundMirror(rAASrvPlugin):
    MIRROR_INBOUND_CMD = 'sudo -u apache bash -c "/usr/share/rbuilder/scripts/mirror-inbound http://mintauth:mintpass@localhost/xmlrpc-private/ 2>> /srv/rbuilder/logs/mirror-inbound.log"'

    def doTask(self, schedId, execId):
        os.system(self.MIRROR_INBOUND_CMD)
