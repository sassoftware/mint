#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import logging
import time

from mint import mint_error
from mint.django_rest.rbuilder.inventory import models

log = logging.getLogger(__name__)

class RbuilderDjangoManager(object):
    def __init__(self, cfg):
        self.cfg = cfg

class SystemManager(RbuilderDjangoManager):

    def addSystem(self, targetSystemId, cloudName, cloudType):
        import epdb; epdb.serve()  
        targetId = self.db.targetMgr.getTargetId(cloudType, cloudName)
        managedSystemId = self.db.db.managedSystems.new(created=time.time())
        return self.db.db.systemsTargets.new(managedSystemId=managedSystemId,
                targetId=targetId, targetSystemId=targetSystemId)
