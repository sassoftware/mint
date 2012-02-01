#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.db import models
from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from xobj import xobj
import sys

# XObjHidden = modellib.XObjHidden
# APIReadOnly = modellib.APIReadOnly

class Surveys(modellib.Collection):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'surveys')
    list_fields = ['survey']
    survey = []
    view_name = 'Surveys'

    def __init__(self):
        modellib.Collection.__init__(self)

    def save(self):
        # shouldn't really be surfacing this
        return [s.save() for s in self.survey]

class Diffs(modellib.Collection):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(tag='survey_diffs')
    list_fields = [ 'survey_diff']
    survey_diff = []
    view_name = 'SurveyDiffs'
 
    def __init__(self):
        modellib.Collection.__init__(self)

    def save(self):
        return [s.save() for s in self.survey_diffs]

class Survey(modellib.XObjIdModel):
    
    class Meta:
        db_table = 'inventory_survey'
    view_name = 'Survey'
    _xobj_explicit_accessors = set([
         'conary_packages',
         'rpm_packages',
         'services',
         'tags',
    ])
    _xobj = xobj.XObjMetadata(
        tag = 'survey', attributes = {'id':str}
    )

    survey_id     = D(models.AutoField(primary_key=True),
        "the database ID for the survey", short="Survey ID")
    name          = models.TextField()
    uuid          = models.TextField(null=False)
    description   = models.TextField()
    created_date  = modellib.DateTimeUtcField(auto_now_add=True)
    modified_date = modellib.DateTimeUtcField(auto_now_add=True)
    created_by    = modellib.ForeignKey('users.User', db_column='created_by', related_name='+') 
    modified_by    = modellib.ForeignKey('users.User', db_column='modified_by', related_name='+') 
    # FIXME: add to database schema
    #removeable   = models.BooleanField(default=True)
    system        = modellib.ForeignKey('inventory.System', related_name='surveys', db_column='system_id')
    comment       = models.TextField()

    # FIXME: TODO: custom URL method so URL is UUID based


class RpmPackage(modellib.XObjIdModel):
     class Meta:
         db_table = 'inventory_rpm_package'
     _xobj = xobj.XObjMetadata(tag='_rpm_package')
     rpm_package_id = models.AutoField(primary_key=True)
     name           = models.TextField(null=False)
     epoch          = models.IntegerField(null=True)
     version        = models.TextField(null=False)
     release        = models.TextField(null=False)
     architecture   = models.TextField(null=False)
     description    = models.TextField(null=True)
     signature      = models.TextField(null=False)

class ConaryPackage(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_conary_package'
    _xobj = xobj.XObjMetadata(tag='_conary_package')
    conary_package_id = models.AutoField(primary_key=True)
    name              = models.TextField(null=False)
    version           = models.TextField(null=False)
    flavor            = models.TextField(null=False)
    description       = models.TextField(null=False)
    revision          = models.TextField(null=False)
    architecture      = models.TextField(null=False)
    signature         = models.TextField(null=False)
    rpm_package       = modellib.DeferredForeignKey(RpmPackage, related_name='+')

class Service(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_service'
    _xobj = xobj.XObjMetadata(tag='_service')

    service_id        = models.AutoField(primary_key=True)
    name              = models.TextField(null=False)
    autostart         = models.BooleanField(default=False)
    runlevels         = models.TextField(default='')

class SurveyTag(modellib.XObjIdModel):

    class Meta:
       db_table = 'inventory_survey_tags'
    _xobj = xobj.XObjMetadata(tag='tag')

    tag_id = models.AutoField(primary_key=True)
    survey = modellib.ForeignKey(Survey, related_name='tags')
    name = models.TextField()

class SurveyRpmPackage(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_survey_rpm_package'
    _xobj = xobj.XObjMetadata(tag='rpm_package')
    map_id        = models.AutoField(primary_key=True)
    survey        = modellib.ForeignKey(Survey, related_name='rpm_packages')
    rpm_package   = modellib.ForeignKey(RpmPackage, related_name='survey_rpm_packages')
    install_date  = modellib.DateTimeUtcField(auto_now_add=True)
    

class SurveyConaryPackage(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_survey_conary_package'
    _xobj = xobj.XObjMetadata(tag='conary_package')
    map_id         = models.AutoField(primary_key=True)
    survey         = modellib.ForeignKey(Survey, related_name='conary_packages')
    conary_package = modellib.ForeignKey(ConaryPackage, related_name='survey_conary_packages')
    install_date   = modellib.DateTimeUtcField(auto_now_add=True)
 
class SurveyService(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_survey_service'
    _xobj = xobj.XObjMetadata(tag='service')
    map_id         = models.AutoField(primary_key=True)
    survey         = modellib.ForeignKey(Survey, related_name='services')
    service        = modellib.ForeignKey(Service, related_name='survey_services')
    running        = models.BooleanField()
    status         = models.TextField()

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
