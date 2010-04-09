#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import datetime
import logging
import time

from django.db import transaction

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
        name, version, flavor = softwareVersion
        version = version.freeze()
        flavor = str(flavor)
        softwareVersion, created = models.SoftwareVersion.objects.get_or_create(name=name,
                                        version=version, flavor=flavor)
        return softwareVersion

    def getManagedSystemForInstanceId(self, instanceId):
        systemTarget = models.SystemTarget.objects.filter(targetSystemId=instanceId)
        if len(systemTarget) == 1:
            return systemTarget[0].managedSystem
        else:
            return None

    def setSoftwareVersionForInstanceId(self, instanceId, softwareVersion):
        managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            return 

        models.SystemSoftwareVersion.objects.filter(managedSystem=managedSystem).delete()

        for version in softwareVersion:
            softwareVersion = self.addSoftwareVersion(version)

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

        versions = []
        for version in systemSoftwareVersion:
            versions.append('%s=%s[%s]' % (
                version.softwareVersion.name, version.softwareVersion.version,
                version.softwareVersion.flavor))

        if versions:
            return '\n'.join(versions)
        else:
            return versions

    def deleteSoftwareVersionsForInstanceId(self, instanceId):
        managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            return 
        models.SystemSoftwareVersion.objects.filter(managedSystem=managedSystem).delete()
