#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import json
from lxml import etree

from django.db import connection
from django.db.models import Q

from mint.lib import data as mintdata
from mint.django_rest.rbuilder import errors, modellib
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.targets import models
from mint.django_rest.rbuilder.inventory import zones
from mint.django_rest.rbuilder.jobs import models as jobsmodels
from mint.django_rest.rbuilder.querysets import models as qsmodels

from smartform import descriptor

class CatalogServiceHelper(object):
    @classmethod
    def getDriverClass(cls, targetType):
        moduleName = "catalogService.rest.drivers.%s" % targetType.name
        DriverClass = __import__(moduleName, {}, {}, '.driver').driver
        return DriverClass

class TargetsManager(basemanager.BaseManager, CatalogServiceHelper):
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
    def createTarget(self, targetType, targetName, targetData):
        targetData.pop('name', None)
        description = targetData.get('description', targetName)
        zoneName = targetData.pop('zone')
        zone = modellib.Cache.get(zones.Zone, name=zoneName)
        target = models.Target(name=targetName, description=description,
            target_type=targetType, zone=zone)
        target.save()
        for k, v in targetData.iteritems():
            v = json.dumps(v)
            td = models.TargetData(target=target, name=k, value=v)
            td.save()
        self._addTargetQuerySet(target)
        return target

    def _addTargetQuerySet(self, target):
        feField = 'target.target_id'
        feOperator = 'EQUAL'
        feValue = target.target_id

        fe, created = qsmodels.FilterEntry.objects.get_or_create(field=feField,
            operator=feOperator, value=feValue)

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
    def getDescriptorConfigureCredentials(self, target_id):
        target = self.getTargetById(target_id)
        DriverClass = self.getDriverClass(target.target_type)
        descr = descriptor.ConfigurationDescriptor(
            fromStream=DriverClass.credentialsDescriptorXmlData)
        descr.setRootElement("descriptor_data")
        return descr

    @exposed
    def serializeDescriptorConfigureCredentials(self, target_id):
        descr = self.getDescriptorConfigureCredentials(target_id)
        wrapper = etreeObjectWrapper(descr.getElementTree(validate=True))
        return wrapper

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
    def serializeDescriptorRefreshImages(self, targetId):
        descr = self.getDescriptorRefreshImages(targetId)
        wrapper = etreeObjectWrapper(descr.getElementTree(validate=True))
        return wrapper

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

    def _image(self, target, image):
        imageName = self._unXobj(getattr(image, 'productName',
            getattr(image, 'shortName', getattr(image, 'longName'))))
        imageDescription = self._unXobj(getattr(image, 'longName', imageName))
        imageId = self._unXobj(getattr(image, 'internalTargetId'))
        rbuilderImageId = self._unXobj(getattr(image, 'imageId'))
        if rbuilderImageId == imageId:
            rbuilderImageId = None

        model = models.TargetImage(target=target,
            name=imageName, description=imageDescription,
            target_internal_id=imageId, rbuilder_image_id=rbuilderImageId)
        return model

    @classmethod
    def _unXobj(cls, value):
        if value is None:
            return None
        return unicode(value)

class TargetTypesManager(basemanager.BaseManager, CatalogServiceHelper):
    @exposed
    def getTargetTypeById(self, target_type_id):
        return models.TargetType.objects.get(pk=target_type_id)
        
    @exposed
    def getTargetTypes(self):
        TargetTypes = models.TargetTypes()
        TargetTypes.target_type = models.TargetType.objects.order_by('target_type_id')
        return TargetTypes

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

    @exposed
    def serializeDescriptorCreateTargetByTargetType(self, target_type_id):
        descr = self.getDescriptorCreateTargetByTargetType(target_type_id)
        wrapper = etreeObjectWrapper(descr.getElementTree(validate=True))
        return wrapper

# XXX This should go in modellib most likely
class etreeObjectWrapper(object):
    def __init__(self, element):
        self.element = element
    def to_xml(self, request=None, xobj_model=None):
        return etree.tostring(self.element, pretty_print=False,
            encoding="UTF-8", xml_declaration=False)

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
            
