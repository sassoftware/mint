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
    system = []
    view_name = 'Surveys'

    def __init__(self):
        modellib.Collection.__init__(self)

    def save(self):
        # shouldn't really be surfacing this
        return [s.save() for s in self.survey]

class Survey(modellib.XObjIdModel):
    
    class Meta:
        db_table = 'inventory_survey'
    view_name = 'Survey'
    _xobj_explicit_accessors = set([])
    _xobj = xobj.XObjMetadata(
                tag = 'survey',
                attributes = {'id':str})

    survey_id    = D(models.AutoField(primary_key=True),
        "the database ID for the survey", short="Survey ID")
    tags         = models.ManyToManyField('SurveyTag', through="SurveyTags")
    name         = models.TextField()
    description  = models.TextField()
    created_date = modellib.DateTimeUtcField(auto_now_add=True)
    removeable   = models.BooleanField(default=True)
    comment      = models.TextField()

class SurveyTag(modellib.XObjIdModel):

    class Meta:
       db_table = 'inventory_survey_tag'
    _xobj = xobj.XObjMetadata(tag='tag')

    survey_tag_id = models.AutoField(primary_key=True)
    tag = models.TextField()

class SurveyTags(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_survey_tags'
    # XXX This class should never be serialized directly, but unless an _xobj
    # field is added, we have no access to it from modellib
    _xobj = xobj.XObjMetadata(tag='__surveyTags')
    survey_tags_id = models.AutoField(primary_key=True)
    survey = modellib.ForeignKey(Survey)
    tag = models.ForeignKey('SurveyTag', unique=True, related_name='surveys')

# classes to add:
#
# SurveyXml --- original XML from system
# SurveyRpmPackages
# SurveyRpmPackage
# SurveyConaryPackages
# SurveyConaryPackage
# SurveySurveyServices
# SurveyService
# SurveyServiceRunLevels
# SurveyServiceRunLevel

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
