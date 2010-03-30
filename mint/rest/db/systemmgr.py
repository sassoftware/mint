#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import logging

from mint import mint_error
from mint.rest.db import manager

log = logging.getLogger(__name__)

class SystemManager(manager.Manager):

    def addSystem(self, targetSystemId, cloudName, cloudType):
        targetId = self.db.targetMgr.getTargetId(cloudType, cloudName)
        return self.db.db.systems.new(targetSystemId=targetSystemId, 
                targetId=targetId)
