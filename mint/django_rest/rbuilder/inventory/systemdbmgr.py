#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import copy
import datetime
import os
import time

from django.db import connection

from conary import versions
from conary.deps import deps

from mint.django_rest.rbuilder import inventory
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import models

from rpath_storage import api1 as storage

class RbuilderDjangoManager(object):
    def __init__(self, cfg=None, userName=None):
        self.cfg = cfg
        if userName is None:
            self.user = None
        else:
            # The salt field contains binary data that blows django's little
            # mind when it tries to decode it as UTF-8. Since we don't need it
            # here, defer the loading of that column
            self.user = rbuildermodels.Users.objects.defer("salt").get(username = userName)

class SystemDBManager(RbuilderDjangoManager):

    def __init__(self, *args, **kw):
        RbuilderDjangoManager.__init__(self, *args, **kw)
        self.systemStore = self.getSystemStore()

    def getSystemStore(self):
        if self.cfg is None:
            storagePath = '/tmp/storage'
        else:
            storagePath = self.cfg.dataPath
        path = os.path.join(os.path.join(storagePath, 'catalog'), 'systems')
        cfg = storage.StorageConfig(storagePath=path)
        dstore = storage.DiskStorage(cfg)
        return dstore

    def getSystem(self, system):
        return models.managed_system.objects.get(pk=system)

    def getSystems(self):
        systems = models.managed_system.objects.all()
        for system in systems:
            system.populateRelatedModelsFromDb()
        return systems

    def _sanitizeSystem(self, system):
        systemCopy = copy.deepcopy(system)
        key = os.path.join(systemCopy.generated_uuid, 'x509key')
        keyPath = self.systemStore.set(key, systemCopy.ssl_client_key)
        systemCopy.ssl_client_key = keyPath
        cert = os.path.join(systemCopy.generated_uuid, 'x509cert')
        certPath = self.systemStore.set(cert, systemCopy.ssl_client_certificate)
        systemCopy.ssl_client_certificate = certPath

        return systemCopy

    def activateSystem(self, system):
        sanitizedSystem = self._sanitizeSystem(system)
        managedSystem = models.managed_system.loadFromDb(sanitizedSystem)

        matchedIps = []
        if managedSystem:
            matchedIps = [n.ip_address for n in \
                          managedSystem.network_information_set.all() \
                          if n.ip_address == sanitizedSystem.ip_address]

        if matchedIps:
            # TODO: update, log activation
            pass
        else:
            # New activation, need to create a new managedSystem
            managedSystem = models.managed_system.factoryParser(sanitizedSystem)
            
        managedSystem.activation_date = datetime.datetime.now()
        managedSystem.save()
        managedSystem.populateRelatedModelsFromParser(sanitizedSystem)
        managedSystem.saveAll()

        return managedSystem

    def launchSystem(self, system):
        managedSystem = models.managed_system.factoryParser(system)
        managedSystem.launching_user = self.user
        managedSystem.launch_date = datetime.datetime.now()
        managedSystem.save()
        target = rbuildermodels.Targets.objects.get(
                    targettype=system.target_type,
                    targetname=system.target_name)
        systemTarget = models.system_target(managed_system=managedSystem,
            target=target, target_system_id=system.target_system_id)
        systemTarget.save()
        return systemTarget
        
    def updateSystem(self, system):
        systemTarget = models.system_target.objects.get(
                        target_system_id=system.target_system_id)
        systemTarget.managed_system.updateFromParser(system)
        systemTarget.managed_system.save()
        return systemTarget.managed_system

    def matchSystem(self, system):
        matchingIPs = models.network_information.objects.filter(
                        ip_address=system.ip_address)
        for matchingIP in matchingIPs:
            sslCert = open(matchingIP.managed_system.ssl_client_certificate).read()
            if sslCert == system.ssl_client_certificate:
                return matchingIP.managed_system

        return None

    def getSystemByInstanceId(self, instanceId):
        managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            return models.System()
        managedSystemObj = managedSystem.getParser()
        if not self.isManageable(managedSystem):
            managedSystemObj.ssl_client_certificate = None
            managedSystemObj.ssl_client_key = None
            managedSystemObj.set_is_manageable(False)
        else:
            isManageable = (managedSystem.ssl_client_certificate is not None
                and managedSystem.ssl_client_key is not None
                and os.path.exists(managedSystem.ssl_client_certificate)
                and os.path.exists(managedSystem.ssl_client_key))
            managedSystemObj.set_is_manageable(isManageable)
        
        return managedSystemObj

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
              JOIN TargetUserCredentials tc2 USING (targetId, credentials)
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
            st = systemTarget[0]
            if st.target_id is None:
                # System was disassociated from target, probably target got
                # removed
                return None
            return st.managed_system
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

    def getCachedUpdates(self, nvf):
        softwareVersion, created = models.software_version.objects.get_or_create(
            name=nvf[0], version=nvf[1], flavor=nvf[2])

        # If it was just created, obviously there's nothing cached.
        if created:
            return None

        updates = models.software_version_update.objects.filter(
                    software_version=softwareVersion)

        now = datetime.datetime.now()
        oneDay = datetime.timedelta(1)

        # RBL-6007 last_refresh should not be None here as there's a not null
        # constraint, but still check just in case.
        cachedUpdates = [u for u in updates \
                         if (u.last_refreshed is not None) and \
                            (now - u.last_refreshed < oneDay)]

        if not cachedUpdates:
            return None

        updatesAvailable = [c for c in cachedUpdates if c.available_update is not None]
        if updatesAvailable:
           updatesAvailable  = [(str(s.available_update.name),
                              versions.ThawVersion(s.available_update.version),
                              deps.parseFlavor(s.available_update.flavor)) for s in updatesAvailable]
        else:
            return []

        return updatesAvailable 
                
    def clearCachedUpdates(self, nvfs):
        for nvf in nvfs:
            name, version, flavor = nvf
            version = version.freeze()
            flavor = str(flavor)
            softwareVersion, created = models.software_version.objects.get_or_create(
                name=name, version=version, flavor=flavor)
            if not created:
                updates = models.software_version_update.objects.filter(
                                software_version=softwareVersion)
                updates.delete()

    def cacheUpdate(self, nvf, updateNvf):
        softwareVersion, created = models.software_version.objects.get_or_create(
            name=nvf[0], version=nvf[1], flavor=nvf[2])
                
        if updateNvf:
            updateSoftwareVersion, created = models.software_version.objects.get_or_create(
                name=updateNvf[0], version=updateNvf[1], flavor=updateNvf[2])
        else:
            updateSoftwareVersion = None

        cachedUpdate, created = models.software_version_update.objects.get_or_create(
                                    software_version=softwareVersion,
                                    available_update=updateSoftwareVersion)
        if not created:
            cachedUpdate.last_refreshed = datetime.datetime.now()
            cachedUpdate.save()
            
