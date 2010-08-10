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

from mint.django_rest import logger as log
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder import rbuilder_manager

from rpath_storage import api1 as storage

class SystemDBManager(rbuilder_manager.RbuilderDjangoManager):

    def __init__(self, *args, **kw):
        rbuilder_manager.RbuilderDjangoManager.__init__(self, *args, **kw)
        self.systemStore = self.getSystemStore()

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

    def getSystem(self, system_id):
        system = models.System.objects.get(pk=system_id)
        self.log_system(system, "System data fetched.")
        return system

    def deleteSystem(self, system):
        managedSystem = models.managed_system.objects.get(pk=system)
        managedSystem.delete()

    def getSystems(self):
        Systems = models.Systems()
        Systems.system = list(models.System.objects.all())
        return Systems

    def log_system(self, system, log_msg):
        system_log, created = models.SystemLog.objects.get_or_create(
            system=system)
        system_log_entry = models.SystemLogEntry(system_log=system_log,
            entry=log_msg)
        system_log.system_log_entries.add(system_log_entry)
        system_log.save()
        return system_log
        
    def addSystem(self, system):
        '''Add a new system to inventory'''
        
        if not system:
            return
        
        # add the system
        system.save()
        self.log_system(system, models.SystemLogEntry.ADDED)
        
        if system.activated:
            # TODO:  how to de-dup?
            self.log_system(system, models.SystemLogEntry.ACTIVATED)
            self.scheduleSystemPollEvent(system)
        else:
            # mark the system as needing activation
            self.scheduleSystemActivationEvent(system)

        return system

    def launchSystem(self, system):
        managedSystem = models.managed_system.factoryParser(system)
        managedSystem.launching_user = self.user
        managedSystem.launch_date = int(time.time())
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
        systemLog = system.system_log.all()
        if systemLog:
            return systemLog[0]
        else:
            models.SystemLog()

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
            
    def getSystemEvent(self, event_id):
        event = models.SystemEvent.objects.get(pk=event_id)
        return event

    def deleteSystemEvent(self, event):
        event = models.SystemEvent.objects.get(pk=event)
        event.delete()

    def getSystemEvents(self):
        SystemEvents = models.SystemEvents()
        SystemEvents.systemEvent = list(models.SystemEvent.objects.all())
        return SystemEvents
    
    def getSystemEventsForProcessing(self):        
        events = None
        try:
            # get events in order based on whether or not they are enabled and what their priority is (descending)
            current_time = datetime.datetime.utcnow()
            events = models.SystemEvent.objects.filter(time_enabled__lte=current_time).order_by('-priority')[0:self.cfg.systemPollCount].all()
        except models.SystemEvent.DoesNotExist:
            pass
        
        return events
    
    def processSystemEvents(self):
        events = self.getSystemEventsForProcessing()
        if not events:
            log.info("No systems events to process")
            return
        
        for event in events:
            self.dispatchSystemEvent(event)

    def dispatchSystemEvent(self, event):
        log.info("Processing %s event (id %d, enabled %s) for system %s (id %d)" % (event.event_type.name, event.system_event_id, event.time_enabled, event.system.name, event.system.system_id))
        
        # TODO:  dispatch it here, whatever that means
        
        # cleanup now that the event has been processed
        self.cleanupSystemEvent(event)
        
        # create the next event if needed
        if event.event_type.name == models.SystemEventType.POLL or event.event_type.name == models.SystemEventType.POLL_NOW:
            self.scheduleSystemPollEvent(event.system)
        else:
            log.debug("%s events do not trigger a new event creation" % event.event_type.name)
        
    def cleanupSystemEvent(self, event):
        # remove the event since it has been handled
        log.debug("cleaning up %s event (id %d) for system %s" % (event.event_type.name, event.system_event_id,event.system.name))
        event.delete()
            
    def scheduleSystemPollEvent(self, system):
        '''Schedule an event for the system to be polled'''
        poll_event = models.SystemEventType.objects.get(name=models.SystemEventType.POLL)
        self.createSystemEvent(system, poll_event)
        
    def scheduleSystemPollNowEvent(self, system):
        '''Schedule an event for the system to be polled now'''
        # happens on demand, so enable now
        enable_time = datetime.datetime.utcnow()
        event_type = models.SystemEventType.objects.get(
            name=models.SystemEventType.POLL_NOW)
        self.createSystemEvent(system, event_type, enable_time)
        
    def scheduleSystemActivationEvent(self, system):
        '''Schedule an event for the system to be activated'''
        # activation events happen on demand, so enable now
        enable_time = datetime.datetime.utcnow()
        activation_event_type = models.SystemEventType.objects.get(
            name=models.SystemEventType.ACTIVATION)
        self.createSystemEvent(system, activation_event_type, enable_time)
            
    def createSystemEvent(self, system, event_type, enable_time=None):
        if not enable_time:
            enable_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=self.cfg.systemEventDelay)
        event = models.SystemEvent(system=system, event_type=event_type, 
            priority=event_type.priority, time_enabled=enable_time)
        event.save()
        msg = "System %s event registered and will be enabled on %s" % (event_type.name, enable_time)
        self.log_system(event.system, msg)
        log.info(msg)
        
    def importTargetSystems(self):
        log.info("Importing target systems")
