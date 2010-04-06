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
        managedSystem = models.ManagedSystem(
            registrationDate=datetime.datetime.now())
        managedSystem.save()
        target = rbuildermodels.Targets.objects.get(targettype=targetType,
            targetname=targetName)
        systemTarget = models.SystemTarget(managedSystem=managedSystem,
            target=target, targetSystemId=instanceId)
        systemTarget.save()
        return systemTarget
        
    def setSystemSSLInfo(self, instanceId, sslCert, sslKey):
        systemTarget = models.SystemTarget.objects.get(targetSystemId=instanceId)
        systemTarget.managedSystem.sslClientCertificate = sslCert
        systemTarget.managedSystem.sslClientKey = sslKey
        systemTarget.managedSystem.save()
        return systemTarget.managedSystem

    def getSystemSSLInfo(self, instanceId):
        managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            return '', ''
        return managedSystem.sslClientCertificate, managedSystem.sslClientKey

    def addSoftwareVersion(self, softwareVersion):
        softwareVersion = models.SoftwareVersion(softwareVersion=softwareVersion)
        softwareVersion.save()
        return softwareVersion

    def getManagedSystemForInstanceId(self, instanceId):
        systemTarget = models.SystemTarget.objects.filter(targetSystemId=instanceId)
        if len(systemTarget) == 1:
            return systemTarget[0].managedSystem
        else:
            return None

    def setSoftwareVersionsForInstanceId(self, instanceId, softwareVersion):
        managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            return 
        softwareVersion = self.addSoftwareVersion(softwareVersion)
        systemSoftwareVersion = models.SystemSoftwareVersion(
                                    managedSystem=managedSystem,
                                    softwareVersion=softwareVersion)
        systemSoftwareVersion.save()

    def getSoftwareVersionsForInstanceId(self, instanceId):
        managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            return 
        systemSoftwareVersion = \
            models.SystemSoftwareVersion.objects.filter(managedSystem=managedSystem)
        if systemSoftwareVersion:
            return systemSoftwareVersion[0].softwareVersion.softwareVersion
        else:
            return None
