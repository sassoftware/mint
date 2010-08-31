#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import logging
import sys
import datetime
import os
import time
import traceback

from dateutil import tz

from django.db import connection

from conary import versions as cnyver
from conary.deps import deps

from mint.lib import uuid
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory.manager import base

log = logging.getLogger(__name__)

try:
    from rpath_repeater import client as repeater_client
except:
    log.info("Failed loading repeater client, expected in local mode only")
    repeater_client = None  # pyflakes=ignore


class SystemManager(base.BaseManager):
    @base.exposed
    def getEventTypes(self):
        EventTypes = models.EventTypes()
        EventTypes.eventType = list(models.EventType.objects.all())
        return EventTypes

    @base.exposed
    def getEventType(self, event_type_id):
        eventType = models.EventType.objects.get(pk=event_type_id)
        return eventType

    @base.exposed
    def getZone(self, zone_id):
        zone = models.Zone.objects.get(pk=zone_id)
        return zone

    @base.exposed
    def getZoneByJID(self, node_jid):
        zone = models.ManagementNode.objects.get(node_jid=node_jid).zone
        return zone

    @base.exposed
    def getZones(self):
        Zones = models.Zones()
        Zones.zone = list(models.Zone.objects.all())
        return Zones

    @base.exposed
    def addZone(self, zone):
        """Add a zone"""

        if not zone:
            return

        zone.save()
        return zone

    @base.exposed
    def getSystem(self, system_id):
        system = models.System.objects.get(pk=system_id)
        self.log_system(system, "System data fetched.")
        system.addJobs()
        return system

    @base.exposed
    def deleteSystem(self, system):
        managedSystem = models.managed_system.objects.get(pk=system)
        managedSystem.delete()

    @base.exposed
    def getSystems(self):
        Systems = models.Systems()
        Systems.system = list(models.System.objects.all())
        for s in Systems.system:
            s.addJobs()
        return Systems

    @base.exposed
    def getManagementNode(self, zone_id, management_node_id):
        zone = models.Zone.objects.get(pk=zone_id)
        managementNode = models.ManagementNode.objects.get(zone=zone, pk=management_node_id)
        self.log_system(managementNode, "Management node data fetched.")
        return managementNode

    @base.exposed
    def getManagementNodes(self, zone_id):
        zone = models.Zone.objects.get(pk=zone_id)
        ManagementNodes = models.ManagementNodes()
        ManagementNodes.managementNode = list(models.ManagementNode.objects.filter(zone=zone).all())
        return ManagementNodes

    @classmethod
    def systemState(cls, stateName):
        return models.SystemState.objects.get(name = stateName)

    @base.exposed
    def addManagementNode(self, zone_id, managementNode):
        """Add a management node to the inventory"""
        
        if not managementNode:
            return

        zone = models.Zone.objects.get(pk=zone_id)
        managementNode.zone = zone;
        managementNode.save()
        self.log_system(managementNode, models.SystemLogEntry.ADDED)
        
        if managementNode.registered:
            managementNode.registration_date = datetime.datetime.now(tz.tzutc())
            managementNode.current_state = self.systemState(
                models.SystemState.REGISTERED)
            #TO-DO Need to add the JID to the models.ManagementNode object
            managementNode.save()
            self.log_system(managementNode, models.SystemLogEntry.REGISTERED)
        else:
            managementNode.current_state = models.System.UNMANAGED
            managementNode.current_state = self.systemState(
                models.SystemState.UNMANAGED)
            managementNode.save()
        
        return managementNode

    def log_system(self, system, log_msg):
        system_log, created = models.SystemLog.objects.get_or_create(
            system=system)
        system_log_entry = models.SystemLogEntry(system_log=system_log,
            entry=log_msg)
        system_log.system_log_entries.add(system_log_entry)
        system_log.save()
        return system_log

    @base.exposed
    def addSystems(self, systemList):
        '''Add add one or more systems to inventory'''
        for system in systemList:
            self.addSystem(system)

    @base.exposed
    def addSystem(self, system):
        '''Add a new system to inventory'''

        if not system:
            return

        if system.management_node:
            return self.addManagementNode(system.zone.zone_id, system)

        # add the system
        system.save()
        self.log_system(system, models.SystemLogEntry.ADDED)
        
        if system.registered:
            system.registration_date = datetime.datetime.now(tz.tzutc())
            system.current_state = self.systemState(
                models.SystemState.REGISTERED)
            system.save()
            self.log_system(system, models.SystemLogEntry.REGISTERED)
            self.scheduleSystemPollEvent(system)
        else:
            # mark the system as needing registration
            self.scheduleSystemRegistrationEvent(system)

        return system

    @base.exposed
    def updateSystem(self, system):
        # XXX This will have to change and be done in modellib, most likely.
        self.check_system_versions(system)
        system.save()

    def check_system_versions(self, system):
        self.mgr.setInstalledSoftware(system, system.new_versions)

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

    def matchSystem(self, system):
        matchingIPs = models.network_information.objects.filter(
                        ip_address=system.ip_address)
        for matchingIP in matchingIPs:
            sslCert = open(matchingIP.managed_system.ssl_client_certificate).read()
            if sslCert == system.ssl_client_certificate:
                return matchingIP.managed_system

        return None

    def getSystemByInstanceId(self, instanceId):
        # TODO:  this code is outdated.  Returning plain system every time to move
        # forward, but we need to fix this to properly handle updates
        managedSystem = None
        #managedSystem = self.getManagedSystemForInstanceId(instanceId)
        if not managedSystem:
            syst = models.System()
            syst.is_manageable = False
            return syst
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

    @base.exposed
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
        # TODO:  this code is outdated.  Returning None every time to move
        # forward, but we need to fix this to properly handle updates
        return None
    
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
                              cnyver.ThawVersion(s.available_update.version),
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

    @base.exposed
    def getSystemEvent(self, event_id):
        event = models.SystemEvent.objects.get(pk=event_id)
        return event

    @base.exposed
    def deleteSystemEvent(self, event):
        event = models.SystemEvent.objects.get(pk=event)
        event.delete()

    @base.exposed
    def getSystemEvents(self):
        SystemEvents = models.SystemEvents()
        SystemEvents.systemEvent = list(models.SystemEvent.objects.all())
        return SystemEvents

    @base.exposed
    def getSystemSystemEvents(self, system_id):
        system = models.System.objects.get(pk=system_id)
        events = models.SystemEvent.objects.filter(system=system)
        system_events = models.SystemEvents()
        system_events.systemEvent = list(events)
        return system_events

    @base.exposed
    def getSystemSystemEvent(self, system_id, system_event_id):
        event = models.SystemEvent.objects.get(pk=system_event_id)
        return event

    @base.exposed
    def addSystemSystemEvent(self, system_id, systemEvent):
        """Add a system event to a system"""
        
        if not system_id or not systemEvent:
            return
        
        systemEvent.system = models.System.objects.get(pk=system_id)
        systemEvent.save()
        
        enable_time = None
        if systemEvent.dispatchImmediately():
            enable_time = datetime.datetime.now(tz.tzutc())
        else:
            enable_time = datetime.datetime.now(tz.tzutc()) + datetime.timedelta(minutes=self.cfg.systemEventDelay)
            
        self.logSystemEvent(systemEvent, enable_time)
        
        if systemEvent.dispatchImmediately():
            self.dispatchSystemEvent(systemEvent)
        
        return systemEvent
    
    def getSystemEventsForProcessing(self):        
        events = None
        try:
            # get events in order based on whether or not they are enabled and what their priority is (descending)
            current_time = datetime.datetime.now(tz.tzutc())
            events = models.SystemEvent.objects.filter(time_enabled__lte=current_time).order_by('-priority')[0:self.cfg.systemPollCount].all()
        except models.SystemEvent.DoesNotExist:
            pass
        
        return events

    @base.exposed
    def processSystemEvents(self):
        events = self.getSystemEventsForProcessing()
        if not events:
            log.info("No systems events to process")
            return

        for event in events:
            self.dispatchSystemEvent(event)

    def dispatchSystemEvent(self, event):
        log.info("Dispatching %s event (id %d, enabled %s) for system %s (id %d)" % (event.event_type.name, event.system_event_id, event.time_enabled, event.system.name, event.system.system_id))
        
        self._dispatchSystemEvent(event)

        # cleanup now that the event has been processed
        self.cleanupSystemEvent(event)

        # create the next event if needed
        if event.event_type.name == models.EventType.SYSTEM_POLL:
            self.scheduleSystemPollEvent(event.system)
        else:
            log.debug("%s events do not trigger a new event creation" % event.event_type.name)

    def _dispatchSystemEvent(self, event):
        repClient = self.mgr.repeaterMgr.repeaterClient
        if repClient is None:
            log.info("Failed loading repeater client, expected in local mode only")
            return
        self.log_system(event.system,  "Dispatching %s event" % event.event_type.name)

        registrationEvents = set([ models.EventType.SYSTEM_REGISTRATION ])
        pollEvents = set([
            models.EventType.SYSTEM_POLL,
            models.EventType.SYSTEM_POLL_IMMEDIATE,
        ])

        network = self._extractNetworkToUse(event.system)
        if not network:
            msg = "No valid network information found; giving up"
            log.error(msg)
            self.log_system(event.system, msg)
            return
        # If no ip address was set, fall back to dns_name
        destination = network.ip_address or network.dns_name
        eventType = event.event_type.name
        eventUuid = str(uuid.uuid4())
        #zone = event.system.managing_zone.name
        # XXX FIXME
        zone = None
        cimParams = repClient.CimParams(host=destination,
            eventUuid=eventUuid)
        requiredNetwork = (network.required and destination) or None
        if eventType in registrationEvents:
            self._runSystemEvent(event, repClient.register, cimParams,
                zone=zone, requiredNetwork=requiredNetwork)
        elif eventType in pollEvents:
            # XXX remove the hardcoded port from here
            resultsLocation = repClient.ResultsLocation(
                path = "/api/inventory/systems/%d" % event.system.pk,
                port = 80)
            self._runSystemEvent(event, repClient.poll,
                cimParams, resultsLocation, zone=zone)
        else:
            log.error("Unknown event type %s" % eventType)

    def _extractNetworkToUse(self, system):
        networks = system.networks.all()

        # first look for user required nets
        nets = [ x for x in networks if x.required ]
        if nets:
            return nets[0]

        # now look for a non-required active net
        nets = [ x for x in networks if x.active ]
        if nets:
            return nets[0]

        # If we only have one network, return that one and hope for the best
        if len(networks) == 1:
            return networks[0]
        return None

    @classmethod
    def _runSystemEvent(cls, event, method, cimParams, resultsLocation=None,
            **kwargs):
        zone = kwargs.pop('zone', None)
        systemName = event.system.name
        eventType = event.event_type.name
        eventUuid = cimParams.eventUuid
        log.info("System %s (%s), task type '%s' launching" %
            (systemName, cimParams.host, eventType))
        try:
            uuid, job = method(cimParams, resultsLocation, zone=zone)
        except Exception, e:
            tb = sys.exc_info()[2]
            traceback.print_tb(tb)
            log.error("System %s (%s), task type '%s' failed: %s" %
                (systemName, cimParams.host, eventType, str(e)))
            return None, None

        log.info("System %s (%s), task %s (%s) in progress" %
            (systemName, cimParams.host, uuid, eventType))
        job = models.Job()
        job.job_uuid = str(uuid)
        job.event_type = event.event_type
        job.job_state = cls.jobState(models.JobState.RUNNING)
        job.save()

        sjob = models.SystemJob()
        sjob.job = job
        sjob.system = event.system
        sjob.event_uuid = eventUuid
        sjob.save()
        return uuid, job

    def cleanupSystemEvent(self, event):
        # remove the event since it has been handled
        log.debug("cleaning up %s event (id %d) for system %s" % (event.event_type.name, event.system_event_id,event.system.name))
        event.delete()

    @classmethod
    def eventType(cls, name):
        return models.EventType.objects.get(name=name)

    @classmethod
    def jobState(cls, name):
        return models.JobState.objects.get(name=name)

    @base.exposed
    def scheduleSystemPollEvent(self, system):
        '''Schedule an event for the system to be polled'''
        poll_event = self.eventType(models.EventType.SYSTEM_POLL)
        self.createSystemEvent(system, poll_event)

    @base.exposed
    def scheduleSystemPollNowEvent(self, system):
        '''Schedule an event for the system to be polled now'''
        # happens on demand, so enable now
        enable_time = datetime.datetime.now(tz.tzutc())
        event_type = self.eventType(models.EventType.SYSTEM_POLL_IMMEDIATE)
        self.createSystemEvent(system, event_type, enable_time)

    @base.exposed
    def scheduleSystemRegistrationEvent(self, system):
        '''Schedule an event for the system to be registered'''
        # registration events happen on demand, so enable now
        enable_time = datetime.datetime.now(tz.tzutc())
        registration_event_type = self.eventType(
            models.EventType.SYSTEM_REGISTRATION)
        self.createSystemEvent(system, registration_event_type, enable_time)

    @base.exposed
    def createSystemEvent(self, system, event_type, enable_time=None):
        event = None
        
        # do not create events for systems that we cannot possibly contact
        if self.getSystemHasHostInfo(system):
            if not enable_time:
                enable_time = datetime.datetime.now(tz.tzutc()) + datetime.timedelta(minutes=self.cfg.systemEventDelay)
            event = models.SystemEvent(system=system, event_type=event_type, 
                priority=event_type.priority, time_enabled=enable_time)
            event.save()
            self.logSystemEvent(event, enable_time)
            
            if event.dispatchImmediately():
                self.dispatchSystemEvent(event)
        else:
            log.info("System %s %s event cannot be registered because there is no host information" % (system.name, event_type.name))
        
        return event
    
    def logSystemEvent(self, event, enable_time):
        msg = "Event type '%s' registered and will be enabled on %s" % (event.event_type.name, enable_time)
        self.log_system(event.system, msg)
        log.info(msg)
        
    def getSystemHasHostInfo(self, system):
        hasInfo = False
        if system and system.networks:
            for network in system.networks.all():
                if network.ip_address or network.ipv6_address or network.dns_name:
                    hasInfo = True
                    break
                
        return hasInfo
        
    def importTargetSystems(self, targetDrivers):
        if not targetDrivers:
            log.info("No targets found, nothing to import")
            return
        
        for driver in targetDrivers:
            try:
                self.importTargetSystem(driver)
            except Exception, e:
                tb = sys.exc_info()[2]
                traceback.print_tb(tb)
                log.error("Failed importing systems from target %s: %s" % (driver.cloudType, e))
        
    def importTargetSystem(self, driver):
        log.info("Processing target %s (%s) as user %s" % (driver.cloudName, 
            driver.cloudType, driver.userId))
        systems = driver.getAllInstances()
        systemsAdded = 0
        if systems:
            log.info("Importing %d systems from target %s (%s) as user %s" % (len(systems), 
                driver.cloudName, driver.cloudType, driver.userId))
            target = rbuildermodels.Targets.objects.filter(targetname=driver.cloudName).get()
            for sys in systems:
                db_system = models.System(name=sys.instanceName.getText(),
                    description=sys.instanceDescription.getText(), target=target)
                db_system.name = sys.instanceName.getText()
                db_system.description = sys.instanceDescription.getText()
                db_system.target_system_id = sys.instanceId.getText()
                dnsName = sys.dnsName and sys.dnsName.getText() or None
                
                state = sys.state and sys.state.getText() or "unknown"
                systemsAdded = systemsAdded +1
                log.info("Adding system %s (%s, state %s)" % (db_system.name, dnsName and dnsName or "no host info", state))
                db_system.save()
                if dnsName:
                    network = models.Network(system=db_system, dns_name=dnsName, active=True)
                    network.save()
                else:
                    log.info("No public dns information found for system %s (state %s)" % (db_system.name, state))
                
                # now add it
                self.addSystem(db_system)
            log.info("Added %d systems from target %s (%s) as user %s" % (systemsAdded, 
                driver.cloudName, driver.cloudType, driver.userId))

    @base.exposed
    def getSystemsLog(self):
        systemsLog = models.SystemsLog()
        systemLogEntries = \
            models.SystemLogEntry.objects.all().order_by('entry_date')
        systemsLog.systemLogEntry = list(systemLogEntries)
        return systemsLog

    @base.exposed
    def getSystemJobs(self, system, job_uuid):
        return None
    
    def resolveSystems(self):
        '''Used to resolve system dups and possibly other issues'''
        log.info("Resolving system inventory records")
