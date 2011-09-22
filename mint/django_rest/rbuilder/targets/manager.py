#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import json
from lxml import etree

from django.db.models import Q

from mint.lib import data as mintdata
from mint.django_rest.rbuilder import modellib
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
        targetConfig['zone'] = self.getTargetZone(target)
        return targetConfig

    @exposed
    def getTargetCredentialsForCurrentUser(self, target):
        userId = self.auth.userId
        creds = models.TargetCredentials.objects.filter(
            target_user_credentials__target=target,
            target_user_credentials__user__user_id=userId)
        if not creds:
            return None
        return mintdata.unmarshalTargetUserCredentials(creds[0].credentials)

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
        from django.db import connection
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
        description = targetData.pop('description', targetName)
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
        return models.TargetType.objects.filter(
            target_type__target_type_id=target_type_id).order_by('target_type_id')

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
            
