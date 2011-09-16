#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from lxml import etree

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.targets import models
from mint.django_rest.rbuilder.inventory import zones
from mint.django_rest.rbuilder.jobs import models as jobsmodels

from smartform import descriptor

class TargetsManager(basemanager.BaseManager):
    @exposed
    def getTargetById(self, target_id):
        return models.Target.objects.get(pk=target_id)
        
    @exposed
    def getTargets(self):
        Targets = models.Targets()
        Targets.target = models.Target.objects.order_by('target_id')
        return Targets
        
    @exposed
    def createTarget(self, target):
        target.save()
        return target
        
    @exposed
    def updateTarget(self, target_id, target):
        target.save()
        return target
        
    @exposed
    def deleteTarget(self, target_id):
        target = models.Target.objects.get(pk=target_id)
        target.delete()
        
        
class TargetTypesManager(basemanager.BaseManager):
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
        moduleName = "catalogService.rest.drivers.%s" % targetType.name
        DriverClass = __import__(moduleName, {}, {}, '.driver').driver
        descr = descriptor.ConfigurationDescriptor(
            fromStream=DriverClass.configurationDescriptorXmlData)
        zoneList = [ (x.name, x.description)
            for x in zones.Zone.objects.order_by('zone_id') ]
        zoneList = [ descr.ValueWithDescription(n, descriptions=d)
            for (n, d) in zoneList ]
        descr.addDataField('zone',
            descriptions = "Zone",
            type = zoneList)

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

class TargetCredentialsManager(basemanager.BaseManager):
    @exposed
    def getTargetCredentialsForTargetByUserId(self, target_id, user_id):
        return models.TargetUserCredentials.objects.get(target_id=target_id, user_id=user_id)
        
    @exposed
    def getTargetCredentialsForTarget(self, target_id, target_credentials_id):
        return models.TargetCredentials.objects.get(pk=target_credentials_id)

class TargetTypeJobsManager(basemanager.BaseManager):
    @exposed
    def getJobsByTargetType(self, target_type_id):
        jobTargetTypes = models.JobTargetType.objects.filter(target_type__target_type_id=target_type_id).order_by('-job__job_id')
        Jobs = jobsmodels.Jobs()
        Jobs.job = [jobTargetType.job for jobTargetType in jobTargetTypes]
        return Jobs

class TargetJobsManager(basemanager.BaseManager):
    @exposed
    def getJobsByTargetId(self, target_id):
        jobTargets = models.JobTarget.objects.filter(target__target_id=target_id).order_by('-job__job_id')
        Jobs = jobsmodels.Jobs()
        Jobs.job = [jobTarget.job for jobTarget in jobTargets]
        return Jobs