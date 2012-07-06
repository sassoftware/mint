#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import cPickle
import logging
import sys
import random
import time
import traceback
from conary import versions as cny_versions
from conary.deps import deps as cny_deps
from conary.lib import util
from xobj import xobj

from django.db import connection
from django.conf import settings
from django.contrib.redirects import models as redirectmodels
from django.contrib.sites import models as sitemodels
from django.core.exceptions import ObjectDoesNotExist

from mint.lib import uuid, x509
from mint.lib import data as mintdata
from mint.django_rest import signals, timeutils
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import errors
from mint.django_rest.rbuilder.inventory import models
from mint.django_rest.rbuilder.inventory import zones as zmodels
from mint.django_rest.rbuilder.inventory import survey_models
from mint.django_rest.rbuilder.targets import models as targetmodels
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.querysets import models as querysetmodels
from mint.django_rest.rbuilder.jobs import models as jobmodels
from mint.django_rest.rbuilder.images import models as imagemodels
from mint.rest import errors as mint_rest_errors

from smartform import descriptor

log = logging.getLogger(__name__)
exposed = basemanager.exposed

system_assimilate_descriptor = """<descriptor>
  <metadata>
    <displayName>System Assimilation</displayName>
    <descriptions>
      <desc>System Assimilation</desc>
    </descriptions>
  </metadata>
  <dataFields/>
</descriptor>
"""

survey_scan_descriptor = """<descriptor>
  <metadata>
    <displayName>System Scan</displayName>
    <descriptions>
      <desc>System Scan</desc>
    </descriptions>
  </metadata>
  <dataFields>
    <field>
      <name>top_level_group</name>
      <descriptions>
        <desc>Group</desc>
      </descriptions>
      <type>str</type>
      <required>true</required>
    </field>
  </dataFields>
</descriptor>
"""

update_descriptor = """<descriptor>
  <metadata>
    <displayName>Update Software</displayName>
    <descriptions>
      <desc>Update your system</desc>
    </descriptions>
  </metadata>
  <dataFields/>
</descriptor>
"""

# TODO: copy/paste here could really use some templates
configure_descriptor = """<descriptor>
  <metadata>
    <displayName>Apply System Configuration</displayName>
    <descriptions>
      <desc>Apply System Configuration</desc>
    </descriptions>
  </metadata>
  <dataFields/>
</descriptor>
"""

