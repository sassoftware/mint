#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from mint import mint_error
from mint.rest.db import manager

log = logging.getLogger(__name__)

class SystemManager(manager.Manager):

    def addSystem(self, targetSystemId, targetId):
        return self.db.db.systems.new(targetSystemId, targetId)
