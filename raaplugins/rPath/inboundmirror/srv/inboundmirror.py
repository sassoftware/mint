#
# Copyright (C) 2006,-2007 rPath, Inc.
# All rights reserved.
#

import os

from mint import config

from raa.modules.raasrvplugin import rAASrvPlugin

class InboundMirror(rAASrvPlugin):

    def doTask(self, schedId, execId):
        mc = config.MintConfig()
        mc.read(config.RBUILDER_CONFIG)
        mintauth = mc.authUser
        mintpass = mc.authPass
        MIRROR_INBOUND_CMD = 'sudo -u apache bash -c "/usr/share/rbuilder/scripts/mirror-inbound http://%s:%s@localhost/xmlrpc-private/ 2>> /var/log/rbuilder/mirror-inbound.log"' % (mintauth, mintpass)
        os.system(MIRROR_INBOUND_CMD)