class SystemManager(basemanager.BaseManager):
    RegistrationEvents = set([
        jobmodels.EventType.SYSTEM_REGISTRATION,
        jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE,
    ])
    ShutdownEvents = set([
        jobmodels.EventType.SYSTEM_SHUTDOWN,
        jobmodels.EventType.SYSTEM_SHUTDOWN_IMMEDIATE
    ])
    LaunchWaitForNetworkEvents = set([
        jobmodels.EventType.LAUNCH_WAIT_FOR_NETWORK
    ])
    ManagementInterfaceEvents = set([
        jobmodels.EventType.SYSTEM_DETECT_MANAGEMENT_INTERFACE,
        jobmodels.EventType.SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE
    ])
    SystemConfigurationEvents = set([
        jobmodels.EventType.SYSTEM_CONFIG_IMMEDIATE,
    ])
    AssimilationEvents = set([
        jobmodels.EventType.SYSTEM_ASSIMILATE
    ])

    IncompatibleEvents = {
        # All events are incompatible with themselves (enforced in
        # checkEventCompatibility)
        # Can't shutdown and update at the same time
        # Can't shutdown and configure at the same time

        jobmodels.EventType.SYSTEM_UPDATE:\
            [jobmodels.EventType.SYSTEM_SHUTDOWN,
             jobmodels.EventType.SYSTEM_SHUTDOWN_IMMEDIATE],
        jobmodels.EventType.SYSTEM_SHUTDOWN:\
            [jobmodels.EventType.SYSTEM_UPDATE,
            jobmodels.EventType.SYSTEM_CONFIGURE],
        jobmodels.EventType.SYSTEM_SHUTDOWN_IMMEDIATE:\
            [jobmodels.EventType.SYSTEM_UPDATE,
             jobmodels.EventType.SYSTEM_CONFIGURE],
        jobmodels.EventType.SYSTEM_CONFIGURE:\
            [jobmodels.EventType.SYSTEM_SHUTDOWN,
             jobmodels.EventType.SYSTEM_SHUTDOWN_IMMEDIATE],
    }

    X509 = x509.X509

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

        # Recalculate available updates for each trove on the system, if
        # needed.  This call honors the 24 hour cache.
        for trove in system.installed_software.all():
            self.mgr.versionMgr.set_available_updates(trove)
        return system

    @exposed
    def deleteSystem(self, system_id):
        system = models.System.objects.get(pk=system_id)
        # API deletions used here to prevent cascade delete loop issues 
        # that occur via diffs combined with latest_survey association
        matching_surveys = survey_models.Survey.objects.filter(
            system=system
        )
        for survey in matching_surveys:
            self.mgr.deleteSurvey(survey.uuid)

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
    def getImageImportMetadataDescriptor(self):
        importDescriptorFile = open(self.cfg.metadataDescriptorPath)
        descr = descriptor.ConfigurationDescriptor(fromStream=importDescriptorFile)
        return descr

    @exposed
    def getInfrastructureSystems(self):
        systems = models.Systems()
        systems.system = \
            models.System.objects.filter(system_type__infrastructure=True)
        return systems

    @exposed
    def getManagementInterface(self, management_interface_id):
        managementInterface = models.Cache.get(models.ManagementInterface,
                pk=int(management_interface_id))
        return managementInterface

    @exposed
    def getManagementInterfaces(self):
        ManagementInterfaces = models.ManagementInterfaces()
        ManagementInterfaces.management_interface = models.Cache.all(
            models.ManagementInterface)
        return ManagementInterfaces
    
    @exposed
    def updateManagementInterface(self, management_interface):
        """Update a management interface"""

        if not management_interface:
            return


        management_interface.save()
        return management_interface

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
    def getWindowsBuildServiceSystemType(self):
        "Return the zone for this rBuilder"
        return models.Cache.get(models.SystemType,
            name=models.SystemType.INFRASTRUCTURE_WINDOWS_BUILD_NODE)

    @exposed
    def wmiManagementInterface(self):
        return models.Cache.get(models.ManagementInterface,
            name=models.ManagementInterface.WMI)

    @exposed
    def cimManagementInterface(self):
        return models.Cache.get(models.ManagementInterface,
            name=models.ManagementInterface.CIM)

    @exposed
    def sshManagementInterface(self):
        return models.Cache.get(models.ManagementInterface,
            name=models.ManagementInterface.SSH)

    @exposed
    def getWindowsBuildServiceNodes(self):
        nodes = []
        try:
            system_type = self.getWindowsBuildServiceSystemType()
            systems = self.getSystemTypeSystems(system_type.system_type_id)
            nodes = systems and systems.system or []
        except ObjectDoesNotExist:
            pass
        
        return nodes

    @exposed
    def getWindowsBuildServiceDestination(self):
        nodes = self.getWindowsBuildServiceNodes()
        if not nodes:
            return None
        node = random.choice(nodes)
        network = self.extractNetworkToUse(node)
        if not network:
            return None
        r = network.ip_address or network.dns_name
        dest = str(r.strip())
        log.info("Selected Windows Build Service with network address %s", dest)
        return dest

    @exposed
    def addWindowsBuildService(self, name, description, network_address):
        log.info("Adding Windows Build Service with name '%s', description '%s', and network address '%s'" % (name, description, network_address))
        system = models.System(name=name, description=description)
        system.current_state = self.systemState(models.SystemState.UNMANAGED)
        system.managing_zone = self.getLocalZone()
        system.management_interface = models.ManagementInterface.objects.get(pk=1)
        system.system_type = self.getWindowsBuildServiceSystemType()
        system.save()

        network = models.Network()
        network.dns_name = network_address
        network.system = system
        network.save()
        
        return system

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
    def addSystem(self, system, generateCertificates=False,
                  withManagementInterfaceDetection=True, for_user=None,
                  withRetagging=True):
        '''Add a new system to inventory'''

        if not system:
            return

        try:
            if system.system_type.name == models.SystemType.INFRASTRUCTURE_MANAGEMENT_NODE:
                return self.addManagementNode(system)
        except ObjectDoesNotExist:
            pass # will default later on

        system.created_by = for_user
        system.modified_by = for_user

        # add the system
        system.save()

        if system.survey is not None:
            # XXX we theoretically shouldn't have to have the synthetic
            # field, and be able to pass the survey as part of the
            # surveys collection, but because of all the special parsing
            # in surveymgr, this is not possible at the moment -- misa
            self.mgr.addSurveyForSystemFromXobj(system.system_id, system)

        # Verify potential duplicates here
        system = self.mergeSystems(system)

        # setSystemState will generate a CIM call; if it's a new registration,
        # it will be using the outbound certificate signed by the low-grade
        # CA. The personalized pair is not stored on the disk yet
        self.setSystemState(system,
            withManagementInterfaceDetection=withManagementInterfaceDetection)

        if generateCertificates:
            self.generateSystemCertificates(system)

        if system.event_uuid:
            self.postprocessEvent(system)

        if withRetagging:
            if for_user:
                self.mgr.addToMyQuerySet(system, for_user)
            self.mgr.retagQuerySetsByType('system', for_user)

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
        if oldModel:
            currentState = self.systemState(oldModel.current_state.name)
            if currentState == responsiveState:
                savedState = currentState

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
                DELETE FROM inventory_system_installed_software
                 WHERE system_id = %s
            """, [ system.pk ])
            cu.execute("""
                UPDATE inventory_system_installed_software
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

    def setSystemState(self, system, withManagementInterfaceDetection=True):
        if system.oldModel is None:
            self.log_system(system, models.SystemLogEntry.ADDED)
        registeredState = self.systemState(models.SystemState.REGISTERED)
        onlineState = self.systemState(models.SystemState.RESPONSIVE)
        credentialsMissing = self.systemState(models.SystemState.UNMANAGED_CREDENTIALS_REQUIRED)
        winBuildNodeType = self.getWindowsBuildServiceSystemType()
        wmiIfaceId = self.wmiManagementInterface().management_interface_id
        if system.isNewRegistration:
            system.registration_date = self.now()
            system.current_state = registeredState
            system.save()
            if system.oldModel is None:
                # We really see this system the first time with its proper
                # uuids. We'll assume it's been registered with rpath-register
                self.log_system(system, models.SystemLogEntry.REGISTERED)
            if (system.management_interface_id == wmiIfaceId and not system.credentials):
                # No credentials, nothing to do here
                system.current_state = credentialsMissing
                system.save()
        elif system.isRegistered:
            # See if a new poll is required
            if (system.current_state_id in self.NonresponsiveStates):
                system.current_state = registeredState
                system.save()
            # Already registered and no need to re-synchronize, if the
            # old state was online, and the new state is registered, we must
            # be coming in through rpath-tools, so preserve the online state.
            elif (system.oldModel is not None and 
                    system.oldModel.current_state.system_state_id == \
                    onlineState.system_state_id and
                    system.current_state_id == \
                    registeredState.system_state_id):
                system.current_state = onlineState
                system.save()
            elif system.current_state == registeredState:
                # system is registered and scanned, should just go ahead and mark online
                # definitely do not poll again as the initial registration polled.  Orchestrate if you
                # want crazy amounts of extra polling.
                system.current_state = onlineState
                system.save()
                return None
        elif system.isRegistrationIncomplete:
            self.log_system(system, "Incomplete registration: missing local_uuid. Possible cause: dmidecode malfunctioning")
        elif (system.management_interface_id == wmiIfaceId and not system.credentials):
                # No credentials, nothing to do here
                system.current_state = credentialsMissing
                system.save()
        elif withManagementInterfaceDetection:
            # Need to dectect the management interface on the system
            self.scheduleSystemDetectMgmtInterfaceEvent(system)
        # so that a transition between Inactive and Active systems will make the system
        # move between querysets.  Note, not retagging, would be grossly inefficient
        # with lots of system activity
        self.mgr.invalidateQuerySetsByType('system')

        
    def generateSystemCertificates(self, system):
        if system._ssl_client_certificate is not None and \
                system._ssl_client_key is not None:
            # Certs are already generated. We may want to re-generate them at
            # some point, but not now
            return
        if system.local_uuid is None or system.generated_uuid is None:
            # No point in trying to generate certificates if the system hasn't
            # registered yet
            return
        # We won't sign the certificate, because validation requires
        # that the lgca is present, and that totally defeats the purpose
        # of locking down security. We'll go with self-signed certs for now
        if 0:
            # Grab the low grade cert
            lg_cas = rbuildermodels.PkiCertificates.objects.filter(
                purpose="lg_ca").order_by('-time_issued')
            if not lg_cas:
                raise Exception("Unable to find suitable low-grade CA")
            lg_ca = lg_cas[0]
            ca_crt = self.X509(None, None)
            ca_crt.load_from_strings(lg_ca.x509_pem, lg_ca.pkey_pem)
            issuer_x509 = ca_crt.x509
            issuer_pkey = ca_crt.pkey
        else:
            issuer_pkey = issuer_x509 = None
        # When we get around to re-generate certs, bump the serial here
        serial = 0
        rbuilderIdent = "http://%s" % (self.cfg.siteHost, )
        cn = "local_uuid:%s generated_uuid:%s serial:%d" % (
            system.local_uuid, system.generated_uuid, serial)
        subject = self.X509.Subject(O="rPath rBuilder", OU=rbuilderIdent, CN=cn)
        crt = self.X509.new(subject=subject, serial=serial,
            issuer_x509=issuer_x509, issuer_pkey=issuer_pkey)
        if 0:
            del ca_crt
        system._ssl_client_certificate = crt.x509.as_pem()
        system._ssl_client_key = crt.pkey.as_pem(None)
        system.save()

    @exposed
    def updateSystem(self, system, for_user=None):
        if not system.event_uuid and self.checkAndApplyShutdown(system):
            return
        self.checkInstalledSoftware(system)
        last_job = getattr(system, 'lastJob', None)
        if last_job and last_job.job_state.name == jobmodels.JobState.COMPLETED:
            # This will update the system state as a side-effect
            self.addSystem(system, generateCertificates=False,
                withManagementInterfaceDetection=False,
                withRetagging=False)
        self.setSystemStateFromJob(system)
        if for_user:
            system.modified_by = for_user
        system.modified_date = timeutils.now()
        system.save()
        self.mgr.retagQuerySetsByType('system')
        return system

    def checkInstalledSoftware(self, system):
        # If there is an event_uuid set on system, assume we're just updating
        # the DB with the results of a job, otherwise, update the actual
        # installed software on the system.
        if system.new_versions is None:
            return
        troveSpecs = ["%s=%s[%s]" % x.getNVF()
            for x in system.new_versions ]
        # This isn't technically needed anymore, but for now it will prevent
        # clients from inadvertently overwriting the software if they still
        # PUT a system model and expect that to trigger a software update
        if not system.event_uuid:
            return
        if troveSpecs:
            msg = "Setting installed software to: %s" % (
                ', '.join(troveSpecs), )
        else:
            msg = "Deleting all installed software"
        self.log_system(system, msg)
        self.mgr.setInstalledSoftware(system, system.new_versions)

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
            nstate = self.systemState(nextSystemState)
            self.log_system(system, "System state change: %s -> %s" %
                (system.current_state.description, nstate.description))

            system.current_state = nstate
            system.state_change_date = self.now()
            system.save()

    @staticmethod
    def _getTrovesForLayeredImage(system):
        image = system.source_image
        # do not send down trove info for images we did not build,
        # images we built but never stored the source, or images
        # that are not layered/deferred
        if not image or not image.base_image:
            return None, None
        version = cny_versions.ThawVersion(str(image.trove_version))
        flavor = cny_deps.ThawFlavor(str(image.trove_flavor))
        installTrove = '%s=%s[%s]' % (image.trove_name, version, flavor)
        projectLabel = str(version.trailingLabel())
        return installTrove, projectLabel

    def getNextSystemState(self, system, job):

        # Return None if the state hasn't changed
        jobStateName = job.job_state.name
        eventTypeName = job.job_type.name
        system.updateDerivedData()


        if jobStateName == jobmodels.JobState.COMPLETED:
            if eventTypeName == jobmodels.EventType.SYSTEM_REGISTRATION:
                return models.SystemState.RESPONSIVE
            if eventTypeName in self.ManagementInterfaceEvents:
                # Management interface detection finished, need to schedule a
                # registration event now.
                wmiIfaceId = self.wmiManagementInterface().pk
                # unless we are SSH, in which case, assimilation is the only
                # way to upgrade to a interface type that can do something other
                # than just assimilate
                sshIfaceId = self.sshManagementInterface().pk

                # Copy credentials from the source image if available.
                self._copyImageCredentials(system)

                if system.management_interface_id == sshIfaceId:
                    # if no credentials, then the system is not one we are
                    # supposed to assimilate
                    if system.credentials:
                        # TODO: refactor
                        new_job = jobmodels.Job(
                            job_type = jobmodels.EventType.objects.get(
                                name=jobmodels.EventType.SYSTEM_ASSIMILATE
                            )
                        )
                        self.scheduleJobAction(system, new_job)
                        # assimilation will call rpath-register no need
                        # to queue now, it's not ready
                    return None

                if system.management_interface_id == wmiIfaceId:
                    if system.credentials and system.hasSourceImage():
                        # Ready to migrate after a layered image deployment.
                        trove, _ = self._getTrovesForLayeredImage(system)
                        self.scheduleSystemApplyUpdateEvent(system, [trove])
                    elif not system.credentials:
                        # No credentials avaiable, prompt the user for them.
                        return models.SystemState.UNMANAGED_CREDENTIALS_REQUIRED
                self.scheduleSystemRegistrationNowEvent(system)
                return None
            else:
                # Add more processing here if needed
                return None
        if jobStateName == jobmodels.JobState.FAILED:
            currentStateName = system.current_state.name
            # Simple cases first.
            if job.status_code == 401:
                # Authentication required
                if currentStateName == models.SystemState.UNMANAGED:
                    return models.SystemState.UNMANAGED_CREDENTIALS_REQUIRED
                # A mothballed system remains mothballed
                if currentStateName in [models.SystemState.MOTHBALLED,
                        models.SystemState.UNMANAGED_CREDENTIALS_REQUIRED,
                        models.SystemState.NONRESPONSIVE_CREDENTIALS]:
                    return None
                return models.SystemState.NONRESPONSIVE_CREDENTIALS
            if currentStateName == models.SystemState.MOTHBALLED:
                return None
            timedelta = self.now() - system.state_change_date
            if currentStateName == models.SystemState.DEAD:
                if timedelta.days >= self.cfg.mothballedStateTimeout:
                    return models.SystemState.MOTHBALLED
                return None
            if currentStateName in self.NonresponsiveStates:
                if timedelta.days >= self.cfg.deadStateTimeout:
                    return models.SystemState.DEAD
                return None
            return None
        # Some other job state, do nothing
        return None

    def _copyImageCredentials(self, system):
        if not system.hasSourceImage():
            return

        # Now check to see if the source image has a base image trove in the
        # builddata. This means it is a deferred image and we need to lookup
        # the base image.
        builddata = imagemodels.ImageData.objects.filter(
                image=system.source_image, name='baseImageTrove')

        if not builddata:
            return

        baseImageTrove = builddata[0].value
        baseImage = imagemodels.Image.objects.filter(
                output_trove=baseImageTrove)[0]

        md = baseImage.metadata
        username = password = domain = key = ''
        if hasattr(md, 'credentials_username'):
            username = md.credentials_username
        if hasattr(md, 'credentials_password'):
            password = md.credentials_password
        if hasattr(md, 'credentials_domain'):
            domain = md.credentials_domain
        if hasattr(md, 'credentials_sshkey'):
            key = md.credentials_sshkey

        creds = dict(
            username=username,
            password=password,
            domain=domain,
            key=key,
        )

        self._addSystemCredentials(system, creds)

    def lookupTarget(self, targetTypeName, targetName):
        return targetmodels.Target.objects.get(
            target_type__name=targetTypeName, name=targetName)

    @exposed
    def captureSystem(self, system, params):
        if not system.target_id:
            raise errors.SystemNotDeployed()
        # XXX more stuff to happen here

    @exposed
    def addLaunchedSystems(self, systems, imageId=None, forUser=None):
        if imageId is not None:
            img = imagemodels.Image.objects.get(image_id=imageId)
        else:
            img = None
        # Copy the incoming systems; we'll replace them with real ones
        slist = systems.system
        rlist = systems.system = []
        for system in slist:
            djSystem = self.mgr.addLaunchedSystem(system,
                dnsName=system.dnsName,
                targetName=system.targetName, targetType=system.targetType,
                sourceImage=img, for_user=forUser)
            rlist.append(djSystem)
            if system.dnsName:
                self.postSystemLaunch(djSystem)
        return systems

    def fromXobj(self, obj):
        if obj is None:
            return obj
        return unicode(obj)

    @exposed
    def getXobjProperty(self, obj, prop, default=None):
        val = getattr(obj, prop, default)
        if val is default:
            return val
        return self.fromXobj(val)

    @exposed
    def addLaunchedSystem(self, system, dnsName=None, targetName=None,
            targetType=None, for_user=None, sourceImage=None):
        if isinstance(targetType, basestring):
            targetTypeName = targetType
        else:
            targetTypeName = targetType.name
        target = self.lookupTarget(targetTypeName=targetTypeName,
            targetName=targetName)
        system.target = target
        system.source_image = sourceImage
        # Copy incoming certs (otherwise read-only)
        system._ssl_client_certificate = system.ssl_client_certificate
        system._ssl_client_key = system.ssl_client_key
        if sourceImage is not None:
            system.project_id = sourceImage.project_id
            system.project_branch_id = sourceImage.project_branch_id
            system.project_branch_stage_id = sourceImage.project_branch_stage_id
        if system.managing_zone_id is None:
            system.managing_zone = self.getLocalZone()
        oldModel, system = models.System.objects.load_or_create(system,
            withReadOnly=True)
        xobjModel = getattr(system, '_xobjModel', None)
        # Copy some of the otherwise read-only fields
        system.target_system_name = self.getXobjProperty(xobjModel,
            'target_system_name', system.target_system_name)
        system.target_system_description = self.getXobjProperty(xobjModel,
            'target_system_description', system.target_system_description)
        system.target_system_state= self.getXobjProperty(xobjModel,
            'target_system_state', system.target_system_state)
        # Add an old style job, to persist the boot uuid
        self._addOldStyleJob(system)
        system.launching_user = self.user
        if for_user:
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
        self.addSystem(system, for_user=for_user,
            withManagementInterfaceDetection=False)
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
        for matchingIP in matchingIPs:
            sslCert = open(matchingIP.managed_system.ssl_client_certificate).read()
            if sslCert == system.ssl_client_certificate:
                return matchingIP.managed_system

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

    def _getCredentialsModel(self, system, credsDict):
        credentials = models.Credentials(system)
        for k, v in credsDict.items():
            setattr(credentials, k, v)
        return credentials

    @classmethod
    def unmarshalCredentials(cls, credentialsString):
        creds = mintdata.unmarshalGenericData(credentialsString)
        # Keys should be strings, not unicode
        creds = dict((str(k), v) for (k, v) in creds.iteritems())
        return creds

    @classmethod
    def marshalCredentials(cls, credentialsDict):
        return mintdata.marshalGenericData(credentialsDict)

    def _systemOrId(self, system_or_id):
        '''Allow input of systems or system ids'''
        if type(system_or_id) != models.System:
            return models.System.objects.get(pk=system_or_id)
        else:
            return system_or_id

    @exposed
    def getSystemCredentials(self, system):
        '''
        Get the credentials assigned to the management interface, which
        differs by type (SSH, WMI, CIM...), as an xobj model
        '''
        system = self._systemOrId(system)
        systemCreds = {}
        if system.management_interface:
            if system.management_interface.name in [ 'wmi', 'ssh' ]:
                if system.credentials is None:
                    systemCreds = {}
                else:
                    systemCreds = self.unmarshalCredentials(system.credentials)
            else: 
                systemCreds = dict(
                    ssl_client_certificate=system._ssl_client_certificate,
                    ssl_client_key=system._ssl_client_key)

        return self._getCredentialsModel(system, systemCreds)

    @exposed
    def addSystemCredentials(self, system_id, credentials):
        system = models.System.objects.get(pk=system_id)
        self._addSystemCredentials(system, credentials)
        # We assume the system is unmanaged, and kick a registration
        system.current_state = self.systemState(models.SystemState.UNMANAGED)
        system.save()
        # Schedule a system registration event after adding/updating
        # credentials.
        self.scheduleSystemRegistrationNowEvent(system)
        return self._getCredentialsModel(system, credentials)

    def _addSystemCredentials(self, system, credentials):
        if system.management_interface:
            if system.management_interface.name in [ 'wmi', 'ssh' ]:
                systemCreds = self.marshalCredentials(credentials)
                system.credentials = systemCreds
            elif system.management_interface.name == 'cim':
                if credentials.has_key('ssl_client_certificate'):
                    system._ssl_client_certificate = \
                        credentials['ssl_client_certificate']
                if credentials.has_key('ssl_client_key'):
                    system._ssl_client_key = credentials['ssl_client_key']

    @exposed
    def getSystemConfigurationDescriptor(self, system_id):
        system = models.System.objects.get(pk=system_id)
        return self.mgr.getConfigurationDescriptor(system)
    
    @exposed
    def getSystemConfiguration(self, system_id):
        system = models.System.objects.get(pk=system_id)
        if system.configuration is None:
            systemConfig = {}
        else:
            systemConfig = self.unmarshalConfiguration(system.configuration)
        return self._getConfigurationModel(system, systemConfig)

    @exposed
    def saveSystemConfiguration(self, system_id, configuration):
        system = models.System.objects.get(pk=system_id)
        systemConfig = self.marshalConfiguration(configuration)
        system.configuration = systemConfig
        system.configuration_set = True
        system.configuration_applied = False
        system.save()
        return self._getConfigurationModel(system, configuration)

    # FIXME: OBSOLETE with new config stuff, REMOVE
    def applySystemConfiguration(self):    
        self.scheduleSystemConfigurationEvent()

    def _getConfigurationModel(self, system, configDict):
        config = models.Configuration(system)
        for k, v in configDict.items():
            setattr(config, k, v)
        return config

    @classmethod
    def unmarshalConfiguration(cls, configString):
        config = mintdata.unmarshalGenericData(configString)
        # Keys should be strings, not unicode
        config = dict((str(k), v) for (k, v) in config.iteritems())
        return config

    @classmethod
    def marshalConfiguration(cls, configDict):
        return mintdata.marshalGenericData(configDict)

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

        # If this systemEvent requires that a management interface be set on
        # the system and one is not, instead schedule an event to detect the
        # interface.
        if systemEvent.event_type.requiresManagementInterface:
            if not system.management_interface:
                if self.getSystemHasHostInfo(system):
                    return self.scheduleSystemDetectMgmtInterfaceEvent(system) 
                else:
                    log.info("Event cannot be created for system id %s '%s' "
                        "because there is no host information" % \
                        (system.pk, systemEvent.event_type.description))
                    self.log_system(system,
                        "Unable to create event '%s': no networking information" %
                            systemEvent.event_type.description)
                    raise errors.InvalidNetworkInformation

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

        # Check other incompatible event types
        incompatibleEvents = self.IncompatibleEvents.get(
            event.event_type.name, None)
        if incompatibleEvents:
            for runningEventType in runningEventTypes:
                if runningEventType in incompatibleEvents:
                    raise errors.IncompatibleEvents(
                        firstEventType=runningEventType,
                        secondEventType=event.event_type.name)

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

    @classmethod
    @exposed
    def getSystemManagementInterfaceName(cls, system):
        if system.management_interface_id is None:
            # Assume CIM
            return models.ManagementInterface.CIM
        return system.management_interface.name

    def _computeDispatcherMethodParams(self, repClient, system, destination, eventUuid, requiredNetwork):
        methodMap = {
            models.ManagementInterface.CIM : self._cimParams,
            models.ManagementInterface.WMI : self._wmiParams,
            # this may have to change if the SSH interface starts to do more
            # than just assimilation
            models.ManagementInterface.SSH : None
        }
        mgmtInterfaceName = self.getSystemManagementInterfaceName(system)
        if mgmtInterfaceName == models.ManagementInterface.SSH:
            # there will be no following events, no need to do this.
            return None
        else:
            method = methodMap[mgmtInterfaceName]
        return method(repClient, system, destination, eventUuid, requiredNetwork)

    def _cimParams(self, repClient, system, destination, eventUuid, requiredNetwork):
        if system.target_id is not None:
            targetName = system.target.name
            targetType = system.target.target_type.name
        else:
            targetName = None
            targetType = None
        cimParams = repClient.CimParams(host=destination,
            port=system.agent_port,
            eventUuid=eventUuid,
            clientCert=system._ssl_client_certificate,
            clientKey=system._ssl_client_key,
            requiredNetwork=requiredNetwork,
            # XXX These three do not belong to cimParams
            instanceId=system.target_system_id,
            targetName=targetName,
            targetType=targetType,
            launchWaitTime=self.cfg.launchWaitTime)
        if None in [cimParams.clientKey, cimParams.clientCert]:
            # This is most likely a new system.
            # Get a cert that is likely to work
            outCerts = rbuildermodels.PkiCertificates.objects.filter(purpose="outbound").order_by('-time_issued')
            if outCerts:
                outCert = outCerts[0]
                cimParams.clientCert = outCert.x509_pem
                cimParams.clientKey = outCert.pkey_pem
        return cimParams

    def _wmiParams(self, repClient, system, destination, eventUuid, requiredNetwork):
        kwargs = {}
        credentialsString = system.credentials
        if credentialsString:
            kwargs.update(self.unmarshalCredentials(credentialsString))
            if not kwargs.get('domain'):
                # Copy hostname or IP to domain field if not provided, to
                # indicate that the credentials are for the local system
                kwargs['domain'] = destination.upper()
        kwargs.update(
            host=destination,
            port=system.agent_port,
            eventUuid=eventUuid,
            requiredNetwork=requiredNetwork)

        # SlotCompare objects are smart enough to ignore unknown keywords
        wmiParams = repClient.WmiParams(**kwargs)
        return wmiParams

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
        params = None
        if eventType not in self.AssimilationEvents:
            params = self._computeDispatcherMethodParams(repClient, event.system,
                destination, eventUuid, requiredNetwork)
            if params is None:
                # no follow up event for non-assimilation SSH operations
                return
        else:
            # assimilation events are not management interface related
            # so the computeDispatcher logic is short-circuited
            event_data = cPickle.loads(event.event_data)
            certs  = rbuildermodels.PkiCertificates.objects
            hcerts = certs.filter(purpose="hg_ca").order_by('-time_issued')

            cert   = hcerts[0].x509_pem

            # look at the source image to find the label
            installTrove, projectLabel = self._getTrovesForLayeredImage(
                    event.system)
            params = repClient.AssimilatorParams(host=destination,
                caCert=cert, sshAuth=event_data,
                eventUuid=eventUuid, projectLabel=projectLabel,
                installTrove=installTrove)

        resultsLocation = repClient.ResultsLocation(
            path = "/api/v1/inventory/systems/%d" % event.system.pk,
            port = 80)

        mgmtInterfaceName = self.getSystemManagementInterfaceName(event.system)

        job = None
        # TODO: refactor
        if eventType in self.RegistrationEvents:
            method = getattr(repClient, "register_" + mgmtInterfaceName)
            job = self._runSystemEvent(event, method, params, resultsLocation,
                user=self.user, zone=zone)
        elif eventType in self.SystemConfigurationEvents:
            data = event.event_data
            method = getattr(repClient, "configuration_" + mgmtInterfaceName)
            job = self._runSystemEvent(event, method, params, resultsLocation,
                user=self.user, zone=zone, configuration=data)
        elif eventType in self.ShutdownEvents:
            method = getattr(repClient, "shutdown_" + mgmtInterfaceName)
            job = self._runSystemEvent(event, method, params, resultsLocation,
                user=self.user, zone=zone)
        elif eventType in self.LaunchWaitForNetworkEvents:
            method = repClient.launchWaitForNetwork
            job = self._runSystemEvent(event, method, params, resultsLocation,
                user=self.user, zone=zone)
        elif eventType in self.ManagementInterfaceEvents:
            params = self.getManagementInterfaceParams(repClient, destination)
            params.eventUuid = eventUuid
            method = repClient.detectMgmtInterface
            job = self._runSystemEvent(event, method, params, resultsLocation,
                user=self.user, zone=zone)
        elif eventType in self.AssimilationEvents:
            method = repClient.bootstrap
            job = self._runSystemEvent(event, method, params, resultsLocation,
                user=self.user, zone=zone) # sources=data)
        else:
            log.error("Unknown event type %s" % eventType)
            raise errors.UnknownEventType(eventType=eventType)
        return job

    def getManagementInterfaceParams(self, repClient, destination):
        # Enumerate all management interfaces
        ifaces = models.Cache.all(models.ManagementInterface)
        interfacesList = [ dict(interfaceHref=x.get_absolute_url(), port=x.port)
            for x in ifaces ]
        # Order the list so we detect wmi before cim (luckily we can sort by
        # port number), but SSH should always come last.  This is a bit silly
        # as we could just hardcode the list, though this may prevent suprises
        # when we add the next one.
        def interfaceSorter(x):
            if x['port'] == 22:
                return 99999   # SSH comes last
            else:
                return x['port']
            
        interfacesList.sort(key=lambda x: interfaceSorter(x))
        params = repClient.ManagementInterfaceParams(host=destination,
            interfacesList=interfacesList)
        return params

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
        jobUuid = str(uuid.uuid4())

        logFunc = lambda x: log.info("System %s (%s), task %s (%s) %s" %
            (systemName, params.host, jobUuid, eventType, x))

        logFunc("queued")

        job = jobmodels.Job()
        job.job_uuid = jobUuid
        job.job_type = event.event_type
        job.job_state = self.jobState(jobmodels.JobState.QUEUED)
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
    def scheduleSystemRegistrationEvent(self, system):
        '''Schedule an event for the system to be registered'''
        # registration events happen on demand, so enable now
        return self._scheduleEvent(system,
            jobmodels.EventType.SYSTEM_REGISTRATION,
            enableTime=self.now())

    @exposed
    def scheduleSystemRegistrationNowEvent(self, system):
        '''Schedule an event for the system to be registered'''
        # registration events happen on demand, so enable now
        return self._scheduleEvent(system,
            jobmodels.EventType.SYSTEM_REGISTRATION_IMMEDIATE,
            enableTime=self.now())

    @exposed
    def scheduleSystemApplyUpdateEvent(self, system, sources):
        '''Schedule an event for the system to be updated'''
        # FIXME: verify that this function creates something that is usable by new-style update
        # code.   Is event data correct?
        return self._scheduleEvent(system,
            jobmodels.EventType.SYSTEM_UPDATE,
            eventData=sources)

    @exposed
    def scheduleSystemShutdownEvent(self, system):
        '''Schedule an event to shutdown the system.'''
        return self._scheduleEvent(system,
            jobmodels.EventType.SYSTEM_SHUTDOWN_IMMEDIATE)

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

    @exposed
    def scheduleSystemDetectMgmtInterfaceEvent(self, system):
        """
        Schedule an immediate event that detects the management interface
        on the system.
        """
        return self._scheduleEvent(system,
            jobmodels.EventType.SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE,
            enableTime=self.now())

    @exposed
    def scheduleSystemConfigurationEvent(self, system):
        '''Schedule an event for the system to be configured'''
        return self._scheduleEvent(system,
            jobmodels.EventType.SYSTEM_CONFIG_IMMEDIATE,
            enableTime=self.now(),
            eventData=system.configuration)

    @classmethod
    def configDictToXml(cls, configuration):
        if configuration is None:
            configuration = {}
        obj = Configuration(**configuration)
        return xobj.toxml(obj, prettyPrint=False, xml_declaration=False)

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
        job.descriptor_data = xobj.parse('<descriptor_data/>').descriptor_data
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
        if not existingSystems:
            t1 = time.time()
            self.scheduleSystemDetectMgmtInterfaceEvent(system)
            log.info("    Scheduling action completed in %.2f seconds" %
                (time.time() - t1, ))
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
        # FIXME: move this closer to the inventory action code
        system = models.System.objects.get(pk=systemId)
        methodMap = dict(
            assimilation = self.getDescriptorAssimilation,
            capture      = self.getDescriptorCaptureSystem,
            configure    = self.getDescriptorConfigure,
            update       = self.getDescriptorUpdate,
            survey_scan  = self.getDescriptorSurveyScan,
        )
        method = methodMap.get(descriptorType)
        if method is None:
            raise errors.errors.ResourceNotFound()
        return method(systemId)

    def getDescriptorAssimilation(self, systemId, *args, **kwargs):
        descr = descriptor.ConfigurationDescriptor(
            fromStream=system_assimilate_descriptor)
        return descr

    def getDescriptorUpdate(self, systemId, *args, **kwargs):
        descr = descriptor.ConfigurationDescriptor(
            fromStream=update_descriptor)
        return descr

    def getDescriptorSurveyScan(self, systemId, *args, **kwargs):
        descr = descriptor.ConfigurationDescriptor(
            fromStream=survey_scan_descriptor)
        return descr

    def getDescriptorConfigure(self, systemId, *args, **kwargs):
        descr = descriptor.ConfigurationDescriptor(
            fromStream=configure_descriptor)
        return descr

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
        # get integer job type even if not a django model
        job_name = job.job_type.name

        if job_name == jobmodels.EventType.SYSTEM_ASSIMILATE:
            creds = self.getSystemCredentials(system)
            password = getattr(creds, 'password', None)
            if password is None:
                raise Exception('no SSH credentials set')
            auth = [dict(
                sshUser     = 'root',
                sshPassword = password,
                sshKey      = creds.key,
            )]
            event = self._scheduleEvent(system, job_name, eventData=auth)
            # we can completely ignore descriptor and descriptor_data
            # for this job, because we have that data stored in credentials
            # but other actions will have work to do with them in this
            # function.
        else:
            raise Exception("action dispatch not yet supported on job type: %s" % job.job_type.name)
        
        if event is None:
            # this can happen if the event preconditions are not met and the exception
            # gets caught somewhere up the chain (which we should fix)
            raise Exception("failed to schedule event")
        return event

    def getDescriptorCaptureSystem(self, systemId, *args, **kwargs):
        system = models.System.objects.get(pk=systemId)
        DriverClass = targetmodels.Target.getDriverClassForTargetId(system.target_id)
        if not hasattr(DriverClass, "drvCaptureSystem"):
            raise errors.InvalidData(msg="drvCaptureSystem not supported")

        descr = descriptor.ConfigurationDescriptor(
            fromStream=DriverClass.systemCaptureXmlData)
        descr.setRootElement("descriptor_data")
        field = descr.getDataField('instanceId')
        field.set_default([system.target_system_id])
        from mint.django_rest.rbuilder.projects import models as projmodels
        # XXX Needs RBAC here
        stages = sorted((x.stage_id, self._makeStageLabel(x)) for x in projmodels.Stage.objects.all())
        descr.addDataField('stageId',
            descriptions = 'Project Stage',
            required = True,
            type = descr.EnumeratedType(descr.ValueWithDescription(
                                            str(sid), descriptions=slabel)
                for sid, slabel in stages),
            default=str(stages[0][0]))
        imageImportDescriptor = self.getImageImportMetadataDescriptor()
        for f in imageImportDescriptor.getDataFields():
            # The flex implementation assumes structured objects
            # whenever they see a dot, so avoid that for now
            f.set_name(f.get_name().replace('metadata.', 'metadata_'))
            descr.addDataField(f)
        return descr

    @classmethod
    def _makeStageLabel(cls, stage):
        labelComponents = [ stage.project.name, stage.project_branch.name, stage.name ]
        return ' / '.join(labelComponents)

    @exposed
    def serializeDescriptor(self, descriptor, validate=True):
        wrapper = models.modellib.etreeObjectWrapper(
            descriptor.getElementTree(validate=validate))
        return wrapper

    @exposed
    def systemUpdateSystem(self, system, job):
        # TODO Rename. This is a terrible name but needs to be
        #  distinguished from the old-school systemUpdate.
        try:
            self._updateSystem(system, job)
        except:
            exc = sys.exc_info()
            stream = util.BoundedStringIO()
            util.formatTrace(*exc, stream=stream, withLocals=False)
            stream.seek(0)

            job.job_state = self.mgr.getJobStateByName(jobmodels.JobState.FAILED)
            job.status_code = 500
            job.status_text = "Failed"
            job.status_detail = stream.read()
        else:
            job.job_state = self.mgr.getJobStateByName(jobmodels.JobState.COMPLETED)
            job.status_code = 200
            job.status_text = "Done"
        job.save()

class Configuration(object):
    _xobj = xobj.XObjMetadata(
        tag = 'configuration')
    def __init__(self, **kwargs):
        self.__dict__ = kwargs
