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
from xobj import xobj

from django.db import connection
from django.conf import settings
from django.contrib.redirects import models as redirectmodels
from django.contrib.sites import models as sitemodels
from django.core.exceptions import ObjectDoesNotExist

from mint.lib import uuid, x509
from mint.lib import data as mintdata
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import errors
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
    LaunchWaitForNetworkEvents = set([
        models.EventType.LAUNCH_WAIT_FOR_NETWORK
    ])
    ManagementInterfaceEvents = set([
        models.EventType.SYSTEM_DETECT_MANAGEMENT_INTERFACE,
        models.EventType.SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE
    ])
    SystemConfigurationEvents = set([
        models.EventType.SYSTEM_CONFIG_IMMEDIATE,
    ])

    IncompatibleEvents = {
        # All events are incompatible with themselves (enforced in
        # checkEventCompatibility)
        # Can't shutdown and update at the same time
        # Can't shutdown and configure at the same time

        models.EventType.SYSTEM_APPLY_UPDATE:\
            [models.EventType.SYSTEM_SHUTDOWN,
             models.EventType.SYSTEM_SHUTDOWN_IMMEDIATE],
        models.EventType.SYSTEM_APPLY_UPDATE_IMMEDIATE:\
            [models.EventType.SYSTEM_SHUTDOWN,
             models.EventType.SYSTEM_SHUTDOWN_IMMEDIATE],
        models.EventType.SYSTEM_SHUTDOWN:\
            [models.EventType.SYSTEM_APPLY_UPDATE,
             models.EventType.SYSTEM_APPLY_UPDATE_IMMEDIATE,
             models.EventType.SYSTEM_CONFIG_IMMEDIATE],
        models.EventType.SYSTEM_SHUTDOWN_IMMEDIATE:\
            [models.EventType.SYSTEM_APPLY_UPDATE,
             models.EventType.SYSTEM_APPLY_UPDATE_IMMEDIATE,
             models.EventType.SYSTEM_CONFIG_IMMEDIATE],
        models.EventType.SYSTEM_CONFIG_IMMEDIATE:\
            [models.EventType.SYSTEM_SHUTDOWN,
             models.EventType.SYSTEM_SHUTDOWN_IMMEDIATE],
    }

    TZ = tz.tzutc()
    X509 = x509.X509

    NonresponsiveStates = set([
        models.SystemState.NONRESPONSIVE,
        models.SystemState.NONRESPONSIVE_NET,
        models.SystemState.NONRESPONSIVE_HOST,
        models.SystemState.NONRESPONSIVE_SHUTDOWN,
        models.SystemState.NONRESPONSIVE_SUSPENDED,
        models.SystemState.NONRESPONSIVE_CREDENTIALS,
    ])

    @classmethod
    def now(cls):
        return datetime.datetime.now(cls.TZ)

    @base.exposed
    def getEventTypes(self):
        EventTypes = models.EventTypes()
        EventTypes.event_type = list(models.EventType.objects.all())
        return EventTypes

    @base.exposed
    def getEventType(self, event_type_id):
        eventType = models.EventType.objects.get(pk=event_type_id)
        return eventType
    
    @base.exposed
    def updateEventType(self, event_type):
        """Update an event type"""

        if not event_type:
            return

        event_type.save()
        return event_type

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
    def getNetwork(self, network_id):
        network = models.Network.objects.get(pk=network_id)
        return network
    
    @base.exposed
    def getNetworks(self):
        Networks = models.Networks()
        Networks.network = list(models.Network.objects.all())
        return Networks
    
    @base.exposed
    def updateNetwork(self, network):
        """Update a network"""

        if not network:
            return

        network.save()
        return network
    
    @base.exposed
    def deleteNetwork(self, network_id):
        network = models.Network.objects.get(pk=network_id)
        network.delete()

    @base.exposed
    def getSystem(self, system_id):
        system = models.System.objects.get(pk=system_id)

        # Recalculate available updates for each trove on the system, if
        # needed.  This call honors the 24 hour cache.
        # We only want to do this if we're not running in local mode.
        if not settings.MANAGE_RBUILDER_MODELS:
            for trove in system.installed_software.all():
                self.mgr.versionMgr.set_available_updates(trove)
        return system

    @base.exposed
    def deleteSystem(self, system_id):
        system = models.System.objects.get(pk=system_id)
        system.delete()

    @base.exposed
    def getSystemByTargetSystemId(self, target_system_id):
        systems = models.System.objects.filter(
            target_system_id=target_system_id)
        if systems:
            return systems[0]
        else:
            return None

    @base.exposed
    def XXXgetSystems(self):
        Systems = models.Systems()
        qs = models.System.objects.select_related(
            'current_state', 'target', 'launching_user', 'managing_zone',
            'management_node', )
        Systems.system = list(qs)
        return Systems

    @classmethod
    def _getClassName(cls, field):
        xobj = getattr(field, '_xobj', None)
        if xobj:
            clsName = xobj.tag
        else:
            clsName = field._meta.verbose_name
        return models.modellib.type_map[clsName]

    def bulkLoad(self, cursor, baseCls, depth):
        baseTableName = baseCls._meta.db_table
        baseTablePkName = baseCls._meta.auto_field.name
        baseObjects = baseCls.objects.extra(
            select = dict(_baseId = 'inventory_tmp.res_id'),
            tables=["inventory_tmp"],
            where=["inventory_tmp.res_id = %s.%s" %
                        (baseTableName, baseTablePkName),
                   "inventory_tmp.depth = %s" % depth])
        baseObjectsMap = dict((x.pk, x) for x in baseObjects)
        valuesMap = {}
        for fk in baseCls.iterForeignKeys():
            cls = self._getClassName(fk.rel.to)
            dbTable = fk.rel.to._meta.db_table
            dbColumn = fk.rel.get_related_field().db_column
            if not dbColumn:
                dbColumn = fk.rel.field_name
            # Because this is a pure FK, we lose track of the source object,
            # so we add it as an extra select
            objects = cls.objects.extra(
                select = dict(_baseId = 'inventory_tmp.res_id'),
                tables=["inventory_tmp", baseTableName, dbTable],
                where=["inventory_tmp.res_id = %s.%s" %
                        (baseTableName, baseTablePkName),
                       "%s.%s = %s.%s" % (baseTableName, fk.column,
                            dbTable, dbColumn),
                   "inventory_tmp.depth = %s" % depth])
            if objects:
                valuesMap[fk.name] = dict((x._baseId, x) for x in objects)
        for fk in baseCls.iterAccessors(withHidden=False):
            if getattr(fk.field, 'Deferred', False):
                # XXX FIXME
                continue
            cls = self._getClassName(fk.model)
            dbTable = fk.opts.db_table
            dbColumn = fk.field.column
            objects = cls.objects.extra(
                tables=["inventory_tmp", dbTable],
                where=["inventory_tmp.res_id = %s.%s" %
                            (dbTable, dbColumn),
                   "inventory_tmp.depth = %s" % depth])
            vmKey = fk.get_accessor_name()
            valuesMap[vmKey] = vmap = {}
            # Prepare the values. Accessor values are lists
            for obj in objects:
                # k = getattr(getattr(x, fk.field.name)
                k = getattr(obj, dbColumn)
                # We're cheating a bit. We know the base object is related to
                # this object already, so we're adding it as a value. This
                # prevents another recursive bulkLoad
                revFieldName = fk.field.related.field.name
                svmap = { revFieldName : baseObjectsMap[k] }
                vmap.setdefault(k, []).append((obj, svmap))
        for m2m in baseCls.iterM2MAccessors(withHidden=False):
            cls = m2m.rel.to
            #if m2m.rel.through:
            #    cls = m2m.rel.through
            #else:
            #    cls = self._getClassName(m2m.model)
            field = m2m.m2m_field_name()
            m2mTable = m2m.m2m_db_table()
            m2mFieldFrom = getattr(m2m.rel.through, field).field.rel.field_name
            toField = m2m.rel.get_related_field().name

            # Track objects for this m2m relationship
            sql = """
                SELECT DISTINCT inventory_tmp.res_id, %s.%s
                  FROM inventory_tmp
                  JOIN %s ON (inventory_tmp.res_id = %s.%s)
                 WHERE inventory_tmp.depth = %%s
            """ % (m2mTable, toField, m2mTable, m2mTable, m2mFieldFrom)
            subobjMap = {}
            cursor.execute(sql, [ depth ])
            res = cursor.fetchall()
            for (resId, relId) in res:
                subobjMap.setdefault(relId, []).append(resId)

            sql = """
                DELETE FROM inventory_tmp WHERE depth = %s
            """
            cursor.execute(sql, [ depth + 1 ])
            sql = """
                INSERT INTO inventory_tmp (res_id, depth)
                SELECT DISTINCT %s.%s, %%s
                  FROM inventory_tmp
                  JOIN %s ON (inventory_tmp.res_id = %s.%s)
                 WHERE inventory_tmp.depth = %%s
            """ % (m2mTable, toField,
                m2mTable, m2mTable, m2mFieldFrom)
            cursor.execute(sql, [ depth + 1, depth ])

            objects, subvaluesMap = self.bulkLoad(cursor, cls, depth + 1)
            vmKey = m2m.name
            valuesMap[vmKey] = vmap = {}
            for obj in objects:
                objPk = obj.pk
                baseObjectIds = subobjMap.get(objPk, [])
                subvMap = subvaluesMap.get(objPk, {})
                for baseObjectId in baseObjectIds:
                    vmap.setdefault(baseObjectId, []).append((obj, subvMap))
        # Reassemble valuesMap to be keyed on the baseObject's pk
        retvMap = {}
        for vmKey, vhash in valuesMap.items():
            for resId, values in vhash.items():
                retvMap.setdefault(resId, {})[vmKey] = values
        return baseObjects, retvMap

    @base.exposed
    def getSystems(self, request):
        profiling = False
        if profiling:
            from django.db import settings
            settings.DEBUG = True
            t0 = time.time()
            del connection.queries[:]
        cu = connection.cursor()
        cu.execute("DELETE FROM inventory_tmp")
        # XXX we will have to change this to allow for filtering too
        sql = """
            INSERT INTO inventory_tmp (res_id, depth)
            SELECT system_id, 0 FROM inventory_system"""
        cu.execute(sql)
        baseCls = models.System
        depth = 0
        systems, valuesMap = self.bulkLoad(cu, baseCls, depth)
        ret = self.bulkSerialize(request, systems, valuesMap)
        Systems = models.Systems()
        Systems.system = ret
        if profiling:
            settings.DEBUG = False
            now = time.time()
            elapsed = now - t0
            f = file("/tmp/queries-%.2f" % now, "w")
            for q in connection.queries:
                f.write("qtime: %s s: %s\n\n" % (q['time'], q['sql'].strip()))
            f.write("PID: %d; %d queries, %.2f s\n" %
                (os.getpid(), len(connection.queries), elapsed))
        return Systems

    def bulkSerialize(self, request, objects, valuesMap):
        ret = []
        for obj in objects:
            pk = obj.pk
            ret.append(self.bulkSerializeOne(request, obj,
                valuesMap.get(pk, {})))
        return ret

    def bulkSerializeOne(self, request, obj, values):
        ret = obj.serialize(request, values=values)
        return ret
    
    @base.exposed
    def getInventorySystems(self):
        systems = models.Systems()
        systems.system = \
            models.System.objects.filter(system_type__infrastructure=False)
        return systems

    @base.exposed
    def getImageImportMetadataDescriptor(self):
        importDescriptorFile = open(self.cfg.metadataDescriptorPath)
        importDescriptorData = importDescriptorFile.read()
        importDescriptorFile.close()
        return importDescriptorData

    @base.exposed
    def getInfrastructureSystems(self):
        systems = models.Systems()
        systems.system = \
            models.System.objects.filter(system_type__infrastructure=True)
        return systems

    @base.exposed
    def getManagementInterface(self, management_interface_id):
        managementInterface = models.ManagementInterface.objects.get(pk=management_interface_id)
        return managementInterface

    @base.exposed
    def getManagementInterfaces(self):
        ManagementInterfaces = models.ManagementInterfaces()
        ManagementInterfaces.management_interface = list(models.ManagementInterface.objects.all())
        return ManagementInterfaces
    
    @base.exposed
    def updateManagementInterface(self, management_interface):
        """Update a management interface"""

        if not management_interface:
            return

        management_interface.save()
        return management_interface

    @base.exposed
    def getManagementNode(self, management_node_id):
        managementNode = models.ManagementNode.objects.get(pk=management_node_id)
        return managementNode

    @base.exposed
    def getManagementNodes(self):
        ManagementNodes = models.ManagementNodes()
        ManagementNodes.management_node = list(models.ManagementNode.objects.all())
        return ManagementNodes
    
    @base.exposed
    def addManagementNode(self, managementNode):
        """Add a management node to the inventory"""
        
        if not managementNode:
            return
        
        managementNode.save()

        self.setSystemState(managementNode)
        #TO-DO Need to add the JID to the models.ManagementNode object
        return managementNode

    @base.exposed
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

    @base.exposed
    def getManagementNodeForZone(self, zone_id, management_node_id):
        zone = models.Zone.objects.get(pk=zone_id)
        managementNode = models.ManagementNode.objects.get(zone=zone, pk=management_node_id)
        return managementNode
    
    @base.exposed
    def addManagementNodeForZone(self, zone_id, managementNode):
        """Add a management node to the inventory"""
        
        if not managementNode:
            return

        zone = models.Zone.objects.get(pk=zone_id)
        managementNode.zone = zone;
        managementNode.save()

        self.setSystemState(managementNode)
        #TO-DO Need to add the JID to the models.ManagementNode object
        return managementNode

    @base.exposed
    def getManagementNodesForZone(self, zone_id):
        zone = models.Zone.objects.get(pk=zone_id)
        ManagementNodes = models.ManagementNodes()
        ManagementNodes.management_node = list(models.ManagementNode.objects.filter(zone=zone).all())
        return ManagementNodes

    @base.exposed
    def getSystemType(self, system_type_id):
        systemType = models.SystemType.objects.get(pk=system_type_id)
        return systemType

    @base.exposed
    def getSystemTypes(self):
        SystemTypes = models.SystemTypes()
        SystemTypes.system_type = list(models.SystemType.objects.all())
        return SystemTypes
    
    @base.exposed
    def updateSystemType(self, system_type):
        """Update a system type"""

        if not system_type:
            return

        system_type.save()
        return system_type
    
    @base.exposed
    def getSystemTypeSystems(self, system_type_id):
        system_type = self.getSystemType(system_type_id)
        Systems = models.Systems()
        Systems.system = system_type.systems.all()
        return Systems
    
    @base.exposed
    def getWindowsBuildServiceSystemType(self):
        "Return the zone for this rBuilder"
        return models.SystemType.objects.get(name=models.SystemType.INFRASTRUCTURE_WINDOWS_BUILD_NODE)
    
    @base.exposed
    def getWindowsBuildServiceNodes(self):
        nodes = []
        try:
            system_type = self.getWindowsBuildServiceSystemType()
            systems = self.getSystemTypeSystems(system_type.system_type_id)
            nodes = systems and systems.system or []
        except ObjectDoesNotExist:
            pass
        
        return nodes
    
    @base.exposed
    def addWindowsBuildService(self, name, description, network_address):
        log.info("Adding Windows Build Service with name '%s', description '%s', and network address '%s'" % (name, description, network_address))
        system = models.System(name=name, description=description)
        system.current_state = self.mgr.sysMgr.systemState(
            models.SystemState.UNMANAGED)
        system.managing_zone = self.getLocalZone()
        system.management_interface = models.ManagementInterface.objects.get(pk=1)
        system.system_type = self.getWindowsBuildServiceSystemType()
        system.save()

        network = models.Network()
        network.dns_name = network_address
        network.system = system
        network.save()
        
        return system

    @base.exposed
    def getSystemState(self, system_state_id):
        systemState = models.SystemState.objects.get(pk=system_state_id)
        return systemState

    @base.exposed
    def getSystemStates(self):
        SystemStates = models.SystemStates()
        SystemStates.system_state = list(models.SystemState.objects.all())
        return SystemStates

    @classmethod
    def systemState(cls, stateName):
        return models.SystemState.objects.get(name = stateName)

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

    @base.exposed
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
    def addSystem(self, system, generateCertificates=False,
                  withManagementInterfaceDetection=True):
        '''Add a new system to inventory'''

        if not system:
            return

        try:
            if system.system_type.name == models.SystemType.INFRASTRUCTURE_MANAGEMENT_NODE:
                return self.addManagementNode(system)
        except ObjectDoesNotExist:
            pass # will default later on

        # add the system
        system.save()

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

        return system

    def mergeSystems(self, system):
        if not system.event_uuid:
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

        models.System.objects.copyFields(system, other, withReadOnly=True)

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

    def setSystemState(self, system, withManagementInterfaceDetection=True):
        if system.oldModel is None:
            self.log_system(system, models.SystemLogEntry.ADDED)
        registeredState = self.systemState(models.SystemState.REGISTERED)
        onlineState = self.systemState(models.SystemState.RESPONSIVE)
        if system.isNewRegistration:
            system.registration_date = self.now()
            system.current_state = registeredState
            system.save()
            if system.oldModel is None:
                # We really see this system the first time with its proper
                # uuids. We'll assume it's been registered with rpath-register
                self.log_system(system, models.SystemLogEntry.REGISTERED)
            if not system.system_type.infrastructure:
                # Schedule a poll event in the future
                self.scheduleSystemPollEvent(system)
                # And schedule one immediately
                self.scheduleSystemPollNowEvent(system)
        elif system.isRegistered:
            # See if a new poll is required
            if self.needsNewSynchronization(system):
                system.current_state = registeredState
                self.scheduleSystemPollNowEvent(system)
                system.save()
            # Already registered and no need to re-syncrhonize, if the
            # old state was online, and the new state is registered, we must
            # be coming in through rpath-tools, so preserve the online state.
            elif (system.oldModel is not None and 
                    system.oldModel.current_state.system_state_id == \
                    onlineState.system_state_id and
                    system.current_state.system_state_id == \
                    registeredState.system_state_id):
                system.current_state = onlineState
                system.save()
            elif system.current_state == registeredState:
                self.scheduleSystemPollNowEvent(system)
        elif withManagementInterfaceDetection:
            # Need to dectect the management interface on the system
            self.scheduleSystemDetectMgmtInterfaceEvent(system)

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
        system.ssl_client_certificate = crt.x509.as_pem()
        system.ssl_client_key = crt.pkey.as_pem(None)
        system.save()

    @base.exposed
    def updateSystem(self, system):
        # XXX This will have to change and be done in modellib, most likely.
        if self.checkAndApplyShutdown(system):
            return
        self.checkInstalledSoftware(system)
        last_job = getattr(system, 'lastJob', None)
        if last_job and last_job.job_state.name == models.JobState.COMPLETED:
            # This will update the system state as a side-effect
            self.addSystem(system, generateCertificates=False,
                withManagementInterfaceDetection=False)
        self.setSystemStateFromJob(system)
        system.save()

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

    def getNextSystemState(self, system, job):
        # Return None if the state hasn't changed
        jobStateName = job.job_state.name
        eventTypeName = job.event_type.name
        if jobStateName == models.JobState.COMPLETED:
            if eventTypeName in self.RegistrationEvents:
                # We don't trust that a registration action did anything, we
                # won't transition to REGISTERED, rpath-register should be
                # responsible with that
                return None
            if eventTypeName in self.PollEvents or \
                    eventTypeName in self.SystemUpdateEvents:
                return models.SystemState.RESPONSIVE
            if eventTypeName in self.ManagementInterfaceEvents:
                # Management interface detection finished, need to schedule a
                # registration event now.
                wmiIfaceId = models.Cache.get(models.ManagementInterface,
                    name=models.ManagementInterface.WMI).pk
                # But if it's a WMI system and we have no credentials, skip
                # directly to UNMANAGED_CREDENTIALS_REQUIRED (RBL-7439)
                if system.management_interface_id == wmiIfaceId:
                    if not system.credentials:
                        return models.SystemState.UNMANAGED_CREDENTIALS_REQUIRED
                self.scheduleSystemRegistrationEvent(system)
                return None
            else:
                # Add more processing here if needed
                return None
        if jobStateName == models.JobState.FAILED:
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
            if eventTypeName not in self.PollEvents and \
                    eventTypeName not in self.SystemUpdateEvents:
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

    @base.exposed
    def addLaunchedSystem(self, system, dnsName=None, targetName=None,
            targetType=None):
        target = self.lookupTarget(targetType=targetType,
            targetName=targetName)
        system.target = target
        if system.managing_zone_id is None:
            system.managing_zone = self.getLocalZone()
        # For bayonet, we only launch in the local zone
        oldModel, system = models.System.objects.load_or_create(system,
            withReadOnly=True)

        system.launching_user = self.user
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
            network = models.Network(dns_name=dnsName,
                            active=True)
            system.networks.add(network)
        else:
            self.scheduleLaunchWaitForNetworkEvent(system)
        self.log_system(system, "System launched in target %s (%s)" %
            (target.targetname, target.targettype))
        self.addSystem(system)
        return system

    def _getCredentialsForUser(self, target):
        tucs = rbuildermodels.TargetUserCredentials.objects.filter(
            targetid=target, userid=self.user)
        for tuc in tucs:
            return tuc.targetcredentialsid
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
        if managedSystem.launching_user.userid == self.user.userid:
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

    @base.exposed
    def getSystemCredentials(self, system_id):
        system = models.System.objects.get(pk=system_id)
        systemCreds = {}
        if system.management_interface:
            if system.management_interface.name == 'wmi':
                if system.credentials is None:
                    systemCreds = {}
                else:
                    systemCreds = self.unmarshalCredentials(system.credentials)
            else:
                systemCreds = dict(
                    ssl_client_certificate=system.ssl_client_certificate,
                    ssl_client_key=system.ssl_client_key)

        return self._getCredentialsModel(system, systemCreds)

    @base.exposed
    def addSystemCredentials(self, system_id, credentials):
        system = models.System.objects.get(pk=system_id)
        if system.management_interface:
            if system.management_interface.name == 'wmi':
                systemCreds = self.marshalCredentials(credentials)
                system.credentials = systemCreds
            else:
                if credentials.has_key('ssl_client_certificate'):
                    system.ssl_client_certificate = \
                        credentials['ssl_client_certificate']
                if credentials.has_key('ssl_client_key'):
                    system.ssl_client_key = credentials['ssl_client_key']

        system.save()
        # Schedule a system registration event after adding/updating
        # credentials.
        self.scheduleSystemRegistrationEvent(system)
        return self._getCredentialsModel(system, credentials)
    
    @base.exposed
    def getSystemConfigurationDescriptor(self, system_id):
        system = models.System.objects.get(pk=system_id)
        return self.mgr.getConfigurationDescriptor(system)
    
    @base.exposed
    def getSystemConfiguration(self, system_id):
        system = models.System.objects.get(pk=system_id)
        if system.configuration is None:
            systemConfig = {}
        else:
            systemConfig = self.unmarshalConfiguration(system.configuration)
        return self._getConfigurationModel(system, systemConfig)

    @base.exposed
    def addSystemConfiguration(self, system_id, configuration):
        system = models.System.objects.get(pk=system_id)
        systemConfig = self.marshalConfiguration(configuration)
        system.configuration = systemConfig
        system.save()
        self.scheduleSystemConfigurationEvent(system, configuration)
        return self._getConfigurationModel(system, configuration)
    
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
        SystemEvents.system_event = list(models.SystemEvent.objects.all())
        return SystemEvents

    @base.exposed
    def getSystemSystemEvents(self, system_id):
        system = models.System.objects.get(pk=system_id)
        events = models.SystemEvent.objects.filter(system=system)
        system_events = models.SystemEvents()
        system_events.system_event = list(events)
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

    def checkEventCompatibility(self, event):
        runningJobs = event.system.jobs.filter(job_state__name=models.JobState.RUNNING) 
        runningEventTypes = [j.event_type.name for j in runningJobs]

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
            except errors.IncompatibleEvent, e:
                log.error(str(e))
                raise e

        log.info("Dispatching %s event (id %d, enabled %s) for system %s (id %d)" % \
            (event.event_type.name, event.system_event_id, event.time_enabled, 
            event.system.name, event.system.system_id))
        
        self._dispatchSystemEvent(event)

        # cleanup now that the event has been processed
        self.cleanupSystemEvent(event)

        # create the next event if needed
        if event.event_type.name == models.EventType.SYSTEM_POLL:
            self.scheduleSystemPollEvent(event.system)
        else:
            log.debug("%s events do not trigger a new event creation" % event.event_type.name)

    @classmethod
    @base.exposed
    def getSystemManagementInterfaceName(cls, system):
        if system.management_interface_id is None:
            # Assume CIM
            return models.ManagementInterface.CIM
        return system.management_interface.name

    def _computeDispatcherMethodParams(self, repClient, system, destination, eventUuid, requiredNetwork):
        methodMap = {
            models.ManagementInterface.CIM : self._cimParams,
            models.ManagementInterface.WMI : self._wmiParams,
        }
        mgmtInterfaceName = self.getSystemManagementInterfaceName(system)
        method = methodMap[mgmtInterfaceName]
        return method(repClient, system, destination, eventUuid, requiredNetwork)

    def _cimParams(self, repClient, system, destination, eventUuid, requiredNetwork):
        if system.target_id is not None:
            targetName = system.target.targetname
            targetType = system.target.targettype
        else:
            targetName = None
            targetType = None
        cimParams = repClient.CimParams(host=destination,
            port=system.agent_port,
            eventUuid=eventUuid,
            clientCert=system.ssl_client_certificate,
            clientKey=system.ssl_client_key,
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
            requiredNetwork = (network.required and destination) or None
        else:
            destination = None
            requiredNetwork = None

        eventUuid = str(uuid.uuid4())
        zone = event.system.managing_zone.name
        params = self._computeDispatcherMethodParams(repClient, event.system,
            destination, eventUuid, requiredNetwork)
        resultsLocation = repClient.ResultsLocation(
            path = "/api/inventory/systems/%d" % event.system.pk,
            port = 80)

        mgmtInterfaceName = self.getSystemManagementInterfaceName(event.system)

        if eventType in self.RegistrationEvents:
            method = getattr(repClient, "register_" + mgmtInterfaceName)
            self._runSystemEvent(event, method, params,
                resultsLocation, zone=zone)
        elif eventType in self.PollEvents:
            method = getattr(repClient, "poll_" + mgmtInterfaceName)
            self._runSystemEvent(event, method,
                params, resultsLocation, zone=zone)
        elif eventType in self.SystemUpdateEvents:
            data = cPickle.loads(event.event_data)
            method = getattr(repClient, "update_" + mgmtInterfaceName)
            self._runSystemEvent(event, method, params,
                resultsLocation, zone=zone, sources=data)
        elif eventType in self.SystemConfigurationEvents:
            data = event.event_data
            method = getattr(repClient, "configuration_" + mgmtInterfaceName)
            self._runSystemEvent(event, method, params,
                resultsLocation, zone=zone, configuration=data)
        elif eventType in self.ShutdownEvents:
            method = getattr(repClient, "shutdown_" + mgmtInterfaceName)
            self._runSystemEvent(event, method,
                params, resultsLocation, zone=zone)
        elif eventType in self.LaunchWaitForNetworkEvents:
            self._runSystemEvent(event, repClient.launchWaitForNetwork,
                params, resultsLocation)
        elif eventType in self.ManagementInterfaceEvents:
            params = self.getManagementInterfaceParams(repClient, destination)
            params.eventUuid = eventUuid
            self._runSystemEvent(event, repClient.detectMgmtInterface,
                params, resultsLocation=resultsLocation, zone=zone)
        else:
            log.error("Unknown event type %s" % eventType)
            raise errors.UnknownEventType(eventType=eventType)

    def getManagementInterfaceParams(self, repClient, destination):
        # Enumerate all management interfaces
        ifaces = models.Cache.all(models.ManagementInterface)
        interfacesList = [ dict(interfaceHref=x.get_absolute_url(), port=x.port)
            for x in ifaces ]
        # Order the list so we detect wmi before cim (luckily we can sort by
        # port number)
        interfacesList.sort(key=lambda x: x['port'])
        params = repClient.ManagementInterfaceParams(host=destination,
            interfacesList=interfacesList)
        return params

    @base.exposed
    def extractNetworkToUse(self, system):
        if hasattr(system.networks, 'all'):
            networks = system.networks.all()
        else:
            networks = system.networks.network
            for net in networks:
                net.required = (net.required == 'true' or net.required == 'True')
                net.active = (net.active == 'true' or net.active == 'True')

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

    def needsNewSynchronization(self, system):
        """
        Relies on the presence of oldModel.  Look to see if any pertinent
        fields have changed that would cause a new synchronization to be
        needed.
        """
        oldModel = getattr(system, 'oldModel', None)
        if not oldModel:
            return False

        oldNetwork = self.extractNetworkToUse(oldModel)
        if not oldNetwork:
            return False
        newNetwork = self.extractNetworkToUse(system)
        
        oldIp = oldNetwork.ip_address or oldNetwork.dns_name
        newIp = newNetwork.ip_address or newNetwork.dns_name
        if oldIp != newIp:
            return True

        oldServerCert = getattr(oldModel, 'ssl_server_certificate', None)
        if not oldServerCert:
            return False

        if oldServerCert != system.ssl_server_certificate:
            return True

    @classmethod
    def _runSystemEvent(cls, event, method, params, resultsLocation=None,
            **kwargs):
        zone = kwargs.pop('zone', None)
        systemName = event.system.name
        eventType = event.event_type.name
        if hasattr(params, 'eventUuid'):
            eventUuid = params.eventUuid
        else:
            eventUuid = kwargs.get('eventUuid')
        log.info("System %s (%s), task type '%s' launching" %
            (systemName, params.host, eventType))
        try:
            uuid, job = method(params, resultsLocation, zone=zone, **kwargs)
        except Exception, e:
            tb = sys.exc_info()[2]
            traceback.print_tb(tb)
            log.error("System %s (%s), task type '%s' failed: %s" %
                (systemName, params.host, eventType, str(e)))
            return None, None

        log.info("System %s (%s), task %s (%s) in progress" %
            (systemName, params.host, uuid, eventType))
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
        return self._scheduleEvent(system, models.EventType.SYSTEM_POLL)

    @base.exposed
    def scheduleSystemPollNowEvent(self, system):
        '''Schedule an event for the system to be polled now'''
        # happens on demand, so enable now
        return self._scheduleEvent(system,
            models.EventType.SYSTEM_POLL_IMMEDIATE,
            enableTime=self.now())

    @base.exposed
    def scheduleSystemRegistrationEvent(self, system):
        '''Schedule an event for the system to be registered'''
        # registration events happen on demand, so enable now
        return self._scheduleEvent(system,
            models.EventType.SYSTEM_REGISTRATION,
            enableTime=self.now())

    @base.exposed
    def scheduleSystemApplyUpdateEvent(self, system, sources):
        '''Schedule an event for the system to be updated'''
        return self._scheduleEvent(system,
            models.EventType.SYSTEM_APPLY_UPDATE_IMMEDIATE,
            eventData=sources)

    @base.exposed
    def scheduleSystemShutdownEvent(self, system):
        '''Schedule an event to shutdown the system.'''
        return self._scheduleEvent(system,
            models.EventType.SYSTEM_SHUTDOWN_IMMEDIATE)

    @base.exposed
    def scheduleLaunchWaitForNetworkEvent(self, system):
        """
        Schedule an event that either waits for the system's IP address to
        become available, or sees that the system has registered via
        rpath-tools.
        """
        return self._scheduleEvent(system,
            models.EventType.LAUNCH_WAIT_FOR_NETWORK,
            enableTime=self.now())

    @base.exposed
    def scheduleSystemDetectMgmtInterfaceEvent(self, system):
        """
        Schedule an immediate event that detects the management interface
        on the system.
        """
        return self._scheduleEvent(system,
            models.EventType.SYSTEM_DETECT_MANAGEMENT_INTERFACE_IMMEDIATE,
            enableTime=self.now())

    @base.exposed
    def scheduleSystemConfigurationEvent(self, system, configuration):
        '''Schedule an event for the system to be configured'''
        # registration events happen on demand, so enable now
        configData = self.configDictToXml(configuration)
        return self._scheduleEvent(system,
            models.EventType.SYSTEM_CONFIG_IMMEDIATE,
            enableTime=self.now(),
            eventData=configData)

    @classmethod
    def configDictToXml(cls, configuration):
        obj = Configuration(**configuration)
        return xobj.toxml(obj, prettyPrint=False, xml_declaration=False)

    def _scheduleEvent(self, system, eventType, enableTime=None,
            eventData=None):
        eventTypeObject = self.eventType(eventType)
        return self.createSystemEvent(system, eventTypeObject, enableTime=enableTime,
            eventData=eventData)

    @base.exposed
    def createSystemEvent(self, system, eventType, enableTime=None,
                          eventData=None):
        event = None
        # do not create events for systems that we cannot possibly contact
        if self.getSystemHasHostInfo(system) or \
                eventType.name in self.LaunchWaitForNetworkEvents:
            if not enableTime:
                enableTime = self.now() + datetime.timedelta(
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
            target_system_id=targetSystemId,
            managing_zone = self.getLocalZone())
        if created:
            self.log_system(system, "System added as part of target %s (%s)" %
                (target.targetname, target.targettype))
            # Having nothing else available, we copy the target's name
            system.name = targetSystem.instanceName
            system.description = targetSystem.instanceDescription
        system.target_system_name = targetSystem.instanceName
        system.target_system_description = targetSystem.instanceDescription
        self._addTargetSystemNetwork(system, target, targetSystem)
        system.target_system_state = targetSystem.state
        system.save()
        self._setSystemTargetCredentials(system, target,
            targetSystem.userNames)
        if created:
            t1 = time.time()
            self.scheduleSystemDetectMgmtInterfaceEvent(system)
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
            if system.target_system_id is None:
                # Systems without a target_system_id are ignored
                continue
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

    @classmethod
    def _getField(cls, system, fieldName):
        fieldVal = getattr(system, fieldName)
        if fieldVal is not None:
            return fieldVal.getText()
        return None

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
            instanceName = self._getField(tsys, 'instanceName')
            instanceDescription = self._getField(tsys, 'instanceDescription')
            dnsName = self._getField(tsys, 'dnsName')
            state = self._getField(tsys, 'state') or 'unknown'
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
        systemsLog.system_log_entry = list(systemLogEntries)
        return systemsLog

class Configuration(object):
    _xobj = xobj.XObjMetadata(
        tag = 'configuration')
    def __init__(self, **kwargs):
        self.__dict__ = kwargs
