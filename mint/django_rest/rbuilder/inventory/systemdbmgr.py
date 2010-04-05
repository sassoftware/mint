#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import datetime
import logging
import time

from mint import mint_error
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import models

log = logging.getLogger(__name__)

class RbuilderDjangoManager(object):
    def __init__(self, cfg):
        self.cfg = cfg

class SystemDBManager(RbuilderDjangoManager):

    def getSystems(self):
        return models.ManagedSystems.objects.all()

    def launchSystem(self, instanceId, targetType, targetName):
        managedSystem = models.ManagedSystems(
            registrationDate=datetime.datetime.now())
        managedSystem.save()
        target = rbuildermodels.Targets.objects.get(targettype=targetType,
            targetname=targetName)
        systemTarget = models.SystemsTargets(managedSystemId=managedSystem,
            targetId=target, targetSystemId=instanceId)
        systemTarget.save()
        
    def setSystemSSLInfo(self, instanceId, sslCert, sslKey):
        systemTarget = models.SystemsTargets.objects.get(targetSystemId=instanceId)
        systemTarget.managedSystemId.sslClientCertificate = sslCert
        systemTarget.managedSystemId.sslClientKey = sslKey
        systemTarget.managedSystemId.save()
