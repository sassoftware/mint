#
# Copyright (C) 2006-2007 rPath, Inc.
# All rights reserved.
#

import os

from mint import config

from raa.modules.raasrvplugin import rAASrvPlugin


class OutboundMirror(rAASrvPlugin):

    def doTask(self, schedId, execId):
        mc = config.MintConfig()
        mc.read(config.RBUILDER_CONFIG)
        mintauth = mc.authUser
        mintpass = mc.authPass
        MIRROR_OUTBOUND_CMD = (
                '/usr/share/rbuilder/scripts/mirror-outbound '
                '"http://%s:%s@localhost/xmlrpc-private/"'
                % (mintauth, mintpass))
        os.system(MIRROR_OUTBOUND_CMD)
