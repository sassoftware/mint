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

from mint.lib import uuid, x509
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory.manager import base
from mint.rest import errors as mint_rest_errors

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
    ShutdownEvents = set([
        models.EventType.SYSTEM_SHUTDOWN,
        models.EventType.SYSTEM_SHUTDOWN_IMMEDIATE
    ])

    TZ = tz.tzutc()
    X509 = x509.X509

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
    def getLocalZone(self):
        "Return the zone for this rBuilder"
        zone = models.Zone.objects.get(name='Local rBuilder')
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
    def updateZone(self, zone):
        """Update a zone"""

        if not zone:
            return

        zone.save()
        return zone
    
    @base.exposed
    def deleteZone(self, zone):
        """Update a zone"""

        if not zone:
            return

        zone.delete()
        
        return

    @base.exposed
    def getSystem(self, system_id):
        system = models.System.objects.get(pk=system_id)
        system.addJobs()
        return system

    @base.exposed
    def deleteSystem(self, system_id):
        system = models.System.objects.get(pk=system_id)
        system.delete()

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
        return managementNode

    @base.exposed
    def getManagementNodes(self, zone_id):
        zone = models.Zone.objects.get(pk=zone_id)
        ManagementNodes = models.ManagementNodes()
        ManagementNodes.managementNode = list(models.ManagementNode.objects.filter(zone=zone).all())
        return ManagementNodes

    @base.exposed
    def getSystemState(self, system_state_id):
        systemState = models.SystemState.objects.get(pk=system_state_id)
        return systemState

    @base.exposed
    def getSystemStates(self):
        SystemStates = models.SystemStates()
        SystemStates.systemState = list(models.SystemState.objects.all())
        return SystemStates

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

        self.setSystemState(managementNode)
        #TO-DO Need to add the JID to the models.ManagementNode object
        return managementNode

    def _getProductVersionAndStage(self, nvf):
        name, version, flavor = nvf
        label = version.trailingLabel()
        hostname = label.getHost().split('.')[0]
        try:
            product = self.db.getProduct(hostname)
            prodVersions = self.db.listProductVersions(product.hostname)
        except mint_rest_errors.ProductNotFound:
            # Not a product that lives on this rba
            return None, None

        for version in prodVersions.versions:
            stages = self.db.getProductVersionStages(product.hostname, version.name)
            for stage in stages.stages:
                if stage.label == label.asString():
                    return version, stage

        return None, None


    def log_system(self, system, log_msg):
        system_log = system.createLog()
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
    def addSystem(self, system, generateCertificates=False):
        '''Add a new system to inventory'''

        if not system:
            return

        if system.management_node:
            return self.addManagementNode(system.zone.zone_id, system)

        # add the system
        system.save()

        self.setSystemState(system)

        if generateCertificates:
            self.generateSystemCertificates(system)

        if system.event_uuid:
            self.postprocessEvent(system)

        return system

    def postprocessEvent(self, system):
        # This code is kept here just as an example of how one can react to
        # events
        """
        # Look up the job associated with this event
        sjobs = models.SystemJob.objects.filter(system__system_id=system.pk,
            event_uuid=system.event_uuid)
        if not sjobs:
            return
        job = sjobs[0].job
        if job.event_type.name != job.event_type.SYSTEM_REGISTRATION:
            return
        # We came back from a registration. Schedule an immediate system poll.
        self.scheduleSystemPollNowEvent(system)
        """

    def setSystemState(self, system):
        if system.oldModel is None:
            self.log_system(system, models.SystemLogEntry.ADDED)
        registeredState = self.systemState(models.SystemState.REGISTERED)
        if system.isNewRegistration:
            system.registration_date = self.now()
            system.current_state = registeredState
            system.save()
            if system.oldModel is None:
                # We really see this system the first time with its proper
                # uuids. We'll assume it's been registered with rpath-register
                self.log_system(system, models.SystemLogEntry.REGISTERED)
            if not system.management_node:
                # Schedule a poll event in the future
                self.scheduleSystemPollEvent(system)
                # And schedule one immediately
                self.scheduleSystemPollNowEvent(system)
        elif system.isRegistered:
            if system.current_state.system_state_id != registeredState.system_state_id:
                system.current_state = registeredState
                system.save()
                self.log_system(system, models.SystemLogEntry.REGISTERED)
        else:
            # mark the system as needing registration
            self.scheduleSystemRegistrationEvent(system)


    def generateSystemCertificates(self, system):
        if system.ssl_client_certificate is not None and \
                system.ssl_client_key is not None:
            # Certs are already generated. We may want to re-generate them at
            # some point, but not now
            return
        if system.local_uuid is None or system.generated_uuid is None:
            # No point in trying to generate certificates if the system hasn't
            # registered yet
            return
        # Grab the low grade cert
        lg_cas = rbuildermodels.PkiCertificates.objects.filter(
            purpose="lg_ca").order_by('-time_issued')
        if not lg_cas:
            raise Exception("Unable to find suitable low-grade CA")
        lg_ca = lg_cas[0]
        ca_crt = self.X509(None, None)
        ca_crt.load_from_strings(lg_ca.x509_pem, lg_ca.pkey_pem)
        # When we get around to re-generate certs, bump the serial here
        serial = 0
        rbuilderIdent = "http://%s" % (self.cfg.siteHost, )
        cn = "local_uuid:%s generated_uuid:%s serial:%d" % (
            system.local_uuid, system.generated_uuid, serial)
        subject = self.X509.Subject(O="rPath rBuilder", OU=rbuilderIdent, CN=cn)
        crt = self.X509.new(subject=subject, serial=serial,
            issuer_x509=ca_crt.x509, issuer_pkey=ca_crt.pkey)
        del ca_crt
        system.ssl_client_certificate = crt.x509.as_pem()
        system.ssl_client_key = crt.pkey.as_pem(None)
        system.save()

    @base.exposed
    def updateSystem(self, system):
        # XXX This will have to change and be done in modellib, most likely.
        if self.checkAndApplyShutdown(system):
            return
        self.check_system_versions(system)
        self.setSystemStateFromJob(system)
        self.check_system_last_job(system)
        system.save()

    def check_system_last_job(self, system):
        # This is not the place to schedule an event, since rpath-tools may
        # not have come back yet. Leaving the code commented out as an example
        """"
        last_job = getattr(system, 'lastJob', None)
        if last_job and last_job.job_state.name == models.JobState.COMPLETED:
            if last_job.event_type.name in \
               (models.EventType.SYSTEM_APPLY_UPDATE,
                models.EventType.SYSTEM_APPLY_UPDATE_IMMEDIATE):
                self.scheduleSystemPollNowEvent(system)
        """

    def check_system_versions(self, system):
        # TODO: check for system.event_uuid
        # If there is an event_uuid set on system, assume we're just updating
        # the DB with the results of a job, otherwise, update the actual
        # installed software on the system.
        if system.event_uuid:
            self.mgr.setInstalledSoftware(system, system.new_versions)
        else:
            self.mgr.updateInstalledSoftware(system, system.new_versions)

    def checkAndApplyShutdown(self, system):
        currentStateName = system.current_state.name
        if currentStateName == models.SystemState.NONRESPONSIVE_SHUTDOWN:
            self.scheduleSystemShutdownEvent(system)
            return True
        else:
            return False

    def setSystemStateFromJob(self, system):
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
        # XXX Deal with time-based transitions too (i.e.
        # NONRESPONSIVE -> DEAD, DEAD->MOTHBALLED)
        jobStateName = job.job_state.name
        eventTypeName = job.event_type.name
        if jobStateName == models.JobState.COMPLETED:
            if eventTypeName in self.RegistrationEvents:
                # We don't trust that a registration action did anything, we
                # won't transition to REGISTERED, rpath-register should be
                # responsible with that
                return None
            if eventTypeName in self.PollEvents:
                return models.SystemState.RESPONSIVE
            else:
                # Add more processing here if needed
                return None
        if jobStateName == models.JobState.FAILED:
            currentStateName = system.current_state.name
            # Simple cases first.
            if currentStateName in [models.SystemState.UNMANAGED,
                    models.SystemState.DEAD,
                    models.SystemState.MOTHBALLED,
                    models.SystemState.NONRESPONSIVE,
                    models.SystemState.NONRESPONSIVE_NET,
                    models.SystemState.NONRESPONSIVE_HOST,
                    models.SystemState.NONRESPONSIVE_SHUTDOWN,
                    models.SystemState.NONRESPONSIVE_SUSPENDED]:
                # No changes in this case
                return None
            if eventTypeName not in self.PollEvents:
                # Non-polling event, nothing to do
                return None
            if currentStateName in [models.SystemState.REGISTERED,
                    models.SystemState.RESPONSIVE]:
                return models.SystemState.NONRESPONSIVE
        # Some other job state, do nothing
        return None

    def lookupTarget(self, targetType, targetName):
        return rbuildermodels.Targets.objects.get(
            targettype=targetType, targetname=targetName)

    def launchSystem(self, system):
        managedSystem = models.managed_system.factoryParser(system)
        managedSystem.launching_user = self.user
        managedSystem.launch_date = int(time.time())
        managedSystem.save()
        target = self.lookupTarget(system.target_type, system.target_name)
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
    def getSystemLogEntries(self, system):
        systemLog = self.getSystemLog(system)
        logEntries = systemLog.system_log_entries.order_by('-entry_date')
        return logEntries

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
            enable_time = self.now() + datetime.timedelta(minutes=self.cfg.systemEventsPollDelay)
            
        self.logSystemEvent(systemEvent, enable_time)
        
        if systemEvent.dispatchImmediately():
            self.dispatchSystemEvent(systemEvent)
        
        return systemEvent
    
    def getSystemEventsForProcessing(self):        
        events = None
        try:
            # get events in order based on whether or not they are enabled and what their priority is (descending)
            current_time = self.now()
            events = models.SystemEvent.objects.filter(time_enabled__lte=current_time).order_by('-priority')[0:self.cfg.systemEventsNumToProcess].all()
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
            eventUuid=eventUuid,
            clientCert=event.system.ssl_client_certificate,
            clientKey=event.system.ssl_client_key)
        if None in [cimParams.clientKey, cimParams.clientCert]:
            # This is most likely a new system.
            # Get a cert that is likely to work
            outCerts = rbuildermodels.PkiCertificates.objects.filter(purpose="outbound").order_by('-time_issued')
            if outCerts:
                outCert = outCerts[0]
                cimParams.clientCert = outCert.x509_pem
                cimParams.clientKey = outCert.pkey_pem
        requiredNetwork = (network.required and destination) or None
        resultsLocation = repClient.ResultsLocation(
            path = "/api/inventory/systems/%d" % event.system.pk,
            port = 80)
        if eventType in self.RegistrationEvents:
            self._runSystemEvent(event, repClient.register, cimParams,
                resultsLocation, zone=zone, requiredNetwork=requiredNetwork)
        elif eventType in self.PollEvents:
            self._runSystemEvent(event, repClient.poll,
                cimParams, resultsLocation, zone=zone)
        elif eventType in self.SystemUpdateEvents:
            data = cPickle.loads(event.event_data)
            self._runSystemEvent(event, repClient.update, cimParams,
                resultsLocation, zone=zone, sources=data)
        elif eventType in self.ShutdownEvents:
            self._runSystemEvent(event, repClient.shutdown,
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
    def scheduleSystemShutdownEvent(self, system):
        '''Schedule an event to shutdown the system.'''
        shutdown_event_type = models.EventType.objects.get(
            name=models.EventType.SYSTEM_SHUTDOWN_IMMEDIATE)
        self.createSystemEvent(system, shutdown_event_type)

    @base.exposed
    def createSystemEvent(self, system, event_type, enable_time=None, 
                          data=None):
        event = None
        # do not create events for systems that we cannot possibly contact
        if self.getSystemHasHostInfo(system):
            if not enable_time:
                enable_time = self.now() + datetime.timedelta(minutes=self.cfg.systemEventsPollDelay)
            pickledData = cPickle.dumps(data)
            event = models.SystemEvent(system=system, event_type=event_type, 
                priority=event_type.priority, time_enabled=enable_time,
                event_data=pickledData)
            event.save()
            self.logSystemEvent(event, enable_time)
            
            if event.dispatchImmediately():
                self.dispatchSystemEvent(event)
        else:
            systemName = system.name or system.hostname or system.target_system_name
            log.info("System %s (%s) '%s' cannot be registered because there is no host information" % (system.pk, systemName, event_type.name))
            self.log_system(system,
                "Unable to register event '%s': no networking information" % event_type.name)

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

    @base.exposed
    def importTargetSystems(self, targetDrivers):
        if not targetDrivers:
            log.info("No targets found, nothing to import")
            return

        t0 = time.time()
        targetsData = self.collectTargetsData(targetDrivers)
        inventoryData = self.collectInventoryTargetsData()
        todelete, toupdate = targetsData.deltaSystems(inventoryData)
        self._disassociateFromTargets(todelete)
        self._addSystemsToTargets(toupdate)
        log.info("Import of systems from all targets completed in %.2f seconds" % (
            time.time() - t0))

    def _disassociateFromTargets(self, objList):
        for (targetType, targetName), systemMap in objList:
            target = self.lookupTarget(targetType, targetName)
            for targetSystemId in systemMap:
                system = models.System.objects.get(target=target,
                    target_system_id=targetSystemId)
                self.log_system(system, "Disassociating from target %s (%s)"
                    % (targetName, targetType))
                system.target = None
                system.save()
                models.SystemTargetCredentials.objects.filter(system=system).delete()

    def _addSystemsToTargets(self, objList):
        for (targetType, targetName), systemMap in objList:
            t0 = time.time()
            target = self.lookupTarget(targetType, targetName)

            log.info("Importing %d systems from target %s (%s)" % (
                len(systemMap), targetName, targetType))
            for targetSystemId, tSystem in systemMap.items():
                self._addSystemToTarget(target, targetSystemId, tSystem)
            log.info("Target %s (%s) import of %d systems completed in %.2f seconds" % (
                targetName, targetType, len(systemMap), time.time() - t0))

    def _addSystemToTarget(self, target, targetSystemId, targetSystem):
        t0 = time.time()
        log.info("  Importing system %s (%s)" % (targetSystemId,
            targetSystem.instanceName))
        system, created = models.System.objects.get_or_create(target=target,
            target_system_id=targetSystemId)
        if created:
            self.log_system(system, "System added as part of target %s (%s)" %
                (target.targetname, target.targettype))
            # Having nothing else available, we copy the target's name
            system.name = targetSystem.instanceName
            system.description = targetSystem.instanceDescription
            system.managing_zone = self.getLocalZone()
        system.target_system_name = targetSystem.instanceName
        system.target_system_description = targetSystem.instanceDescription
        self._addTargetSystemNetwork(system, target, targetSystem)
        system.target_system_state = targetSystem.state
        system.save()
        self._setSystemTargetCredentials(system, target,
            targetSystem.userNames)
        if created:
            t1 = time.time()
            self.scheduleSystemRegistrationEvent(system)
            log.info("    Scheduling action completed in %.2f seconds" %
                (time.time() - t1, ))
        log.info("  Importing system %s (%s) completed in %.2f seconds" %
            (targetSystemId, targetSystem.instanceName, time.time() - t0))

    def _addTargetSystemNetwork(self, system, target, tsystem):
        dnsName = tsystem.dnsName
        if dnsName is None:
            return
        nws = system.networks.all()
        for nw in nws:
            if dnsName in [ nw.dns_name, nw.ip_address ]:
                return
        # Remove the other networks, they're probably stale
        for nw in nws:
            ipAddress = nw.ip_address and nw.ip_address or "ip unset"
            self.log_system(system,
                "%s (%s): removing stale network information %s (%s)" %
                (target.targetname, target.targettype, nw.dns_name,
                ipAddress))
            nw.delete()
        self.log_system(system, "%s (%s): using %s as primary contact address" %
            (target.targetname, target.targettype, dnsName))
        nw = models.Network(system=system, dns_name=dnsName)
        nw.save()

    def _setSystemTargetCredentials(self, system, target, userNames):
        existingCredsMap = dict((x.credentials_id, x)
            for x in system.target_credentials.all())
        desiredCredsMap = dict()
        for userName in userNames:
            desiredCredsMap.update((x.targetcredentialsid.targetcredentialsid,
                    x.targetcredentialsid)
                for x in rbuildermodels.TargetUserCredentials.objects.filter(
                    targetid=target, userid__username=userName))
        existingCredsSet = set(existingCredsMap)
        desiredCredsSet = set(desiredCredsMap)

        for credId in existingCredsSet - desiredCredsSet:
            existingCredsMap[credId].delete()
        for credId in desiredCredsSet - existingCredsSet:
            stc = models.SystemTargetCredentials(system=system,
                credentials=desiredCredsMap[credId])
            stc.save()

    def collectInventoryTargetsData(self):
        targetsData = self.TargetsData()
        systems = models.System.objects.filter(target__isnull = False)
        for system in systems:
            target = system.target
            # Grab credentials used when importing this system
            credentials = system.target_credentials.all()
            userNames = []
            for cred in credentials:
                tucs = rbuildermodels.TargetUserCredentials.objects.filter(
                    targetid=target, targetcredentialsid=cred)
                userNames.extend(x.userid.username for x in tucs)
            if not userNames:
                userNames = [ None ]
            for userName in userNames:
                # We don't care about dnsName and system, they're not used for
                # determining uniqueness
                targetsData.addSystem(target.targettype, target.targetname,
                    userName, system.target_system_id,
                    system.target_system_name,
                    system.target_system_description, None, None)
        return targetsData

    class TargetsData(object):
        "Handy class to collect information about systems from all targets"
        class System(object):
            def __init__(self, instanceName, instanceDescription, dnsName,
                    state):
                self.userNames = []
                self.instanceName = instanceName
                self.instanceDescription = instanceDescription
                if state is not None:
                    state = state.encode('ascii')
                self.state = state
                self.dnsName = dnsName
            def addUser(self, userName):
                self.userNames.append(userName)
            def __repr__(self):
                return "<System instance; instanceName='%s'>" % (
                    self.instanceName, )

        def __init__(self):
            self._systemsMap = {}

        def addSystem(self, targetType, targetName, userName, instanceId,
                instanceName, instanceDescription, dnsName, state):
            # We key by (targetType, targetName). The value is another
            # dictionary keyed on instanceId (since within a single target,
            # the instance id is unique). The same system may be available to
            # multiple users.
            targetSystems = self._systemsMap.setdefault((targetType, targetName),
                {})
            system = targetSystems.setdefault(instanceId, self.System(
                instanceName, instanceDescription, dnsName, state))
            # weak attempt to enforce uniqueness of instanceId
            if (system.instanceName != instanceName or
                    system.instanceDescription != instanceDescription):
                raise Exception("Same instanceId for different systems: "
                    "Target type: %s; target name: %s; instanceId: %s; "
                    "names: (%s, %s); descriptions:  (%s, %s)" %
                    (targetType, targetName, instanceId,
                    instanceName, system.instanceName,
                    instanceDescription, system.instanceDescription))
            if userName is not None:
                system.addUser(userName)

        def iterSystems(self):
            """
            Returns list of:
                (targetName, targetType), { instanceId : System, ... })
            """
            return self._systemsMap.iteritems()

        def deltaSystems(self, other):
            if not isinstance(other, self.__class__):
                return [], []
            todelete = []
            toupdate = []
            # Grab targets we don't know about
            selfTargets = set(self._systemsMap)
            otherTargets = set(other._systemsMap)

            todeleteSet = otherTargets - selfTargets
            toaddSet = selfTargets - otherTargets
            toupdateSet = selfTargets.intersection(otherTargets)
            todelete = [ (x, other._systemsMap[x]) for x in todeleteSet ]

            # Unconditionally add the new targets
            toupdate = [ (x, self._systemsMap[x]) for x in toaddSet ]
            # We still have to delete systems that disappeared, so go through
            # the update list
            for k in toupdateSet:
                todel, toup = self._deltaTargetSystems(
                    self._systemsMap[k],
                    other._systemsMap[k])
                if todel:
                    todelete.append((k, todel))
                if toup:
                    toupdate.append((k, toup))

            return todelete, toupdate

        def _deltaTargetSystems(self, selfSystems, otherSystems):
            selfSet = set(selfSystems)
            otherSet = set(otherSystems)
            todeleteSet = otherSet - selfSet
            toupdateSet = selfSet - todeleteSet
            # These are systems we need to delete
            todelMap = dict((x, otherSystems[x]) for x in todeleteSet)
            toupMap = dict((x, selfSystems[x]) for x in toupdateSet)

            return todelMap, toupMap

    def collectTargetsData(self, targetDrivers):
        t0 = time.time()
        targetsData = self.TargetsData()
        for driver in targetDrivers:
            try:
                self.collectOneTargetData(driver, targetsData)
            except Exception, e:
                tb = sys.exc_info()[2]
                traceback.print_tb(tb)
                log.error("Failed importing systems from target %s: %s" % (driver.cloudType, e))
        log.info("Target data collected in %.2f seconds" % (time.time() - t0))
        return targetsData

    def collectOneTargetData(self, driver, targetsData):
        t0 = time.time()
        log.info("Enumerating systems for target %s (%s) as user %s" %
            (driver.cloudName, driver.cloudType, driver.userId))
        targetType = driver.cloudType
        targetName = driver.cloudName
        userName = driver.userId
        tsystems = driver.getAllInstances()
        for tsys in tsystems:
            instanceId = tsys.instanceId.getText()
            instanceName = tsys.instanceName.getText()
            instanceDescription = tsys.instanceDescription.getText()
            dnsName = (tsys.dnsName and tsys.dnsName.getText()) or None
            state = (tsys.state and tsys.state.getText()) or "unknown"
            targetsData.addSystem(targetType, targetName, userName,
                instanceId, instanceName, instanceDescription, dnsName,
                state)
        log.info("Target %s (%s) as user %s enumerated in %.2f seconds" %
            (driver.cloudName, driver.cloudType, driver.userId,
                time.time() - t0))

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
