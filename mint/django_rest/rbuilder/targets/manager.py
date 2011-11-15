#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import json

from django.db import connection
from django.db.models import Q

from mint.lib import data as mintdata
from mint.django_rest import timeutils
from mint.django_rest.rbuilder import errors, modellib
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.targets import models
from mint.django_rest.rbuilder.inventory import zones
from mint.django_rest.rbuilder.jobs import models as jobsmodels
from mint.django_rest.rbuilder.querysets import models as qsmodels

from smartform import descriptor

import logging
log = logging.getLogger(__name__)

class CatalogServiceHelper(object):
    _driverCache = {}

    @classmethod
    def getDriverClass(cls, targetType):
        drvClass = cls._driverCache.get(targetType.name)
        if drvClass is not None:
            return drvClass
        driverName = targetType.name
        # xen enterprise is a one-off
        if driverName == 'xen-enterprise':
            driverName = 'xenent'

        moduleName = "catalogService.rest.drivers.%s" % driverName
        DriverClass = __import__(moduleName, {}, {}, '.driver').driver
        cls._driverCache[targetType.name] = DriverClass
        return DriverClass

class TargetsManager(basemanager.BaseManager, CatalogServiceHelper):
    @exposed
    def authTargetJob(self, job):
        requireAdmin = set(self.mgr.sysMgr.eventType(x).job_type_id
            for x in [ jobsmodels.EventType.TARGET_CREATE, jobsmodels.EventType.TARGET_CONFIGURE, ])
        if job.job_type_id in requireAdmin and not self.user.is_admin:
            raise errors.PermissionDenied()

    @exposed
    def getTargetById(self, target_id):
        return models.Target.objects.get(pk=target_id)

    @exposed
    def getTargets(self):
        Targets = models.Targets()
        Targets.target = models.Target.objects.order_by('target_id')
        return Targets

    @exposed
    def getTargetConfiguration(self, target):
        targetConfig = dict()
        for obj in models.TargetData.objects.filter(target=target):
            targetConfig[obj.name] = self._stripUnicode(json.loads(obj.value))
        targetConfig['zone'] = self.getTargetZone(target).name
        targetConfig['name'] = target.name
        targetConfig['description'] = target.description
        return targetConfig

    def _getTargetCredentialsForCurrentUser(self, target):
        userId = self.auth.userId
        creds = models.TargetCredentials.objects.filter(
            target_user_credentials__target=target,
            target_user_credentials__user__user_id=userId)
        if not creds:
            return None
        return creds[0]

    @exposed
    def getTargetCredentialsForCurrentUser(self, target):
        creds = self._getTargetCredentialsForCurrentUser(target)
        if creds is None:
            return None
        return mintdata.unmarshalTargetUserCredentials(creds.credentials)

    @exposed
    def getModelTargetCredentialsForCurrentUser(self, targetId):
        target = self.getTargetById(targetId)
        creds = self.getTargetCredentialsForCurrentUser(target)
        if not creds:
            raise errors.ResourceNotFound()
        credModel= models.TargetUserCredentialsModel(user=self.user)
        credModel.setCredentials(creds)
        return credModel

    @exposed
    def deleteTargetUserCredentialsForCurrentUser(self, targetId):
        target = self.getTargetById(targetId)
        models.TargetUserCredentials.objects.filter(target=target,
            user__user_id=self.auth.userId).delete()
        self._pruneTargetCredentials()
        credModel = models.TargetUserCredentialsModel(user=self.user)
        return credModel

    @exposed
    def setTargetUserCredentials(self, target, credentials):
        data = mintdata.marshalTargetUserCredentials(credentials)
        tcred, created = models.TargetCredentials.objects.get_or_create(
            credentials=data)
        oldTUCreds = models.TargetUserCredentials.objects.filter(target=target,
            user__user_id=self.auth.userId)
        if oldTUCreds:
            oldTUCreds = oldTUCreds[0]
            if oldTUCreds.target_credentials_id == tcred.target_credentials_id:
                return oldTUCreds
            # Remove old credentials if present
            oldTUCreds.delete()
        user = self.mgr.usersMgr.getUser(self.auth.userId)
        tucreds = models.TargetUserCredentials(target=target, user=user,
            target_credentials=tcred)
        tucreds.save()
        self._pruneTargetCredentials()
        self.recomputeTargetDeployableImages()
        return tucreds

    def _pruneTargetCredentials(self):
        cu = connection.cursor()
        cu.execute("""
            DELETE FROM TargetCredentials
             WHERE targetCredentialsId not in (
                   SELECT targetCredentialsId
                     FROM TargetUserCredentials)
        """)

    @exposed
    def getTargetZone(self, target):
        return modellib.Cache.get(zones.Zone, pk=target.zone_id)

    @classmethod
    def _stripUnicode(cls, value):
        if hasattr(value, 'encode'):
            return value.encode('ascii')
        return value

    @exposed
    def addTarget(self, targetSrc, configured=False, forUser=None):
        if configured:
            state = 0
        else:
            state = 1
        zone = modellib.Cache.get(zones.Zone, name=targetSrc.zone_name)
        targetType = self.mgr.getTargetTypeByName(targetSrc.target_type_name)
        target = models.Target(name=targetSrc.name,
            description=targetSrc.description,
            target_type=targetType,
            zone=zone,
            state=state)
        target.save()
        self.mgr.retagQuerySetsByType('target', forUser)
        return target

    @exposed
    def createTarget(self, targetType, targetName, targetData):
        targetData.pop('name', None)
        description = targetData.get('description', targetName)
        zoneName = targetData.pop('zone')
        zone = modellib.Cache.get(zones.Zone, name=zoneName)
        target = models.Target(name=targetName, description=description,
            target_type=targetType, zone=zone,
            state=models.Target.States.OPERATIONAL)
        target.save()
        self._setTargetData(target, targetData)
        self._addTargetQuerySet(target)
        self.mgr.retagQuerySetsByType('target', for_user=None)
        return target

    def _setTargetData(self, target, targetData):
        for k, v in targetData.iteritems():
            v = json.dumps(v)
            td = models.TargetData(target=target, name=k, value=v)
            td.save()

    @exposed
    def updateTargetConfiguration(self, target, targetName, targetData):
        targetData.pop('name', None)
        description = targetData.get('description', targetName)
        zoneName = targetData.pop('zone')
        zone = modellib.Cache.get(zones.Zone, name=zoneName)
        target.name = targetName
        target.description = description
        target.zone = zone
        target.state = models.Target.States.OPERATIONAL
        target.save()
        models.TargetData.objects.filter(target=target).delete()
        self._setTargetData(target, targetData)
        self._addTargetQuerySet(target)
        self.mgr.retagQuerySetsByType('target', for_user=None)
        return target

    def _addTargetQuerySet(self, target):
        feField = 'target.target_id'
        feOperator = 'EQUAL'
        feValue = target.target_id

        fe, created = qsmodels.FilterEntry.objects.get_or_create(field=feField,
            operator=feOperator, value=feValue)

        if not created:
            # Delete the old query set
            qsmodels.QuerySet.objects.filter(
                filter_entries__filter_entry_id=fe.filter_entry_id,
                resource_type='system').delete()

        querySetName = "All %s systems (%s)" % (target.name,
            target.target_type.name)
        qs, created = qsmodels.QuerySet.objects.get_or_create(name=querySetName,
            description=querySetName, resource_type='system')
        qs.filter_entries.add(fe)

    @exposed
    def updateTarget(self, target_id, target):
        target.save()
        return target

    @exposed
    def deleteTarget(self, target_id):
        target = models.Target.objects.get(pk=target_id)
        target.delete()

    @exposed
    def getDescriptorTargetCreation(self):
        descr = descriptor.ConfigurationDescriptor()
        descr.setRootElement('descriptor_data')
        descr.setDisplayName("Create target")
        descr.addDescription("Create target")
        descr.addDataField('name',
                descriptions='Target Name',
                type='str',
                required=True)
        descr.addDataField('description',
                descriptions='Target Description',
                type='str',
                required=True)

        allTypes = sorted(modellib.Cache.all(models.TargetType),
            key=lambda x: x.target_type_id)
        typeList = [ (x.name, x.description)
            for x in allTypes ]
        typeList = [ descr.ValueWithDescription(n, descriptions=d)
            for (n, d) in typeList ]
        descr.addDataField('target_type_name',
            descriptions = "Target Type",
            type = typeList,
            required=True)

        allZones = sorted(modellib.Cache.all(zones.Zone),
            key=lambda x: x.zone_id)
        zoneList = [ (x.name, x.description)
            for x in allZones ]
        zoneList = [ descr.ValueWithDescription(n, descriptions=d)
            for (n, d) in zoneList ]
        descr.addDataField('zone_name',
            descriptions = "Zone",
            type = zoneList,
            required=True)

        return descr

    @exposed
    def getDescriptorConfigureCredentials(self, target_id):
        target = self.getTargetById(target_id)
        DriverClass = self.getDriverClass(target.target_type)
        descr = descriptor.ConfigurationDescriptor(
            fromStream=DriverClass.credentialsDescriptorXmlData)
        descr.setRootElement("descriptor_data")
        return descr

    @exposed
    def getDescriptorRefreshImages(self, target_id):
        # This will validate the target
        self.getTargetById(target_id)
        descr = descriptor.ConfigurationDescriptor()
        descr.setRootElement('descriptor_data')
        descr.setDisplayName("Refresh images")
        descr.addDescription("Refresh images")
        return descr

    @exposed
    def getDescriptorRefreshSystems(self, target_id):
        # This will validate the target
        self.getTargetById(target_id)
        descr = descriptor.ConfigurationDescriptor()
        descr.setRootElement('descriptor_data')
        descr.setDisplayName("Refresh systems")
        descr.addDescription("Refresh systems")
        return descr

    @exposed
    def getDescriptorLaunchSystem(self, targetId, buildFileId):
        return self._getDescriptorFromCatalogService(targetId, buildFileId,
            'systemLaunchDescriptor')

    @exposed
    def getDescriptorDeployImage(self, targetId, buildFileId):
        return self._getDescriptorFromCatalogService(targetId, buildFileId,
            'imageDeploymentDescriptor')

    def _getDescriptorFromCatalogService(self, targetId, buildFileId,
                rmakeMethodName):
        repClient = self.mgr.repeaterMgr.repeaterClient
        if repClient is None:
            log.info("Failed loading repeater client, expected in local mode only")
            return
        target = self.getTargetById(targetId)
        targetConfiguration = self._buildTargetConfigurationFromDb(repClient, target)
        targetUserCredentials = self._buildTargetCredentialsFromDb(repClient, target)
        zone = self.getTargetZone(target)
        repClient.targets.configure(zone.name, targetConfiguration,
            targetUserCredentials)
        method = getattr(repClient.targets, rmakeMethodName)
        uuid, job = method()
        job = self.mgr.waitForRmakeJob(uuid, interval=.1)
        if not job.status.final:
            raise Exception("Final state not reached")
        if job.status.failed:
            raise errors.RbuilderError(msg=job.status.text,
                traceback=job.status.detail)
        descrXml = job.data.data
        descr = descriptor.ConfigurationDescriptor(fromStream=descrXml)
        descr.setRootElement("descriptor_data")
        # Fill in imageId
        field = descr.getDataField('imageId')
        field.set_default([str(buildFileId)])
        return descr

    def _buildTargetConfigurationFromDb(self, cli, target):
        targetData = self.mgr.getTargetConfiguration(target)
        targetTypeName = modellib.Cache.get(models.TargetType,
            pk=target.target_type_id).name
        targetConfiguration = cli.targets.TargetConfiguration(
            targetTypeName, target.name, targetData.get('alias'),
            targetData)
        return targetConfiguration

    def _buildTargetCredentialsFromDb(self, cli, target):
        creds = self.mgr.getTargetCredentialsForCurrentUser(target)
        if creds is None:
            raise errors.InvalidData()
        return self._buildTargetCredentials(cli, creds)

    def _buildTargetCredentials(self, cli, creds):
        userCredentials = cli.targets.TargetUserCredentials(
            credentials=creds,
            rbUser=self.user.user_name,
            rbUserId=self.user.user_id,
            isAdmin=self.user.is_admin)
        return userCredentials

    @exposed
    def addTargetImage(self, target, image):
        creds = self._getTargetCredentialsForCurrentUser(target)
        if creds is None:
            raise errors.InvalidData()
        credsId = creds.target_credentials_id

        timg = self._image(target, image)
        timg.save()

        models.TargetImageCredentials.objects.create(target_image=timg,
            target_credentials_id=credsId)
        self.recomputeTargetDeployableImages()
        return timg

    @exposed
    def updateTargetImages(self, target, images):
        creds = self._getTargetCredentialsForCurrentUser(target)
        if creds is None:
            raise errors.InvalidData()
        credsId = creds.target_credentials_id
        cu = connection.cursor()
        cu.execute("""
            CREATE TEMPORARY TABLE tmp_target_image (
                name TEXT,
                description TEXT,
                target_internal_id TEXT,
                rbuilder_image_id TEXT
            )
        """)
        query = """
            INSERT INTO tmp_target_image
                (name, description, target_internal_id, rbuilder_image_id)
            VALUES (%s, %s, %s, %s)
        """
        timgs = [ self._image(target, x) for x in images ]
        # Eliminate dupes
        timgMap = dict((x.target_internal_id, x) for x in timgs)
        params = [ (x.name, x.description, x.target_internal_id, x.rbuilder_image_id)
            for x in timgMap.values() ]
        cu.executemany(query, params)
        # Retrieve images to be updated
        query = """
            SELECT ti.target_image_id, ti.target_internal_id
              FROM tmp_target_image AS tmpti
              JOIN target_image AS ti USING (target_internal_id)
             WHERE ti.target_id = %s
               AND (ti.name != tmpti.name
                   OR ti.description != tmpti.description
                   OR NOT ((ti.rbuilder_image_id IS NULL AND tmpti.rbuilder_image_id IS NULL)
                     OR ti.rbuilder_image_id = tmpti.rbuilder_image_id))
        """
        cu.execute(query, [ target.target_id ])
        toUpdate = cu.fetchall()
        now = self.mgr.sysMgr.now()
        for targetImageId, targetInternalId in toUpdate:
            model = models.TargetImage.objects.get(target_image_id=targetImageId)
            src = timgMap[targetInternalId]
            model.name = src.name
            model.description = src.description
            model.rbuilder_image_id = src.rbuilder_image_id
            model.modified_date = now
            model.save()
        # Insert all new images
        query = """
            INSERT INTO target_image
                (target_id, name, description, target_internal_id, rbuilder_image_id)
            SELECT %s, name, description, target_internal_id, rbuilder_image_id
              FROM tmp_target_image AS tti
             WHERE target_internal_id NOT IN
               (SELECT target_internal_id FROM target_image WHERE target_id=%s)
        """
        cu.execute(query, [ target.target_id, target.target_id ])
        # Relink images to target credentials
        # First, remove the ones not in this list
        query = """
            DELETE FROM target_image_credentials
             WHERE target_credentials_id = %s
               AND target_image_id NOT IN (
                   SELECT ti.target_image_id
                     FROM target_image AS ti
                     JOIN tmp_target_image AS tmpti USING (target_internal_id)
                    WHERE ti.target_id = %s)"""
        cu.execute(query, [ credsId, target.target_id ])
        # Add the new ones
        query = """
            INSERT INTO target_image_credentials
                (target_image_id, target_credentials_id)
            SELECT ti.target_image_id, %s
              FROM target_image AS ti
              JOIN tmp_target_image AS tmpti USING (target_internal_id)
             WHERE ti.target_id = %s
               AND ti.target_image_id NOT IN
               (SELECT target_image_id FROM target_image_credentials
                WHERE target_credentials_id=%s)
        """
        cu.execute(query, [ credsId, target.target_id, credsId ])
        # Finally, remove all images that have no credentials
        query = """
            DELETE FROM target_image
             WHERE target_image_id NOT IN (
               SELECT target_image_id FROM target_image_credentials
             )
        """
        cu.execute(query)
        cu.execute("DROP TABLE tmp_target_image")
        self.recomputeTargetDeployableImages()

    @exposed
    def updateTargetSystems(self, target, systems):
        creds = self._getTargetCredentialsForCurrentUser(target)
        if creds is None:
            raise errors.InvalidData()
        cu = connection.cursor()
        cu.execute("""
            CREATE TEMPORARY TABLE tmp_target_system (
                name TEXT,
                description TEXT,
                target_internal_id TEXT,
                ip_addr_1 TEXT,
                ip_addr_2 TEXT,
                state TEXT,
                created_date TIMESTAMP WITH TIME ZONE
            )
        """)
        try:
            self._updateTargetSystems(cu, target, creds, systems)
        finally:
            cu.execute("DROP TABLE tmp_target_system")

    def _updateTargetSystems(self, cu, target, creds, systems):
        credsId = creds.target_credentials_id
        query = """
            INSERT INTO tmp_target_system
                (name, description, target_internal_id, ip_addr_1, ip_addr_2, state, created_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        tsys = [ self._system(target, x) for x in systems ]
        # Eliminate dupes
        tsysMap = dict((x.target_internal_id, x) for x in tsys)
        params = [ (x.name, x.description, x.target_internal_id,
            x.ip_addr_1, x.ip_addr_2, x.state, x.created_date)
                for x in tsysMap.values() ]
        cu.executemany(query, params)
        # Retrieve systems to be updated
        query = """
            SELECT ts.target_system_id, ts.target_internal_id
              FROM tmp_target_system AS tmptsys
              JOIN target_system AS ts USING (target_internal_id)
             WHERE ts.target_id = %s
               AND (ts.name != tmptsys.name
                   OR ts.description != tmptsys.description
                   OR ts.ip_addr_1 != tmptsys.ip_addr_1
                   OR ts.ip_addr_2 != tmptsys.ip_addr_2
                   OR ts.state != tmptsys.state
                   OR (ts.created_date IS NULL AND tmptsys.created_date IS NOT NULL)
                   OR ts.created_date != tmptsys.created_date)
        """
        cu.execute(query, [ target.target_id ])
        toUpdate = cu.fetchall()
        now = self.mgr.sysMgr.now()
        for targetSystemId, targetInternalId in toUpdate:
            model = models.TargetSystem.objects.get(target_system_id=targetSystemId)
            src = tsysMap[targetInternalId]
            model.name = src.name
            model.description = src.description
            model.ip_addr_1 = src.ip_addr_1
            model.ip_addr_2 = src.ip_addr_2
            model.state = src.state
            if src.created_date is not None:
                model.created_date = src.created_date
            model.modified_date = now
            model.save()
        # Insert all new systems
        query = """
            INSERT INTO target_system
                (target_id, name, description, target_internal_id, ip_addr_1, ip_addr_2, state, created_date)
            SELECT %s, name, description, target_internal_id, ip_addr_1, ip_addr_2, state, created_date
              FROM tmp_target_system
             WHERE target_internal_id NOT IN
               (SELECT target_internal_id FROM target_system WHERE target_id=%s)
        """
        cu.execute(query, [ target.target_id, target.target_id ])
        # Relink systems to target credentials
        # First, remove the ones not in this list
        query = """
            DELETE FROM target_system_credentials
             WHERE target_credentials_id = %s
               AND target_system_id NOT IN (
                   SELECT ts.target_system_id
                     FROM target_system AS ts
                     JOIN tmp_target_system AS tmptsys USING (target_internal_id)
                    WHERE ts.target_id = %s)"""
        cu.execute(query, [ credsId, target.target_id ])
        # Add the new ones
        query = """
            INSERT INTO target_system_credentials
                (target_system_id, target_credentials_id)
            SELECT ts.target_system_id, %s
              FROM target_system AS ts
              JOIN tmp_target_system AS tmptsys USING (target_internal_id)
             WHERE ts.target_id = %s
               AND ts.target_system_id NOT IN
               (SELECT target_system_id FROM target_system_credentials
                WHERE target_credentials_id=%s)
        """
        cu.execute(query, [ credsId, target.target_id, credsId ])
        # Finally, remove all systems that have no credentials
        query = """
            DELETE FROM target_system
             WHERE target_system_id NOT IN (
               SELECT target_system_id FROM target_system_credentials
             )
        """
        cu.execute(query)
        #self.recomputeTargetSystems()

    @exposed
    def recomputeTargetDeployableImages(self):
        cu = connection.cursor()
        cu.execute("""
            CREATE TEMPORARY TABLE tmp_target_image (
                target_id INT,
                target_image_id INT,
                file_id INT
            )
        """)
        try:
            self._recomputeTargetDeployableImages()
        finally:
            cu.execute("DROP TABLE tmp_target_image")

    def _recomputeTargetDeployableImages(self):
        cu = connection.cursor()
        # First, compute all deployed images
        query = """
            INSERT INTO tmp_target_image (target_id, target_image_id, file_id)
                SELECT tid.targetId, ti.target_image_id, tid.fileId
                  FROM TargetImagesDeployed AS tid
                  JOIN target_image AS ti
                        ON (ti.target_id = tid.targetId
                            AND ti.target_internal_id = tid.targetImageId)
        """
        cu.execute(query)
        # Add undeployed images
        query = """
            INSERT INTO tmp_target_image (target_id, target_image_id, file_id)
                SELECT t.targetId, NULL, imgf.fileId
                  FROM Targets AS t
                  JOIN target_types AS tt USING (target_type_id)
                  JOIN Builds AS img ON (tt.build_type_id = img.buildType)
                  JOIN BuildFiles AS imgf ON (img.buildId = imgf.buildId)
                 WHERE NOT EXISTS (
                       SELECT 1
                         FROM tmp_target_image
                        WHERE target_id = t.targetId
                          AND file_id = imgf.fileId)
        """
        cu.execute(query)
        # XXX Deal with EC2 images
        # XXX prefer ova vs ovf 0.9

        # XXX this should do smart replaces instead of this wholesale
        # replace
        cu.execute("DELETE FROM target_deployable_image")
        cu.execute("""
            INSERT INTO target_deployable_image
                (target_id, target_image_id, file_id)
            SELECT target_id, target_image_id, file_id
              FROM tmp_target_image""")

    def _image(self, target, image):
        imageName = self._unXobj(getattr(image, 'productName', None))
        if imageName is None:
            imageName = self._unXobj(getattr(image, 'shortName', None))
        if imageName is None:
            imageName = self._unXobj(getattr(image, 'longName', None))
        imageDescription = self._unXobj(getattr(image, 'longName', imageName))
        imageId = self._unXobj(getattr(image, 'internalTargetId'))
        rbuilderImageId = self._unXobj(getattr(image, 'imageId'))
        if rbuilderImageId == imageId:
            rbuilderImageId = None

        model = models.TargetImage(target=target,
            name=imageName, description=imageDescription,
            target_internal_id=imageId, rbuilder_image_id=rbuilderImageId)
        return model

    def _system(self, target, system):
        name = self._unXobj(getattr(system, 'instanceName', None))
        description = self._unXobj(getattr(system, 'instanceDescription', name))
        systemId = self._unXobj(getattr(system, 'instanceId'))
        ipAddr1 = self._unXobj(getattr(system, 'publicDnsName', None))
        ipAddr2 = self._unXobj(getattr(system, 'privateDnsName', None))
        state = self._unXobj(getattr(system, 'state'))
        createdDate = self._unXobj(getattr(system, 'launchTime', None))
        if createdDate is not None:
            createdDate = timeutils.fromtimestamp(createdDate)

        model = models.TargetSystem(target=target,
            name=name, description=description,
            target_internal_id=systemId, ip_addr_1=ipAddr1, ip_addr_2=ipAddr2,
            state=state, created_date=createdDate)
        return model

    @classmethod
    def _unXobj(cls, value):
        if value is None:
            return None
        return unicode(value)

    @exposed
    def getDescriptorTargetConfiguration(self, targetId):
        target = self.getTargetById(targetId)
        descr = self.mgr.getDescriptorCreateTargetByTargetType(target.target_type_id)
        return descr


class TargetTypesManager(basemanager.BaseManager, CatalogServiceHelper):
    @exposed
    def getTargetTypeById(self, targetTypeId):
        return modellib.Cache.get(models.TargetType, pk=int(targetTypeId))

    @exposed
    def getTargetTypeByName(self, targetTypeName):
        return modellib.Cache.get(models.TargetType, name=targetTypeName)

    @exposed
    def getTargetTypes(self):
        targetTypes = modellib.Cache.all(models.TargetType)
        ret = models.TargetTypes()
        ret.target_type = sorted(targetTypes, key=lambda x: x.target_type_id)
        return ret

    @exposed
    def getTargetsByTargetType(self, target_type_id):
        # We need to cast to int, otherwise the filter won't catch anything
        target_type_id = int(target_type_id)
        targets = models.Targets(targetTypeFilter=set([target_type_id]))
        targets.target = models.Target.objects.filter(
            target_type__target_type_id=target_type_id).order_by('target_id')
        return targets

    @exposed
    def getTargetTypesByTargetId(self, target_id):
        target = models.Target.objects.get(pk=target_id)
        return target.target_type

    @exposed
    def getDescriptorCreateTargetByTargetType(self, target_type_id):
        targetType = self.getTargetTypeById(target_type_id)
        DriverClass = self.getDriverClass(targetType)
        descr = descriptor.ConfigurationDescriptor(
            fromStream=DriverClass.configurationDescriptorXmlData)
        descr.setRootElement("descriptor_data")
        allZones = sorted(modellib.Cache.all(zones.Zone), key=lambda x: x.zone_id)
        zoneList = [ (x.name, x.description)
            for x in allZones ]
        zoneList = [ descr.ValueWithDescription(n, descriptions=d)
            for (n, d) in zoneList ]
        descr.addDataField('zone',
            descriptions = "Zone",
            type = zoneList,
            required=True)

        return descr

class TargetTypeJobsManager(basemanager.BaseManager):
    @exposed
    def getJobsByTargetType(self, target_type_id):
        jobs = jobsmodels.Job.objects.filter(jobtargettype__target_type__target_type_id = target_type_id).order_by("-job_id")
        Jobs = jobsmodels.Jobs()
        Jobs.job = jobs
        return Jobs

    @exposed
    def getAllTargetTypeJobs(self):
        jobs = jobsmodels.Job.objects.filter(~Q(jobtargettype = None)).order_by("-job_id")
        Jobs = jobsmodels.Jobs()
        Jobs.job = jobs
        return Jobs

class TargetJobsManager(basemanager.BaseManager):
    @exposed
    def getJobsByTargetId(self, target_id):
        jobTargets = models.JobTarget.objects.filter(target__target_id=target_id).order_by('-job__job_id')
        Jobs = jobsmodels.Jobs()
        Jobs.job = [jobTarget.job for jobTarget in jobTargets]
        return Jobs
        
    @exposed
    def getAllTargetJobs(self):
        allTargetJobs = []
        for target in models.Target.objects.all():
            jobs = jobsmodels.Job.objects.filter(target_jobs__target=target)
            allTargetJobs.extend(jobs)
            
            allTargetJobs.extend(jobsmodels.Job.objects.extra(
                tables=[models.JobTarget._meta.db_table],
                where=['jobs_job_target.job_id=jobs_job.job_id']).order_by('-job_id')
            )
            
        Jobs = jobsmodels.Jobs()
        Jobs.job = allTargetJobs
        return Jobs
            
