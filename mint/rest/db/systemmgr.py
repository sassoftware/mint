#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import logging
import time

from mint import mint_error
from mint.rest.db import manager

log = logging.getLogger(__name__)

class SystemManager(manager.Manager):

    def addSystem(self, targetSystemId, cloudName, cloudType):
        targetId = self.db.targetMgr.getTargetId(cloudType, cloudName)
        managedSystemId = self.db.db.managedSystems.new(created=time.time())
        return self.db.db.systemsTargets.new(managedSystemId=managedSystemId,
                targetId=targetId, targetSystemId=targetSystemId)