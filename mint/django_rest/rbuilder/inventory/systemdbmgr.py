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
            registration_date=datetime.datetime.now())
        managedSystem.save()
        target = rbuildermodels.Targets.objects.get(targettype=targetType,
            targetname=targetName)
        systemTarget = models.SystemTarget(managed_system=managedSystem,
            target=target, target_system_id=instanceId)
        systemTarget.save()
        return systemTarget
        
    def setSystemSSLInfo(self, instanceId, sslCert, sslKey):
        systemTarget = models.SystemTarget.objects.get(target_system_id=instanceId)
        systemTarget.managed_system.ssl_client_certificate = sslCert
        systemTarget.managed_system.ssl_client_key = sslKey
        systemTarget.managed_system.save()
        return systemTarget.managed_system

    def getSystemSSLInfo(self, instanceId):
        managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            return '', ''
        return managedSystem.ssl_client_certificate, managedSystem.ssl_client_key

    def addSoftwareVersion(self, softwareVersion):
        name, version, flavor = softwareVersion
        version = version.freeze()
        flavor = str(flavor)
        softwareVersion, created = models.SoftwareVersion.objects.get_or_create(name=name,
                                        version=version, flavor=flavor)
        return softwareVersion

    def getManagedSystemForInstanceId(self, instanceId):
        systemTarget = models.SystemTarget.objects.filter(target_system_id=instanceId)
        if len(systemTarget) == 1:
            return systemTarget[0].managed_system
        else:
            return None

    def setSoftwareVersionForInstanceId(self, instanceId, softwareVersion):
        managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            return 

        models.SystemSoftwareVersion.objects.filter(managed_system=managedSystem).delete()

        for version in softwareVersion:
            softwareVersion = self.addSoftwareVersion(version)

            systemSoftwareVersion = models.SystemSoftwareVersion(
                                        managed_system=managedSystem,
                                        software_version=softwareVersion)
            systemSoftwareVersion.save()

    def getSoftwareVersionsForInstanceId(self, instanceId):
        managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            return 
        systemSoftwareVersion = \
            models.SystemSoftwareVersion.objects.filter(managed_system=managedSystem)

        versions = []
        for version in systemSoftwareVersion:
            versions.append('%s=%s[%s]' % (
                version.software_version.name, version.software_version.version,
                version.software_version.flavor))

        if versions:
            return '\n'.join(versions)
        else:
            return versions

    def deleteSoftwareVersionsForInstanceId(self, instanceId):
        managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            return 
        models.SystemSoftwareVersion.objects.filter(managed_system=managedSystem).delete()
