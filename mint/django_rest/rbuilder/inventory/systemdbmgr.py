#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import copy
import datetime
import os
import time
import vobject

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
        self._jobStates = None

    @property
    def jobStates(self):
        if self._jobStates is not None:
            return self._jobStates
        return dict((x.name, x) for x in models.job_states.objects.all())

    def getSystemStore(self):
        if self.cfg is None:
            storagePath = '/tmp/storage'
        elif hasattr(self.cfg, 'storagePath'):
            storagePath = self.cfg.storagePath
        else:
            storagePath = os.path.join(self.cfg.dataPath, 'catalog')
        path = os.path.join(storagePath, 'systems')
        cfg = storage.StorageConfig(storagePath=path)
        dstore = storage.DiskStorage(cfg)
        return dstore

    def getSystem(self, system):
        managedSystem = models.managed_system.objects.get(pk=system)
        self.logSystem(managedSystem, "System data fetched.")
        managedSystem.populateRelatedModelsFromDb()
        return self._unSanitizeSystem(managedSystem)

    def deleteSystem(self, system):
        managedSystem = models.managed_system.objects.get(pk=system)
        managedSystem.delete()

    def getSystems(self):
        systems = models.managed_system.objects.all()
        retSystems = []
        for system in systems:
            self.logSystem(system, "System data fetched.")
            system.populateRelatedModelsFromDb()
            retSystems.append(self._unSanitizeSystem(system))
        return retSystems

    def _sanitizeSystem(self, system):
        systemCopy = copy.deepcopy(system)
        if systemCopy.generated_uuid:
            key = os.path.join(systemCopy.generated_uuid, 'x509key')
            keyPath = self.systemStore.set(key, systemCopy.ssl_client_key)
            systemCopy.ssl_client_key = keyPath
            cert = os.path.join(systemCopy.generated_uuid, 'x509cert')
            certPath = self.systemStore.set(cert, systemCopy.ssl_client_certificate)
            systemCopy.ssl_client_certificate = certPath
            serverCert = os.path.join(systemCopy.generated_uuid, 'x509servercert')
            serverCertPath = self.systemStore.set(serverCert, systemCopy.ssl_server_certificate)
            systemCopy.ssl_server_certificate = serverCertPath

        return systemCopy

    def _unSanitizeSystem(self, system):
        systemCopy = copy.deepcopy(system)
        keyPath = systemCopy.ssl_client_key
        key = open(keyPath).read()
        systemCopy.ssl_client_key = key
        certPath = systemCopy.ssl_client_certificate
        cert = open(certPath).read()
        systemCopy.ssl_client_certificate = cert
        if systemCopy.ssl_server_certificate:
            serverCertPath = systemCopy.ssl_server_certificate
            serverCert = open(serverCertPath).read()
            systemCopy.ssl_server_certificate = serverCert

        return systemCopy

    def logSystem(self, managedSystem, logMsg):
        entry, created = models.entry.objects.get_or_create(entry=logMsg) 
        entry.save()
        systemLog = models.system_log_entry(entry=entry,
                        managed_system=managedSystem,
                        entry_date=time.time())
        systemLog.save()

    def activateSystem(self, system):
        sanitizedSystem = self._sanitizeSystem(system)
        managedSystem = models.managed_system.loadFromDb(sanitizedSystem)

        matchedIps = []
        if managedSystem:
            matchedIps = [n.ip_address for n in \
                          managedSystem.system_network_information_set.all() \
                          if n.ip_address == sanitizedSystem.ip_address]

        if matchedIps:
            # TODO: update, log activation
            pass
        else:
            # New activation, need to create a new managedSystem
            managedSystem = models.managed_system.factoryParser(sanitizedSystem)
            
        managedSystem.activation_date = int(time.time())
        managedSystem.scheduled_event_start_date = managedSystem.activation_date
        managedSystem.save()
        managedSystem.populateRelatedModelsFromParser(sanitizedSystem)
        managedSystem.saveAll()
        self.logSystem(managedSystem, models.SYSTEM_ACTIVATED_LOG)
        self.computeScheduledEvents([ sanitizedSystem ])

        return managedSystem

    def launchSystem(self, system):
        managedSystem = models.managed_system.factoryParser(system)
        managedSystem.launching_user = self.user
        managedSystem.launch_date = int(time.time())
        if managedSystem.scheduled_event_start_date is None:
            managedSystem.scheduled_event_start_date = managedSystem.launch_date
        managedSystem.save()
        target = rbuildermodels.Targets.objects.get(
                    targettype=system.target_type,
                    targetname=system.target_name)
        systemTarget = models.system_target(managed_system=managedSystem,
            target=target, target_system_id=system.target_system_id)
        systemTarget.save()
        self.computeScheduledEvents([ system ])
        return systemTarget
        
    def updateSystem(self, system):
        systemTarget = models.system_target.objects.get(
                        target_system_id=system.target_system_id)
        managedSystem = systemTarget.managed_system
        managedSystem.updateFromParser(system)
        managedSystem.save()
        return managedSystem

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

    def getSystemLog(self, system):
        systemLog = models.system_log(managed_system=system)
        systemLog.populateRelatedModelsFromDb(system)
        return systemLog

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

    def computeScheduledEvents(self, systems, daysInAdvance=2):
        # Use the latest schedule to compute scheduled events for these
        # systems, these many days in advance

        schedule = self.getSchedule()
        if not schedule:
            return
        managedSystemIdsEventStartDates = self._getManagedSystemEventStartDate(
            systems)
        if not managedSystemIdsEventStartDates:
            return
        # Compute end time
        dtend = datetime.datetime.now() + datetime.timedelta(days=daysInAdvance)
        cal = vobject.readOne(schedule.schedule)

        event = cal.vevent

        queuedStateId = self.jobStates['Queued'].job_state_id
        # XXX This is quite primitive for now
        cu = connection.cursor()
        cu.executemany("""
            DELETE FROM inventory_managed_system_scheduled_event
             WHERE managed_system_id = %s AND state_id = %s
         """, [ [ x[0], queuedStateId ] for x in managedSystemIdsEventStartDates ])

        now = datetime.datetime.now()
        initialState = self.jobStates['Queued']
        for msid, schedEventStartDate in managedSystemIdsEventStartDates:
            dtstart = datetime.datetime.fromtimestamp(schedEventStartDate)
            nevent = event.duplicate(event)
            nevent.add('dtstart').value = dtstart
            for eventTime in nevent.rruleset.between(now, dtend):
                ts = self._totimestamp(eventTime)
                obj = models.managed_system_scheduled_event(
                    managed_system_id = msid,
                    scheduled_time = ts,
                    schedule = schedule,
                    state = initialState)
                obj.save()

    def getScheduledEvents(self, systems):
        managedSystemIdsEventStartDates = self._getManagedSystemEventStartDate(
                    systems)
        ret = []
        for msid, _ in managedSystemIdsEventStartDates:
            ret.extend(models.managed_system_scheduled_event.objects.filter(
                managed_system__id = msid))
        return ret


    def _getManagedSystemEventStartDate(self, systems):
        if systems is None:
            return [ (x.id, x.scheduled_event_start_date)
                for x in models.managed_system_id.objects.all() ]
        managedSystems = []
        for system in systems:
            managedSystems.extend(models.managed_system.objects.filter(
                local_uuid = system.local_uuid,
                generated_uuid = system.generated_uuid))
        return [ (x.id, x.scheduled_event_start_date)
            for x in managedSystems ]

    @staticmethod
    def _totimestamp(dt):
        # Compute number of seconds since Jan 1 1970
        dtclass = datetime.datetime
        utcdt = dt + (dtclass.utcnow() - dtclass.now())
        delta = utcdt - dtclass.utcfromtimestamp(0)
        return delta.days * 86400 + delta.seconds

    def addSchedule(self, schedule):
        sch = models.schedule.factoryParser(schedule)
        if not sch.created:
            sch.created = datetime.datetime.now()
        sch.save()
        return sch

    def getSchedule(self):
        schedules = models.schedule.objects.filter(enabled=1)
        if not schedules:
            return None
        sch = max((x.created, x) for x in schedules)[1]
        return sch
