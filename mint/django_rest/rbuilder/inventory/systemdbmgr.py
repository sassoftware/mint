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
        return systemTarget
        
    def setSystemSSLInfo(self, instanceId, sslCert, sslKey):
        systemTarget = models.SystemsTargets.objects.get(targetSystemId=instanceId)
        systemTarget.managedSystemId.sslClientCertificate = sslCert
        systemTarget.managedSystemId.sslClientKey = sslKey
        systemTarget.managedSystemId.save()
        return systemTarget.managedSystemId

    def getSystemSSLInfo(self, instanceId):
        sId = self.getSystemIdForInstanceId(instanceId)
        if not sId:
            return '', ''
        return sId.sslClientCertificate, sId.sslClientKey

    def addSoftwareVersion(self, softwareVersion):
        sv = models.SoftwareVersions(softwareVersion=softwareVersion)
        sv.save()
        return sv

    def getSystemIdForInstanceId(self, instanceId):
        systemTarget = models.SystemsTargets.objects.filter(targetSystemId=instanceId)
        if len(systemTarget) == 1:
            return systemTarget[0].managedSystemId
        else:
            return None

    def setSoftwareVersionsForInstanceId(self, instanceId, softwareVersions):
        sId = self.getSystemIdForInstanceId(instanceId)
        if not sId:
            return 
        svId = self.addSoftwareVersion(softwareVersions)
        systemSoftwareVersion = models.SystemsSoftwareVersions(
                                    managedSystemId=sId,
                                    softwareVersionId=svId)
        systemSoftwareVersion.save()

    def getSoftwareVersionsForInstanceId(self, instanceId):
        sId = self.getSystemIdForInstanceId(instanceId)
        if not sId:
            return 
        systemsSoftwareVersions = \
            models.SystemsSoftwareVersions.objects.filter(managedSystemId=sId)
        return systemsSoftwareVersions[0].softwareVersionId.softwareVersion
