#
# Copyright (C) 2006-2007 rPath, Inc.
# All rights reserved.
#

import os

from mint import config

from raa.modules.raasrvplugin import rAASrvPlugin

class InboundMirror(rAASrvPlugin):

    def doTask(self, schedId, execId):
        os.system('/usr/share/rbuilder/scripts/mirror-inbound')
