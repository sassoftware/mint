#
# Copyright (C) 2006, rPath, Inc.
# All rights reserved.
#

from raa.modules.raasrvplugin import rAASrvPlugin
import os


class OutboundMirror(rAASrvPlugin):
    MIRROR_OUTBOUND_CMD = 'sudo -u apache bash -c "/usr/share/rbuilder/scripts/mirror-outbound http://mintauth:mintpass@localhost/xmlrpc-private/ 2>> /srv/rbuilder/logs/mirror-outbound.log"'

    def doTask(self, schedId, execId):
        os.system(self.MIRROR_OUTBOUND_CMD)
