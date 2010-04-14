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
        return models.ManagedSystems.objects.all()

    def launchSystem(self, instanceId, targetType, targetName):
        managedSystem = models.ManagedSystem(
            registrationDate=datetime.datetime.now(),
            launchingUser = self.user.userid)
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
        if not self.isManageable(managedSystem):
            return '', ''
        return managedSystem.sslClientCertificate, managedSystem.sslClientKey

    def isManageable(self, managedSystem):
        if managedSystem.launchingUser.userid == self.user.userid:
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
         """, [ self.user.userid, managedSystem.launchingUser.userid ])
        row = cu.fetchone()
        return bool(row)

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
            return None
        systemSoftwareVersion = \
            models.SystemSoftwareVersion.objects.filter(managedSystem=managedSystem)

        versions = []
        for version in systemSoftwareVersion:
            versions.append('%s=%s[%s]' % (
                version.softwareVersion.name, version.softwareVersion.version,
                version.softwareVersion.flavor))

        if versions:
            return '\n'.join(versions)
        return None

    def deleteSoftwareVersionsForInstanceId(self, instanceId):
        managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            return 
        models.SystemSoftwareVersion.objects.filter(managedSystem=managedSystem).delete()
