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

    survey_id = D(models.AutoField(primary_key=True),
        "the database ID for the survey", short="Survey ID")
    # name
    # description
    # created_date
    # removeable
    # tags
    # comment

# classes to add:
#
# SurveyTag
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
