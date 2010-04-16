#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import datetime
import logging
import time

from django.db import connection, transaction

from mint import mint_error
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import models

log = logging.getLogger(__name__)

class RbuilderDjangoManager(object):
    def __init__(self, cfg, userName):
        self.cfg = cfg
        if userName is None:
            self.user = None
        else:
            # The salt field contains binary data that blows django's little
            # mind when it tries to decode it as UTF-8. Since we don't need it
            # here, defer the loading of that column
            self.user = rbuildermodels.Users.objects.defer("salt").get(username = userName)

class SystemDBManager(RbuilderDjangoManager):

    def getSystems(self):
        return models.managed_systems.objects.all()

    def launchSystem(self, instanceId, targetType, targetName):
        managedSystem = models.managed_system(
            registration_date=datetime.datetime.now(),
            launching_user = self.user)
        managedSystem.save()
        target = rbuildermodels.Targets.objects.get(targettype=targetType,
            targetname=targetName)
        systemTarget = models.system_target(managed_system=managedSystem,
            target=target, target_system_id=instanceId)
        systemTarget.save()
        return systemTarget
        
    def setSystemSSLInfo(self, instanceId, sslCert, sslKey):
        systemTarget = models.system_target.objects.get(target_system_id=instanceId)
        systemTarget.managed_system.ssl_client_certificate = sslCert
        systemTarget.managed_system.ssl_client_key = sslKey
        systemTarget.managed_system.save()
        return systemTarget.managed_system

    def getSystemSSLInfo(self, instanceId):
        managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            return '', ''
        if not self.isManageable(managedSystem):
            return '', ''
        return managedSystem.ssl_client_certificate, managedSystem.ssl_client_key

    def isManageable(self, managedSystem):
        if managedSystem.launching_user.userid == self.user.userid:
            # If we own the system, we can manage
            return True
        # Does the user who launched the system have the same credentials as
        # our current user?
        cu = connection.cursor()
        cu.execute("""
            SELECT 1
              FROM TargetUserCredentials tc1
              JOIN TargetUserCredentials tc2 USING (credentials)
             WHERE tc1.userId = %s
               AND tc2.userId = %s
         """, [ self.user.userid, managedSystem.launching_user.userid ])
        row = cu.fetchone()
        return bool(row)

    def addSoftwareVersion(self, softwareVersion):
        name, version, flavor = softwareVersion
        version = version.freeze()
        flavor = str(flavor)
        softwareVersion, created = models.software_version.objects.get_or_create(name=name,
                                        version=version, flavor=flavor)
        return softwareVersion

    def getManagedSystemForInstanceId(self, instanceId):
        systemTarget = models.system_target.objects.filter(target_system_id=instanceId)
        if len(systemTarget) == 1:
            return systemTarget[0].managed_system
        else:
            return None

    def setSoftwareVersionForInstanceId(self, instanceId, softwareVersion):
        managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            return 

        models.system_software_version.objects.filter(managed_system=managedSystem).delete()

        for version in softwareVersion:
            softwareVersion = self.addSoftwareVersion(version)

            systemSoftwareVersion = models.system_software_version(
                                        managed_system=managedSystem,
                                        software_version=softwareVersion)
            systemSoftwareVersion.save()

    def getSoftwareVersionsForInstanceId(self, instanceId):
        managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            return None
        systemSoftwareVersion = \
            models.system_software_version.objects.filter(managed_system=managedSystem)

        versions = []
        for version in systemSoftwareVersion:
            versions.append('%s=%s[%s]' % (
                version.software_version.name, version.software_version.version,
                version.software_version.flavor))

        if versions:
            return '\n'.join(versions)
        return None

    def deleteSoftwareVersionsForInstanceId(self, instanceId):
        managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            return 
        models.system_software_version.objects.filter(managed_system=managedSystem).delete()
