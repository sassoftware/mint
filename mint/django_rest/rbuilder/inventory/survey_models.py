#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.db import models
from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.users import models as usermodels
from xobj import xobj
import sys

# XObjHidden = modellib.XObjHidden
# APIReadOnly = modellib.APIReadOnly

#***********************************************************

class Surveys(modellib.Collection):
    ''' Collection of all surveys for a particular system '''

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'surveys')
    list_fields = ['survey']
    survey = []
    view_name = 'Surveys'

    # FIXME: verify works in paged context

    # make URL work even if we got there in some strange way
    def get_absolute_url(self, request, parents=None, *args, **kwargs):
        if parents:
            return modellib.XObjIdModel.get_absolute_url(self, request,
                parents, *args, **kwargs)
        return request.build_absolute_uri(request.get_full_path())

    def __init__(self):
        modellib.Collection.__init__(self)

    def save(self):
        # shouldn't really be surfacing this
        return [s.save() for s in self.survey]

#***********************************************************

class Diffs(modellib.Collection):
    ''' Collection of all diffs for a given system '''

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

#***********************************************************

class Survey(modellib.XObjIdModel):
    ''' One survey of a given system '''
    
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
    removable     = models.BooleanField(default=False)
    created_by    = modellib.ForeignKey(usermodels.User, null=True, db_column='created_by', related_name='+') 
    modified_by   = modellib.ForeignKey(usermodels.User, null=True, db_column='modified_by', related_name='+') 
    # FIXME: add to database schema
    #removeable   = models.BooleanField(default=True)
    system        = modellib.DeferredForeignKey('inventory.System', related_name='surveys', db_column='system_id')
    comment       = models.TextField()

    def get_url_key(self, *args, **kwargs):
        return [ self.uuid ]

#***********************************************************

class RpmPackageInfo(modellib.XObjIdModel):
     ''' Representation of a possible RPM package, M2M '''

     class Meta:
         db_table = 'inventory_rpm_package'

     summary_view = [ 
         "name", "epoch", "version", "release", 
         "architecture", "description", "signature"
     ]

     view_name = 'SurveyRpmPackageInfo'
     _xobj = xobj.XObjMetadata(tag='rpm_package_info')
     rpm_package_id = models.AutoField(primary_key=True)
     name           = models.TextField(null=False)
     epoch          = models.IntegerField(null=True)
     version        = models.TextField(null=False)
     release        = models.TextField(null=False)
     architecture   = models.TextField(null=False)
     description    = models.TextField(null=True)
     signature      = models.TextField(null=False)

#***********************************************************

class ConaryPackageInfo(modellib.XObjIdModel):
    ''' Representation of a possible Conary package, M2M '''

    class Meta:
        db_table = 'inventory_conary_package'

    view_name = 'SurveyConaryPackageInfo'
    _xobj = xobj.XObjMetadata(tag='conary_package_info')
    # NOTE: rpm_package can't fit into summary view?  Need to fix it.
    summary_view = [
         "name", "version", "flavor", "description",
         "revision", "architecture", "signature",
    ]

    conary_package_id = models.AutoField(primary_key=True)
    name              = models.TextField(null=False)
    version           = models.TextField(null=False)
    flavor            = models.TextField(null=False)
    description       = models.TextField(null=False)
    revision          = models.TextField(null=False)
    architecture      = models.TextField(null=False)
    signature         = models.TextField(null=False)
    # needs to be deferrred so URL is included 
    rpm_package       = modellib.ForeignKey(RpmPackageInfo, related_name='+')

    # workaround summary views and FKs not working as expected
    # FIXME: WHAT, custom serialize not run for these relations?  OW.
    def serialize(self, request=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        if self.rpm_package is not None:
            rpmModel = modellib.XObjIdModel.serialize(self.rpm_package, request)
            xobjModel.rpm_package_info = rpmModel
        return xobjModel

#***********************************************************

class ServiceInfo(modellib.XObjIdModel):
    ''' Representation of a possible Service installation, M2M '''
 
    class Meta:
        db_table = 'inventory_service'

    view_name = 'SurveyServiceInfo'
    _xobj = xobj.XObjMetadata(tag='service_info')

    summary_view = [
        "name", "autostart", "runlevels"
    ]

    service_id        = models.AutoField(primary_key=True)
    name              = models.TextField(null=False)
    autostart         = models.BooleanField(default=False)
    runlevels         = models.TextField(default='')

#***********************************************************

class SurveyTag(modellib.XObjIdModel):
    ''' A survey can have multiple string tags assigned '''

    class Meta:
       db_table = 'inventory_survey_tags'

    _xobj = xobj.XObjMetadata(tag='tag')

    tag_id = models.AutoField(primary_key=True)
    survey = modellib.ForeignKey(Survey, related_name='tags')
    name = models.TextField()

#***********************************************************

class SurveyRpmPackage(modellib.XObjIdModel):
    ''' An RPM installed on a given system '''

    class Meta:
        db_table = 'inventory_survey_rpm_package'

    _xobj     = xobj.XObjMetadata(tag='rpm_package')
    view_name = 'SurveyRpmPackage'
   
    rpm_package_id   = models.AutoField(primary_key=True, db_column='map_id')
    survey           = modellib.ForeignKey(Survey, related_name='rpm_packages', null=False)
    rpm_package_info = modellib.ForeignKey(RpmPackageInfo, related_name='survey_rpm_packages', db_column='rpm_package_id', null=False)
    install_date     = modellib.DateTimeUtcField(auto_now_add=True)

#***********************************************************
    
class SurveyConaryPackage(modellib.XObjIdModel):
    ''' A Conary package installed on a given system '''

    class Meta:
        db_table = 'inventory_survey_conary_package'

    _xobj               = xobj.XObjMetadata(tag='conary_package')
    view_name           = 'SurveyConaryPackage'

    conary_package_id   = models.AutoField(primary_key=True, db_column='map_id')
    survey              = modellib.ForeignKey(Survey, related_name='conary_packages', null=False)
    conary_package_info = modellib.ForeignKey(ConaryPackageInfo, related_name='survey_conary_packages', db_column='conary_package_id', null=False)
    install_date        = modellib.DateTimeUtcField(auto_now_add=True)

#***********************************************************

class SurveyService(modellib.XObjIdModel):
    ''' A service that exists on a given system '''

    class Meta:
        db_table = 'inventory_survey_service'

    _xobj = xobj.XObjMetadata(tag='service')
    view_name       = 'SurveyService'

    service_id      = models.AutoField(primary_key=True, db_column='map_id')
    survey          = modellib.ForeignKey(Survey, related_name='services', null=False)
    service_info    = modellib.ForeignKey(ServiceInfo, related_name='survey_services', db_column='service_id', null=False)
    running         = models.BooleanField()
    status          = models.TextField()

#***********************************************************
    
for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
