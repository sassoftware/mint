#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import cPickle
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

class SystemManager(base.BaseManager):
    RegistrationEvents = set([ models.EventType.SYSTEM_REGISTRATION ])
    PollEvents = set([
        models.EventType.SYSTEM_POLL,
        models.EventType.SYSTEM_POLL_IMMEDIATE,
    ])
    SystemUpdateEvents = set([
        models.EventType.SYSTEM_APPLY_UPDATE,
        models.EventType.SYSTEM_APPLY_UPDATE_IMMEDIATE,
    ])

    TZ = tz.tzutc()

    @classmethod
    def now(cls):
        return datetime.datetime.now(cls.TZ)

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
            managementNode.registration_date = self.now()
            managementNode.current_state = self.systemState(
                models.SystemState.REGISTERED)
            #TO-DO Need to add the JID to the models.ManagementNode object
            managementNode.save()
            self.log_system(managementNode, models.SystemLogEntry.REGISTERED)
        else:
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
            system.registration_date = self.now()
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
        self.setSystemState(system)
        self.check_system_last_job(system)
        system.save()

    def check_system_last_job(self, system):
        last_job = getattr(system, 'lastJob', None)
        if last_job and last_job.job_state.name == models.JobState.COMPLETED:
            if last_job.event_type.name in \
               (models.EventType.SYSTEM_APPLY_UPDATE,
                models.EventType.SYSTEM_APPLY_UPDATE_IMMEDIATE):
                self.scheduleSystemPollNowEvent(system)

    def check_system_versions(self, system):
        # TODO: check for system.event_uuid
        # If there is an event_uuid set on system, assume we're just updating
        # the DB with the results of a job, otherwise, update the actual
        # installed software on the system.
        if system.event_uuid:
            self.mgr.setInstalledSoftware(system, system.new_versions)
        else:
            self.mgr.updateInstalledSoftware(system, system.new_versions)

    def setSystemState(self, system):
        job = system.lastJob
        if job is None:
            # This update did not come in as a result of a job
            return

        nextSystemState = self.getNextSystemState(system, job)
        if nextSystemState is not None:
            self.log_system(system, "System state change: %s -> %s" %
                (system.current_state.name, nextSystemState))
            system.current_state = self.systemState(nextSystemState)
            system.save()

    def getNextSystemState(self, system, job):
        jobStateName = job.job_state.name
        eventTypeName = job.event_type.name
        if jobStateName == models.JobState.COMPLETED:
            if eventTypeName in self.RegistrationEvents:
                return models.SystemState.REGISTERED
            if eventTypeName in self.PollEvents:
                return models.EventType.RESPONSIVE
            else:
                # Add more processing here if needed
                return None
        if jobStateName == models.JobState.FAILED:
            currentStateName = system.current_state.name
            # Simple cases first.
            if currentStateName in [models.SystemState.DEAD,
                    models.SystemState.MOTHBALLED,
                    models.SystemState.NONRESPONSIVE]:
                # No changes in this case
                return None
            if eventTypeName not in self.PollEvents:
                # Non-polling event, nothing to do
                return None
        # Some other job state, do nothing
        return None

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

    @base.exposed
    def getSystemLog(self, system):
        systemLog = system.system_log.all()
        if systemLog:
            return systemLog[0]
        else:
            models.SystemLog()

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
            enable_time = self.now()
        else:
            enable_time = self.now() + datetime.timedelta(minutes=self.cfg.systemEventDelay)
            
        self.logSystemEvent(systemEvent, enable_time)
        
        if systemEvent.dispatchImmediately():
            self.dispatchSystemEvent(systemEvent)
        
        return systemEvent
    
    def getSystemEventsForProcessing(self):        
        events = None
        try:
            # get events in order based on whether or not they are enabled and what their priority is (descending)
            current_time = self.now()
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
        resultsLocation = repClient.ResultsLocation(
            path = "/api/inventory/systems/%d" % event.system.pk,
            port = 80)
        if eventType in self.RegistrationEvents:
            self._runSystemEvent(event, repClient.register, cimParams,
                zone=zone, requiredNetwork=requiredNetwork)
        elif eventType in self.PollEvents:
            # XXX remove the hardcoded port from here
            resultsLocation = repClient.ResultsLocation(
                path = "/api/inventory/systems/%d" % event.system.pk,
                port = 80)
            self._runSystemEvent(event, repClient.poll,
                cimParams, resultsLocation, zone=zone)
        elif eventType in self.SystemUpdateEvents:
            # XXX remove the hardcoded port from here
            data = cPickle.loads(event.event_data)
            self._runSystemEvent(event, repClient.update, cimParams,
                resultsLocation, zone=zone, sources=data)
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
            uuid, job = method(cimParams, resultsLocation, zone=zone, **kwargs)
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
        enable_time = self.now()
        event_type = self.eventType(models.EventType.SYSTEM_POLL_IMMEDIATE)
        self.createSystemEvent(system, event_type, enable_time)

    @base.exposed
    def scheduleSystemRegistrationEvent(self, system):
        '''Schedule an event for the system to be registered'''
        # registration events happen on demand, so enable now
        enable_time = self.now()
        registration_event_type = self.eventType(
            models.EventType.SYSTEM_REGISTRATION)
        self.createSystemEvent(system, registration_event_type, enable_time)

    @base.exposed
    def scheduleSystemApplyUpdateEvent(self, system, sources):
        '''Schedule an event for the system to be updated'''
        apply_update_event_type = models.EventType.objects.get(
            name=models.EventType.SYSTEM_APPLY_UPDATE_IMMEDIATE)
        self.createSystemEvent(system, apply_update_event_type, data=sources)

    @base.exposed
    def createSystemEvent(self, system, event_type, enable_time=None, 
                          data=None):
        event = None
        # do not create events for systems that we cannot possibly contact
        if self.getSystemHasHostInfo(system):
            if not enable_time:
                enable_time = self.now() + datetime.timedelta(minutes=self.cfg.systemEventDelay)
            pickledData = cPickle.dumps(data)
            event = models.SystemEvent(system=system, event_type=event_type, 
                priority=event_type.priority, time_enabled=enable_time,
                event_data=pickledData)
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
