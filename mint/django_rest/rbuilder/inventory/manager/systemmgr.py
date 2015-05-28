#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import cPickle
import logging
import sys
import time
import traceback
import uuid
from conary import versions as cny_versions
from conary.deps import deps as cny_deps
from lxml import etree

from django.db import connection
from django.conf import settings
from django.contrib.redirects import models as redirectmodels
from django.contrib.sites import models as sitemodels
from django.core.exceptions import ObjectDoesNotExist

from mint.django_rest import signals, timeutils
from mint.django_rest.rbuilder.inventory import errors
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory import zones as zmodels
from mint.django_rest.rbuilder.targets import models as targetmodels
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.querysets import models as querysetmodels
from mint.django_rest.rbuilder.jobs import models as jobmodels
from mint.rest import errors as mint_rest_errors

log = logging.getLogger(__name__)
exposed = basemanager.exposed


class SystemManager(basemanager.BaseManager):
    LaunchWaitForNetworkEvents = set([
        jobmodels.EventType.LAUNCH_WAIT_FOR_NETWORK
    ])

    NonresponsiveStates = set([
        models.SystemState.NONRESPONSIVE,
        models.SystemState.NONRESPONSIVE_NET,
        models.SystemState.NONRESPONSIVE_HOST,
        models.SystemState.NONRESPONSIVE_SHUTDOWN,
        models.SystemState.NONRESPONSIVE_SUSPENDED,
        models.SystemState.NONRESPONSIVE_CREDENTIALS,
    ])

    now = timeutils.now

    @exposed
    def getEventTypes(self):
        EventTypes = jobmodels.EventTypes()
        EventTypes.event_type = list(models.Cache.all(jobmodels.EventType))
        return EventTypes

    @exposed
    def getEventType(self, event_type_id):
        eventType = models.Cache.get(jobmodels.EventType, pk=int(event_type_id))
        return eventType

    @exposed
    def getEventTypeByName(self, eventTypeName):
        return models.Cache.get(jobmodels.EventType, name=eventTypeName)

    @exposed
    def updateEventType(self, event_type):
        """Update an event type"""

        if not event_type:
            return

        event_type.save()
        return event_type

    @exposed
    def getZone(self, zone_id):
        zone = models.Cache.get(zmodels.Zone, pk=int(zone_id))
        return zone

    @exposed
    def getLocalZone(self):
        "Return the zone for this rBuilder"
        zone = models.Cache.get(zmodels.Zone, name=zmodels.Zone.LOCAL_ZONE)
        return zone

    @exposed
    def getZoneByJID(self, node_jid):
        zone = models.ManagementNode.objects.get(node_jid=node_jid).zone
        return zone

    @exposed
    def getZones(self):
        Zones = zmodels.Zones()
        Zones.zone = list(models.Cache.all(zmodels.Zone))
        return Zones

    @exposed
    def addZone(self, zone):
        """Add a zone"""
        if not zone:
            return
        zone.save()
        return zone

    @exposed
    def updateZone(self, zone):
        """Update a zone"""
        if not zone:
            return
        zone.save()
        return zone

    @exposed
    def deleteZone(self, zone):
        """Update a zone"""
        if not zone:
            return
        zone.delete()
        return

    @exposed
    def getNetwork(self, network_id):
        network = models.Network.objects.get(pk=network_id)
        return network

    @exposed
    def getNetworks(self):
        Networks = models.Networks()
        Networks.network = list(models.Network.objects.all())
        return Networks

    @exposed
    def updateNetwork(self, network):
        """Update a network"""
        if not network:
            return
        network.save()
        return network

    @exposed
    def deleteNetwork(self, network_id):
        network = models.Network.objects.get(pk=network_id)
        network.delete()

    @exposed
    def getSystem(self, system_id):
        system = models.System.objects.select_related().get(pk=system_id)
        return system

    @exposed
    def deleteSystem(self, system_id):
        system = models.System.objects.get(pk=system_id)
        system.delete()

    @exposed
    def getSystemByTargetSystemId(self, target_system_id):
        systems = models.System.objects.select_related().filter(
            target_system_id=target_system_id)
        if systems:
            return systems[0]
        else:
            return None

    @classmethod
    def _getClassName(cls, field):
        xobj = getattr(field, '_xobj', None)
        if xobj:
            clsName = xobj.tag
        else:
            clsName = field._meta.verbose_name
        return models.modellib.type_map[clsName]

    @exposed
    def getSystems(self):
        systems = models.Systems()
        qs = models.System.objects.select_related()
        systems.system = qs.all()
        return systems

    @exposed
    def getInventorySystems(self):
        systems = models.Systems()
        systems.system = \
            models.System.objects.select_related().filter(system_type__infrastructure=False)
        return systems

    @exposed
    def getInfrastructureSystems(self):
        systems = models.Systems()
        systems.system = \
            models.System.objects.filter(system_type__infrastructure=True)
        return systems

    @exposed
    def getManagementNode(self, management_node_id):
        managementNode = models.ManagementNode.objects.get(pk=management_node_id)
        return managementNode

    @exposed
    def getManagementNodes(self):
        ManagementNodes = models.ManagementNodes()
        ManagementNodes.management_node = list(models.ManagementNode.objects.all())
        return ManagementNodes

    @exposed
    def addManagementNode(self, managementNode):
        """Add a management node to the inventory"""

        if not managementNode:
            return

        managementNode.save()

        self.setSystemState(managementNode)
        #TO-DO Need to add the JID to the models.ManagementNode object
        return managementNode

    @exposed
    def synchronizeZones(self, managementNodes):
        # Grab all existing management nodes
        newhash = set(x.pk for x in managementNodes.management_node)
        oldNodes = models.ManagementNode.objects.all()
        for node in oldNodes:
            if node.pk not in newhash:
                # Ideally we want to disassociate the management node from the
                # zone, but zone_id is not nullable
                # For now, leave the system around until RBL-7703 is fixed
                continue
        # For good measure, save the nodes, since things like the jid may have
        # changed
        for x in managementNodes.management_node:
            # Management nodes live in the same zone they manage
            x.managing_zone_id = x.zone_id
            x.save()

    @exposed
    def getManagementNodeForZone(self, zone_id, management_node_id):
        zone = self.getZone(zone_id)
        managementNode = models.ManagementNode.objects.get(zone=zone, pk=management_node_id)
        return managementNode

    @exposed
    def addManagementNodeForZone(self, zone_id, managementNode):
        """Add a management node to the inventory"""

        if not managementNode:
            return

        zone = zmodels.Zone.objects.get(pk=zone_id)
        managementNode.zone = zone;
        managementNode.save()

        self.setSystemState(managementNode)
        #TO-DO Need to add the JID to the models.ManagementNode object
        return managementNode

    @exposed
    def getManagementNodesForZone(self, zone_id):
        zone = zmodels.Zone.objects.get(pk=zone_id)
        ManagementNodes = models.ManagementNodes()
        ManagementNodes.management_node = list(models.ManagementNode.objects.filter(zone=zone).all())
        return ManagementNodes

    @exposed
    def getSystemType(self, system_type_id):
        systemType = models.SystemType.objects.get(pk=system_type_id)
        return systemType

    @exposed
    def getSystemTypes(self):
        SystemTypes = models.SystemTypes()
        SystemTypes.system_type = list(models.SystemType.objects.all())
        return SystemTypes

    @exposed
    def updateSystemType(self, system_type):
        """Update a system type"""

        if not system_type:
            return

        system_type.save()
        return system_type

    @exposed
    def getSystemTypeSystems(self, system_type_id):
        system_type = self.getSystemType(system_type_id)
        Systems = models.Systems()
        Systems.system = system_type.systems.all()
        return Systems

    @exposed
    def getSystemState(self, system_state_id):
        systemState = models.Cache.get(models.SystemState, pk=int(system_state_id))
        return systemState

    @exposed
    def getSystemStates(self):
        SystemStates = models.SystemStates()
        SystemStates.system_state = list(models.Cache.all(models.SystemState))
        return SystemStates

    @classmethod
    def systemState(cls, stateName):
        return models.Cache.get(models.SystemState,
            name=stateName)

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

    @exposed
    def log_system(self, system, log_msg):
        system_log = system.createLog()
        system_log_entry = models.SystemLogEntry(system_log=system_log,
            entry=log_msg)
        system_log.system_log_entries.add(system_log_entry)
        system_log.save()
        return system_log

    @exposed
    def addSystems(self, systemList, for_user=None):
        '''Add add one or more systems to inventory'''
        for system in systemList:
            self.addSystem(system, for_user=for_user)

    @exposed
    def addSystem(self, system, generateCertificates=False, for_user=None,
                  withRetagging=True):
        '''Add a new system to inventory'''

        if not system:
            return

        try:
            if system.system_type.name == models.SystemType.INFRASTRUCTURE_MANAGEMENT_NODE:
                return self.addManagementNode(system)
        except ObjectDoesNotExist:
            pass # will default later on

        if for_user is not None:
            system.created_by = for_user
            system.modified_by = for_user

        # add the system
        system.save()

        # Verify potential duplicates here
        system = self.mergeSystems(system)

        self.setSystemState(system)

        if system.event_uuid:
            self.postprocessEvent(system)

        if withRetagging:
            if for_user:
                self.mgr.addToMyQuerySet(system, for_user)
            self.mgr.retagQuerySetsByType('system', for_user, defer=True)

        return system

    def mergeSystems(self, system):
        if not system.event_uuid:
            system._not_merged = True
            return system
        # Look up a system with a matching event_uuid
        systems = [ x.system
            for x in models.SystemJob.objects.filter(
                event_uuid = system.event_uuid) ]
        if not systems:
            return system
        # Realistically there should only be one
        systemByUuid = systems[0]
        if systemByUuid.pk == system.pk:
            # Same system, nothing to do
            return system
        systemToKeep, systemToRemove = sorted([system, systemByUuid],
            key = lambda x: x.pk)
        log.info("Merging 2 systems, id %s will be kept, id %s will be "
            "removed." % (systemToKeep.pk, systemToRemove.pk))
        system = self._merge(systemToKeep, systemToRemove)
        return system

    def _merge(self, system, other):
        # We don't want to overwrite the name and description
        other.name = other.description = None

        responsiveState = self.systemState(models.SystemState.RESPONSIVE)
        savedState = None
        oldModel = getattr(system, 'oldModel', None)
        if oldModel is not None:
            currentState = oldModel.xpath('./current_state/name/text()')
            if currentState and currentState[0] == responsiveState:
                savedState = responsiveState

        models.System.objects._copyFields(system, other, withReadOnly=True)

        if savedState:
            system.current_state = savedState

        # XXX maybe we should merge instead of simply updating, since we may
        # step over a unique constraint? -- misa
        cu = connection.cursor()
        cu.execute("""
            UPDATE inventory_system_target_credentials
               SET system_id = %s
              WHERE system_id = %s""", [ system.pk, other.pk, ])

        # If the other system has the uuids, we'll trust its network and
        # installed software info
        if other.generated_uuid:
            cu.execute("""
                DELETE FROM inventory_system_network
                 WHERE system_id = %s
            """, [ system.pk ])
            cu.execute("""
                UPDATE inventory_system_network
                   SET system_id = %s
                 WHERE system_id = %s
            """, [ system.pk, other.pk ])
            cu.execute("""
                UPDATE inventory_system_job
                   SET system_id = %s
                 WHERE system_id = %s
            """, [ system.pk, other.pk ])

        self._mergeLogs(cu, system, other)

        # Add a redirect from the deleted system to the saved system
        redirect = redirectmodels.Redirect(
            site=sitemodels.Site.objects.get(pk=settings.SITE_ID),
            new_path=system.get_absolute_url(),
            old_path=other.get_absolute_url())
        redirect.save()

        # Remove the other system before saving this one, or else we may stop
        # over some unique constraints (like the one on generated_uuid)
        other.delete()
        system.updateDerivedData()
        system.save()
        return system

    def _mergeLogs(self, cu, system, other):
        # See RBL-6968 - product management has agreed we shouldn't keep the
        # other system's logs
        # But now we're trying to merge them
        otherSystemLog = other.system_log.all()
        if not otherSystemLog:
            return
        otherSystemLog = otherSystemLog[0]
        systemLog = self.getSystemLog(system)
        cu.execute("""
            UPDATE inventory_system_log_entry
               SET system_log_id = %s,
                   entry = '(copied) ' || entry
             WHERE system_log_id = %s
        """, [ systemLog.pk, otherSystemLog.pk ])

    def postprocessEvent(self, system):
        # removable legacy artifact given new jobs infrastructure?  Does anything call this?
        pass

    def setSystemState(self, system):

        if system.oldModel is None:
            self.log_system(system, models.SystemLogEntry.ADDED)

        registeredState = self.systemState(models.SystemState.REGISTERED)
        onlineState = self.systemState(models.SystemState.RESPONSIVE)

        if system.isNewRegistration:
            system.update(registration_date=self.now(),
                current_state=onlineState)
            if system.oldModel is None:
                # We really see this system the first time with its proper
                # uuids. We'll assume it's been registered with rpath-register
                self.log_system(system, models.SystemLogEntry.REGISTERED)
        elif system.isRegistered:
            # See if a new poll is required
            if (system.current_state_id in self.NonresponsiveStates):
                system.update(current_state=registeredState)
            # Already registered and no need to re-synchronize, if the
            # old state was online, and the new state is registered, we must
            # be coming in through rpath-tools, so preserve the online state.
            elif (self._getSystemOldCurrentStateId(system) == \
                    onlineState.system_state_id and
                    system.current_state_id == \
                    registeredState.system_state_id):
                system.update(current_state=onlineState)
            elif system.current_state == registeredState:
                # system is registered and scanned, should just go ahead and mark online
                # definitely do not poll again as the initial registration polled.  Orchestrate if you
                # want crazy amounts of extra polling.
                system.update(current_state=onlineState)
                return None
        elif system.isRegistrationIncomplete:
            self.log_system(system, "Incomplete registration: missing local_uuid. Possible cause: dmidecode malfunctioning")
        # so that a transition between Inactive and Active systems will make the system
        # move between querysets.  Note, not retagging, would be grossly inefficient
        # with lots of system activity
        self.mgr.invalidateQuerySetsByType('system')

    @classmethod
    def _getSystemOldCurrentStateId(cls, system):
        if system.oldModel is None:
            return None
        ret = system.oldModel.xpath('./current_state/system_state_id/text()')
        if ret:
            return ret[0]
        return None

    @exposed
    def updateSystem(self, system, for_user=None):
        last_job = getattr(system, 'lastJob', None)
        if last_job and last_job.job_state.name == jobmodels.JobState.COMPLETED:
            # This will update the system state as a side-effect
            self.addSystem(system, generateCertificates=False,
                withRetagging=False)
        self.setSystemStateFromJob(system)
        if for_user:
            system.modified_by = for_user
        system.modified_date = timeutils.now()
        system.save()
        self.mgr.invalidateQuerySetsByType('system')
        return system

    def setSystemStateFromJob(self, system):
        job = system.lastJob
        if job is None:
            # This update did not come in as a result of a job
            return

        nextSystemState = self.getNextSystemState(system, job)
        if nextSystemState is not None:
            nstate = self.systemState(nextSystemState)
            self.log_system(system, "System state change: %s -> %s" %
                (system.current_state.description, nstate.description))

            system.update(current_state=nstate, state_change_date=self.now())

    @classmethod
    def _getTroveSpecForImage(cls, image):
        if image is None:
            return None, None, None, None
        version = cny_versions.ThawVersion(str(image.trove_version))
        flavor = cny_deps.ThawFlavor(str(image.trove_flavor))
        troveSpec = '%s=%s[%s]' % (image.trove_name, version.freeze(), flavor)
        return troveSpec, image.trove_name, version, flavor

    def getNextSystemState(self, system, job):

        # Return None if the state hasn't changed
        jobStateName = job.job_state.name
        eventTypeName = job.job_type.name
        system.updateDerivedData()


        if jobStateName == jobmodels.JobState.COMPLETED:
            if eventTypeName in [ jobmodels.EventType.SYSTEM_REGISTRATION, jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE ]:
                return models.SystemState.RESPONSIVE
            return None
        if jobStateName == jobmodels.JobState.FAILED:
            currentStateName = system.current_state.name
            # Simple cases first.
            if job.status_code == 401:
                return models.SystemState.NONRESPONSIVE_CREDENTIALS
            timedelta = self.now() - system.state_change_date
            if currentStateName == models.SystemState.DEAD:
                return None
            if currentStateName in self.NonresponsiveStates:
                if timedelta.days >= self.cfg.deadStateTimeout:
                    return models.SystemState.DEAD
                return None
            return None
        # Some other job state, do nothing
        return None

    def lookupTarget(self, targetTypeName, targetName):
        return targetmodels.Target.objects.get(
            target_type__name=targetTypeName, name=targetName)

    @exposed
    def addLaunchedSystems(self, systems, job=None, forUser=None):
        img = None
        if job:
            # Try to extract the image for this job
            images = job.images.all()
            if images:
                img = images[0].image
        # Copy the incoming systems; we'll replace them with real ones
        slist = systems.system
        rlist = systems.system = []
        for system in slist:
            djSystem = self.mgr.addLaunchedSystem(system,
                dnsName=system.dnsName,
                targetName=system.targetName, targetType=system.targetType,
                sourceImage=img, job=job,
                for_user=forUser)
            rlist.append(djSystem)
            if system.dnsName:
                self.postSystemLaunch(djSystem)
        return systems

    @exposed
    def getEtreeProperty(self, obj, prop, default=None):
        if obj is None:
            return default
        val = obj.find(prop)
        if val is not None:
            return val.text
        val = obj.attrib.get(prop)
        if val is not None:
            return val
        return default

    @exposed
    def addLaunchedSystem(self, system, dnsName=None, targetName=None,
            targetType=None, for_user=None, sourceImage=None, job=None):
        if isinstance(targetType, basestring):
            targetTypeName = targetType
        else:
            targetTypeName = targetType.name
        target = self.lookupTarget(targetTypeName=targetTypeName,
            targetName=targetName)
        system.target = target
        system.source_image = sourceImage
        if sourceImage is not None:
            system.project_id = sourceImage.project_id
            system.project_branch_id = sourceImage.project_branch_id
            system.project_branch_stage_id = sourceImage.project_branch_stage_id

        if system.managing_zone_id is None:
            system.managing_zone = self.getLocalZone()
        oldModel, system = models.System.objects.load_or_create(system,
            withReadOnly=True)
        etreeModel = getattr(system, '_etreeModel', None)
        # Copy some of the otherwise read-only fields
        system.target_system_name = self.getEtreeProperty(etreeModel,
            'target_system_name', system.target_system_name)
        system.target_system_description = self.getEtreeProperty(etreeModel,
            'target_system_description', system.target_system_description)
        system.target_system_state= self.getEtreeProperty(etreeModel,
            'target_system_state', system.target_system_state)
        # Add an old style job, to persist the boot uuid
        self._addOldStyleJob(system)
        system.launching_user = self.user
        if for_user is None:
            for_user = self.user
        system.created_by  = for_user
        system.modified_by = for_user
        system.launch_date = self.now()
        # Copy some of the data from the target
        if not system.name:
            system.name = system.target_system_name
        if not system.description:
            system.description = system.target_system_description
        # Look up the credentials for this user
        credentials = self._getCredentialsForUser(system.target)
        assert credentials is not None, "User should have credentials"

        # Check if system target creds have already been set.  This can happen
        # if the target systems import script has run in between launching the
        # instance and adding it to inventory.
        stcs = models.SystemTargetCredentials.objects.filter(
            system=system, credentials=credentials)
        if not stcs:
            # Not already set.  Create the link.
            stc = models.SystemTargetCredentials(system=system,
                credentials=credentials)
            stc.save()

        if dnsName:
            network = system._matchNetwork(dnsName)
            if network is None:
                models.Network.objects.create(system=system, dns_name=dnsName, active=True)
        self.log_system(system, "System launched in target %s (%s)" %
            (target.name, target.target_type.name))
        system.system_state = self.systemState(models.SystemState.UNMANAGED)
        self.addSystem(system, for_user=for_user)
        # Add target system
        # get_or_create needs the defaults arg to do this properly (#1631)
        defaults=dict(
            name=system.target_system_name,
            description=system.target_system_description or '',
            ip_addr_1=dnsName)
        tsys, created = targetmodels.TargetSystem.objects.get_or_create(
            target=target,
            target_internal_id=system.target_system_id,
            defaults=defaults)
        if not created:
            tsys.name = system.target_system_name
            tsys.description = system.target_system_description or ''
            # Only update the address if it's not null
            if dnsName:
                tsys.ip_addr_1 = dnsName
            tsys.save()
        targetmodels.TargetSystemCredentials.objects.get_or_create(
            target_system=tsys,
            target_credentials=credentials)
        if job is not None:
            # Link system to job. This call may be repeated, so
            # gracefully handle existing records
            jobmodels.JobSystemArtifact.objects.get_or_create(
                system=system, job=job)

        return system

    def _addOldStyleJob(self, system):
        if system.boot_uuid is None:
            return
        cu = connection.cursor()
        now = time.time() # self.now()
        # Make sure we don't insert duplicates
        cu.execute("""
            INSERT INTO jobs (job_uuid, job_type_id, job_state_id, created_by,
                created, modified)
            SELECT %s, %s, %s, %s, %s, %s
            WHERE NOT EXISTS (SELECT 1 FROM jobs WHERE job_uuid = %s)""",
            [ system.boot_uuid, 1, 3, self.user.user_id, now, now, system.boot_uuid])
        cu.execute("SELECT job_id FROM jobs WHERE job_uuid = %s", [ system.boot_uuid ])
        jobId = cu.fetchone()[0]

        cu.execute("""
            INSERT INTO job_system
                (job_id, system_id)
            SELECT %s, %s
            WHERE NOT EXISTS (
                SELECT 1
                  FROM job_system
                 WHERE job_id = %s
                   AND system_id = %s)""",
        [ jobId, system.pk, jobId, system.pk ])
        system.updateDerivedData()

    @exposed
    def postSystemLaunch(self, system):
        # No longer waiting for a network here, the target waits for
        # network
        self.setSystemState(system)
        system.updateDerivedData()
        return system

    def _getCredentialsForUser(self, target):
        tucs = targetmodels.TargetUserCredentials.objects.filter(
            target=target, user=self.user)
        for tuc in tucs:
            return tuc.target_credentials
        return None

    def matchSystem(self, system):
        matchingIPs = models.network_information.objects.filter(
                        ip_address=system.ip_address)
        if matchingIPs:
            return matchingIPs[0].managed_system
        else:
            return None

    def isManageable(self, managedSystem):
        if managedSystem.launching_user.user_id == self.user.user_id:
            # If we own the system, we can manage
            return True
        # Does the user who launched the system have the same credentials as
        # our current user?
        cu = connection.cursor()
        cu.execute("""
            SELECT 1
              FROM TargetUserCredentials tc1
              JOIN TargetUserCredentials tc2 USING (targetId, targetCredentialsId)
             WHERE tc1.userId = %s
               AND tc2.userId = %s
         """, [ self.user.user_id, managedSystem.launching_user.user_id ])
        row = cu.fetchone()
        return bool(row)

    @exposed
    def getSystemLog(self, system):
        systemLog = system.system_log.all()
        if systemLog:
            return systemLog[0]
        else:
            models.SystemLog()

    @exposed
    def getSystemLogEntries(self, system):
        systemLog = self.getSystemLog(system)
        logEntries = systemLog.system_log_entries.order_by('-entry_date')
        return logEntries

    @exposed
    def getSystemEvent(self, event_id):
        event = models.SystemEvent.objects.get(pk=event_id)
        return event

    @exposed
    def deleteSystemEvent(self, event):
        event = models.SystemEvent.objects.get(pk=event)
        event.delete()

    @exposed
    def getSystemEvents(self):
        SystemEvents = models.SystemEvents()
        SystemEvents.system_event = list(models.SystemEvent.objects.all())
        return SystemEvents

    @exposed
    def getSystemSystemEvents(self, system_id):
        system = models.System.objects.get(pk=system_id)
        events = models.SystemEvent.objects.filter(system=system)
        system_events = models.SystemEvents()
        system_events.system_event = list(events)
        return system_events

    @exposed
    def getSystemSystemEvent(self, system_id, system_event_id):
        event = models.SystemEvent.objects.get(pk=system_event_id)
        return event

    @exposed
    def addSystemSystemEvent(self, system_id, systemEvent):
        """Add a system event to a system"""

        if not system_id or not systemEvent:
            return

        system = models.System.objects.get(pk=system_id)
        systemEvent.system = system
        systemEvent.save()

        enable_time = None
        if systemEvent.dispatchImmediately():
            enable_time = self.now()
        else:
            enable_time = self.now() + timeutils.timedelta(minutes=self.cfg.systemEventsPollDelay)

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

    @exposed
    def processSystemEvents(self):
        events = self.getSystemEventsForProcessing()
        if not events:
            log.info("No systems events to process")
            return

        for event in events:
            try:
                self.dispatchSystemEvent(event)
            except (errors.IncompatibleEvent, errors.InvalidNetworkInformation):
                # Safely ignore these errors
                pass

    def checkEventCompatibility(self, event):
        runningJobs = event.system.jobs.filter(job_state__name=jobmodels.JobState.RUNNING)
        runningEventTypes = [j.job_type.name for j in runningJobs]

        # Event types are incompatible with themselves
        if event.event_type.name in runningEventTypes:
            raise errors.IncompatibleSameEvent(eventType=event.event_type.name)

    def dispatchSystemEvent(self, event):
        # Check if the system has any active jobs before creating the event.
        if event.system.hasRunningJobs():
            try:
                self.checkEventCompatibility(event)
            except (errors.IncompatibleEvent, errors.InvalidNetworkInformation), e:
                log.error(str(e))
                self.cleanupSystemEvent(event)
                raise

        log.info("Dispatching %s event (id %d, enabled %s) for system %s (id %d)" % \
            (event.event_type.name, event.system_event_id, event.time_enabled,
            event.system.name, event.system.system_id))

        try:
            job = self._dispatchSystemEvent(event)
        except:
            self.cleanupSystemEvent(event)
            raise
        else:
            if job is None:
                self.cleanupSystemEvent(event)

    def _cimParams(self, repClient, system, destination, eventUuid, requiredNetwork):
        # CIM is dead; this is just here for LaunchWaitForNetworkEvents
        if system.target_id is not None:
            targetName = system.target.name
            targetType = system.target.target_type.name
        else:
            targetName = None
            targetType = None
        cimParams = repClient.CimParams(host=destination,
            port=None,
            eventUuid=eventUuid,
            clientCert=None,
            clientKey=None,
            requiredNetwork=requiredNetwork,
            # XXX These three do not belong to cimParams
            instanceId=system.target_system_id,
            targetName=targetName,
            targetType=targetType,
            launchWaitTime=self.cfg.launchWaitTime)
        return cimParams

    def _dispatchSystemEvent(self, event):
        repClient = self.mgr.repeaterMgr.repeaterClient
        if repClient is None:
            log.info("Failed loading repeater client, expected in local mode only")
            return
        self.log_system(event.system,
            "Dispatching %s event" % event.event_type.description)

        network = self.extractNetworkToUse(event.system)
        eventType = event.event_type.name
        if not network and eventType not in self.LaunchWaitForNetworkEvents:
            msg = "No valid network information found; giving up"
            log.error(msg)
            self.log_system(event.system, msg)
            raise errors.InvalidNetworkInformation

        # If no ip address was set, fall back to dns_name
        if network:
            destination = network.ip_address or network.dns_name
            requiredNetwork = (network.pinned and destination) or None
        else:
            destination = None
            requiredNetwork = None

        eventUuid = str(uuid.uuid4())
        zone = event.system.managing_zone.name
        params = self._cimParams(repClient, event.system, destination,
                eventUuid, requiredNetwork)
        if params is None:
            return

        resultsLocation = repClient.ResultsLocation(
            path = "/api/v1/inventory/systems/%d" % event.system.pk,
            port = 80)

        if eventType in self.LaunchWaitForNetworkEvents:
            method = repClient.launchWaitForNetwork
            job = self._runSystemEvent(event, method, params, resultsLocation,
                user=self.user, zone=zone)
        else:
            log.error("Unknown event type %s" % eventType)
            raise errors.UnknownEventType(eventType=eventType)
        return job

    @exposed
    def extractNetworkToUse(self, system):
        return models.System.extractNetworkToUse(system)

    def _runSystemEvent(self, event, method, params, resultsLocation=None,
            **kwargs):
        user = kwargs.pop('user', None)
        systemName = event.system.name
        eventType = event.event_type.name
        if hasattr(params, 'eventUuid'):
            eventUuid = params.eventUuid
        else:
            eventUuid = kwargs.get('eventUuid')
        if not kwargs.get('jobToken'):
            kwargs['jobToken'] = str(uuid.uuid4())
        jobUuid = str(uuid.uuid4())

        logFunc = lambda x: log.info("System %s (%s), task %s (%s) %s" %
            (systemName, params.host, jobUuid, eventType, x))

        logFunc("queued")

        job = jobmodels.Job()
        job.job_uuid = jobUuid
        job.job_type = event.event_type
        job.job_state = self.jobState(jobmodels.JobState.QUEUED)
        job.job_token = str(kwargs['jobToken'])
        job.created_by = user
        job.save()

        sjob = models.SystemJob()
        sjob.job = job
        sjob.system = event.system
        sjob.event_uuid = eventUuid
        sjob.save()

        deferred = lambda connection=None, **kw: self._runEventLater(
            event, job, method, params, resultsLocation, kwargs, logFunc)
        signals.PostCommitActions.add(deferred)

        return job

    def _runEventLater(self, event, job, method, params, resultsLocation, kwargs, logFunc):
        try:
            self._runEventLater_r(job, method, params, resultsLocation, kwargs, logFunc)
        finally:
            # cleanup now that the event has been processed
            self.cleanupSystemEvent(event)

    @classmethod
    def _runEventLater_r(cls, job, method, params, resultsLocation, kwargs,
            logFunc):
        zone = kwargs.pop('zone', None)

        logFunc("executing")
        try:
            method(params, resultsLocation=resultsLocation, zone=zone, uuid=job.job_uuid, **kwargs)
        except Exception, e:
            tb = sys.exc_info()[2]
            traceback.print_tb(tb)
            logFunc("failed: %s" % (e, ))
            job.job_state = cls.jobState(jobmodels.JobState.FAILED)
            job.save()
            return None

        logFunc("in progress")
        job.job_state = cls.jobState(jobmodels.JobState.RUNNING)
        job.save()
        for system_job in job.systems.all():
            system_job.system.updateDerivedData()
        return job

    def cleanupSystemEvent(self, event):
        eventType = event.event_type
        system = event.system
        # remove the event since it has been handled
        log.debug("cleaning up %s event (id %d) for system %s" %
            (eventType.name, event.system_event_id, system.name))
        event.delete()

    @classmethod
    def eventType(cls, name):
        return models.Cache.get(jobmodels.EventType, name=name)

    @classmethod
    def jobState(cls, name):
        return jobmodels.JobState.objects.get(name=name)

    @exposed
    def scheduleLaunchWaitForNetworkEvent(self, system):
        """
        Schedule an event that either waits for the system's IP address to
        become available, or sees that the system has registered via
        rpath-tools.
        """
        return self._scheduleEvent(system,
            jobmodels.EventType.LAUNCH_WAIT_FOR_NETWORK,
            enableTime=self.now())

    def _scheduleEvent(self, system, eventType, enableTime=None,
            eventData=None):
        eventTypeObject = self.eventType(eventType)
        return self.createSystemEvent(system, eventTypeObject, enableTime=enableTime,
            eventData=eventData)

    @exposed
    def createSystemEvent(self, system, eventType, enableTime=None,
                          eventData=None):
        event = None
        # do not create events for systems that we cannot possibly contact
        if self.getSystemHasHostInfo(system) or \
                eventType.name in self.LaunchWaitForNetworkEvents:
            if not enableTime:
                enableTime = self.now() + timeutils.timedelta(
                    minutes=self.cfg.systemEventsPollDelay)
            if eventData is not None and not isinstance(eventData, basestring):
                pickledData = cPickle.dumps(eventData)
            else:
                pickledData = eventData
            event = models.SystemEvent(system=system, event_type=eventType,
                priority=eventType.priority, time_enabled=enableTime,
                event_data=pickledData)
            event.save()
            self.logSystemEvent(event, enableTime)

            if event.dispatchImmediately():
                self.dispatchSystemEvent(event)
        else:
            systemName = system.name or system.hostname or system.target_system_name
            log.info("Event cannot be created for system %s (%s) '%s' because "
                "there is no host information" % \
                (system.pk, systemName, eventType.description))
            self.log_system(system,
                "Unable to create event '%s': no networking information" %
                    eventType.description)

        system.updateDerivedData()
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

    def _iterTargetUserCredentials(self):
        "Iterate over all configured targets that have credentials"
        uqmap = dict()
        # We need to build a unique map of credentials for users
        for tuc in targetmodels.TargetUserCredentials.objects.all():
            uqmap[(tuc.target_id, tuc.target_credentials_id)] = tuc
        for tuc in uqmap.values():
            yield tuc

    def _importTargetSystemsForTUC(self, targetUserCredentials):
        jobType = self.getEventTypeByName(jobmodels.EventType.TARGET_REFRESH_SYSTEMS)
        target = targetUserCredentials.target
        job = jobmodels.Job(job_type=jobType)
        # This takes way too long, so let's manufacture the url by hand
        # for now
        #url = urlresolvers.reverse('TargetRefreshSystems', None,
        #    (target.target_id, ))
        job.descriptor = self.mgr.getDescriptorRefreshSystems(target.pk)
        job.descriptor.id = ("/api/v1/targets/%s/descriptors/refresh_systems" %
           target.target_id)
        job.descriptor_data = etree.fromstring('<descriptor_data/>')
        self.mgr.addJob(job)
        return job

    @exposed
    def importTargetSystems(self):
        jobs = []
        for tuc in self._iterTargetUserCredentials():
            jobs.append(self._importTargetSystemsForTUC(tuc))
        return jobs

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

    @exposed
    def addSystemsFromTarget(self, target):
        # Iterate over all existing target systems for this target
        tsystems = targetmodels.TargetSystem.objects.filter(target=target)
        for tsystem in tsystems:
            self._addSystemFromTarget(tsystem)

    def _addSystemFromTarget(self, targetSystem):
        t0 = time.time()
        target = targetSystem.target
        targetInternalId = targetSystem.target_internal_id
        log.info("  Importing system %s (%s)" % (
            targetInternalId, targetSystem.name))
        existingSystems = models.System.objects.filter(target=target,
            target_system_id=targetInternalId)
        if existingSystems:
            system = existingSystems[0]
        else:
            # Having nothing else available, we copy the target's name
            system, _ = models.System.objects.get_or_create(target=target,
                target_system_id=targetInternalId,
                managing_zone=target.zone,
                name=targetSystem.name,
                description=targetSystem.description)
            self.log_system(system, "System added as part of target %s (%s)" %
                (target.name, target.target_type.name))
        system.managing_zone = target.zone
        system.target_system_name = targetSystem.name
        system.target_system_description = targetSystem.description
        self._addTargetSystemNetwork(system, targetSystem)
        system.target_system_state = targetSystem.state
        system.save()
        self._setSystemTargetCredentials(system, targetSystem)
        log.info("  Importing system %s (%s) completed in %.2f seconds" %
            (system.target_system_id, system.target_system_name,
                time.time() - t0))

    def _addTargetSystemNetwork(self, system, tsystem):
        dnsName = tsystem.ip_addr_1
        if dnsName is None:
            return
        nws = system.networks.all()
        for nw in nws:
            if dnsName in [ nw.dns_name, nw.ip_address ]:
                return
        target = system.target
        # Remove the other networks, they're probably stale
        for nw in nws:
            ipAddress = nw.ip_address and nw.ip_address or "ip unset"
            self.log_system(system,
                "%s (%s): removing stale network information %s (%s)" %
                (target.name, target.target_type.name, nw.dns_name,
                ipAddress))
            nw.delete()
        self.log_system(system, "%s (%s): using %s as primary contact address" %
            (target.name, target.target_type.name, dnsName))
        nw = models.Network(system=system, dns_name=dnsName)
        nw.save()
        if tsystem.ip_addr_2:
            nw = models.Network(system=system, dns_name=tsystem.ip_addr_2)
            nw.save()

    def _setSystemTargetCredentials(self, system, targetSystem):
        cu = connection.cursor()
        query = """
            DELETE FROM inventory_system_target_credentials
             WHERE system_id = %s
               AND credentials_id NOT IN
                   (SELECT target_credentials_id
                      FROM target_system_credentials
                     WHERE target_system_id = %s)"""
        cu.execute(query, [ system.system_id, targetSystem.target_system_id ])
        query = """
            INSERT INTO inventory_system_target_credentials
                        (system_id, credentials_id)
            SELECT %s, target_credentials_id
              FROM target_system_credentials
             WHERE target_system_id = %s
               AND target_credentials_id NOT IN
                   (SELECT credentials_id
                      FROM inventory_system_target_credentials
                     WHERE system_id = %s)"""
        cu.execute(query, [ system.system_id, targetSystem.target_system_id,
            system.system_id ])

    @exposed
    def getSystemsLog(self):
        systemsLog = models.SystemsLog()
        systemLogEntries = \
            models.SystemLogEntry.objects.all().order_by('entry_date')
        systemsLog.system_log_entry = list(systemLogEntries)
        return systemsLog

    @exposed
    def getSystemTags(self, system_id):
        system = models.System.objects.get(pk=system_id)
        systemTags = querysetmodels.SystemTags()
        systemTags.system_tag = system.system_tags.all()
        return systemTags

    @exposed
    def getSystemTag(self, system_id, system_tag_id):
        systemTag = querysetmodels.SystemTag.objects.get(pk=system_tag_id)
        return systemTag

    @exposed
    def getSystemDescriptorForAction(self, systemId, descriptorType, parameters=None):
        # OBSOLETE
        raise errors.errors.ResourceNotFound()

    @exposed
    def scheduleJobAction(self, system, job):
        '''
        An action is a bare job submission that is a request to start
        a real job.

        Job coming in will be xobj only,
        containing job_type, descriptor, and descriptor_data.  We'll use
        that data to schedule a completely different job, which will
        be more complete.
        '''
        raise Exception("action dispatch not yet supported on job type: %s" % job.job_type.name)

    @classmethod
    def _makeStageLabel(cls, stage):
        labelComponents = [ stage.project.name, stage.project_branch.name, stage.name ]
        return ' / '.join(labelComponents)

    @exposed
    def serializeDescriptor(self, descriptor, validate=True):
        wrapper = models.modellib.etreeObjectWrapper(
            descriptor.getElementTree(validate=validate))
        return wrapper
