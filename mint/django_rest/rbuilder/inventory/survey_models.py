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
from django.core.urlresolvers import reverse

XObjHidden = modellib.XObjHidden
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

class WindowsPackageInfoList(modellib.UnpaginatedCollection):
   class Meta:
       abstract = True
   _xobj_no_register = True
   _xobj = xobj.XObjMetadata(tag = 'windows_packages_info')
   list_fields = ['windows_package']
   windows_package = []
   view_name = None # ???

   def __init__(self):
       modellib.UnpaginatedCollection.__init__(self)

   def save(self):
       return
#***********************************************************

class WindowsRequiredServiceInfoList(modellib.UnpaginatedCollection):
   class Meta:
       abstract = True
   _xobj_no_register = True
   _xobj = xobj.XObjMetadata(tag = 'required_windows_services_info')
   list_fields = ['windows_service']
   windows_service = []
   view_name = None

   def __init__(self):
       modellib.UnpaginatedCollection.__init__(self)

   def save(self):
       return


#***********************************************************

class Survey(modellib.XObjIdModel):
    ''' One survey of a given system '''
    
    class Meta:
        db_table = 'inventory_survey'
    view_name = 'Survey'
    _xobj_explicit_accessors = set([
         'conary_packages',
         'rpm_packages',
         'windows_packages',
         'windows_patches',
         'services',
         'windows_services',
         'tags',
    ])
    _xobj = xobj.XObjMetadata(
        tag = 'survey', attributes = {'id':str}
    )

    survey_id     = D(modellib.XObjHidden(models.AutoField(primary_key=True)),
        "the database ID for the survey", short="Survey ID")
    name          = models.TextField()
    uuid          = models.TextField(null=False)
    description   = models.TextField()
    created_date  = modellib.DateTimeUtcField(auto_now_add=True)
    modified_date = modellib.DateTimeUtcField(auto_now_add=True)
    removable     = models.BooleanField(default=True)
    created_by    = modellib.ForeignKey(usermodels.User, null=True, db_column='created_by', related_name='+', on_delete=models.SET_NULL) 
    modified_by   = modellib.ForeignKey(usermodels.User, null=True, db_column='modified_by', related_name='+', on_delete=models.SET_NULL) 
    system        = modellib.DeferredForeignKey('inventory.System', related_name='surveys', db_column='system_id')
    comment       = models.TextField()
    system_model  = models.TextField()
    system_model_modified_date = modellib.DateTimeUtcField()
    has_system_model = models.BooleanField(default=False)

    # 'should be like this' values XML from system
    config_properties     = modellib.XMLField(db_column='values_xml')
    # values from config readers
    observed_properties   = modellib.XMLField(db_column='observed_values_xml')
    # 'should be like this' values from server (usually will match system)
    desired_properties    = modellib.XMLField(db_column='desired_values_xml')
    # values from config discovery probes
    discovered_properties = modellib.XMLField(db_column='discovered_values_xml')
    # values from config validation reports
    validation_report  = modellib.XMLField(db_column='validator_values_xml')
     
    compliance_summary            = modellib.XMLField(db_column='compliance_summary_xml')
    config_properties_descriptor  = modellib.XMLField(db_column='config_values_descriptor_xml')
    desired_properties_descriptor = modellib.XMLField(db_column='desired_values_descriptor_xml')
    preview                       = modellib.XMLField(db_column='preview_xml')
    config_compliance             = modellib.XMLField(db_column='config_diff_xml')    

    updates_pending = XObjHidden(models.BooleanField(default=False))
    has_errors = XObjHidden(models.BooleanField(default=False))

    def get_url_key(self, *args, **kwargs):
        return [ self.uuid ]

#***********************************************************

# type codes for SurveyValues
CONFIG_VALUES = 0
DESIRED_VALUES = 1
OBSERVED_VALUES = 2
DISCOVERED_VALUES = 3
VALIDATOR_VALUES = 4

class SurveyValues(modellib.XObjIdModel):
    ''' shredded values of various system properties so they are searchable '''

    class Meta:
        db_table = 'inventory_survey_values'

    _xobj_explicit_accessors = set([])
    _xobj = xobj.XObjMetadata(
        tag = '_inventory_survey_values', attributes = {'id':str}
    )

    survey_value_id = models.AutoField(primary_key=True, db_column='survey_value_id')
    survey          = modellib.ForeignKey(Survey, db_column='survey_id', null=False, related_name='survey_config')
    type            = models.IntegerField(null=False)
    key             = models.TextField(null=False)
    subkey          = models.TextField(null=True)
    value           = models.TextField()

#***********************************************************

class SurveyDiff(modellib.XObjIdModel):
    ''' Differences between two surveys '''

    class Meta:
        db_table = 'inventory_survey_diff'
    view_name = 'SurveyDiff'
    
    # to use this model, look up the XML in the object, do not use xobj

    diff_id       = models.AutoField(primary_key=True)
    left_survey   = modellib.ForeignKey(Survey, null=False, related_name='+')
    right_survey  = modellib.ForeignKey(Survey, null=False, related_name='+')
    created_date  = modellib.DateTimeUtcField(auto_now_add=True)
    xml           = models.TextField()

#***********************************************************

class ShortSurvey(modellib.XObjIdModel):
    '''Hack used to emulate 'summary_views' for survey collections.'''
    # replaceable once we have "view model" support

    class Meta:
        db_table = 'inventory_survey'
    view_name = 'Survey'
    _xobj_explicit_accessors = set([])
    _xobj_no_register = True
    _xobj = xobj.XObjMetadata(
        tag = 'survey', attributes = {'id':str}
    )

    survey_id     = D(modellib.XObjHidden(models.AutoField(primary_key=True)),
        "the database ID for the survey", short="Survey ID")
    system        = XObjHidden(modellib.DeferredForeignKey('inventory.System', related_name='+', db_column='system_id'))
    uuid          = models.TextField()
    name          = models.TextField()
    description   = models.TextField()
    removable     = models.BooleanField(default=False)
    created_date  = modellib.DateTimeUtcField(auto_now_add=True)

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

     def get_url_key(self, *args, **kwargs):
         return [ self.rpm_package_id ]

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
         "revision", "architecture", "signature", "rpm_package_info"
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
    rpm_package_info  = modellib.ForeignKey(RpmPackageInfo, db_column='rpm_package_id', related_name='+')

    def get_url_key(self, *args, **kwargs):
        return [ self.conary_package_id ]


#***********************************************************

class WindowsPackageInfo(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_windows_package'

    view_name = 'SurveyWindowsPackageInfo'
    _xobj = xobj.XObjMetadata(tag='windows_package_info')
    summary_view = [ 'publisher', 'product_code', 'package_code',
                     'product_name', 'type', 'upgrade_code',
                     'version' ]

    windows_package_id = models.AutoField(primary_key=True)
    publisher          = models.TextField(null=False)
    product_code       = models.TextField(null=False)
    package_code       = models.TextField(null=False)
    product_name       = models.TextField(null=False)
    type               = models.TextField(null=False)
    upgrade_code       = models.TextField(null=False)
    version            = models.TextField(null=False)
 
    def get_url_key(self, *args, **kwargs):
        return [ self.windows_package_id ]

#***********************************************************

# get around various modellib funness
class FakeWindowsPackageInfo(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
        tag="windows_package_info",
        attributes= { 'id' : str }
    )
    _xobj_no_register = True
 
    publisher          = models.TextField(null=False)
    product_code       = models.TextField(null=False)
    package_code       = models.TextField(null=False)
    product_name       = models.TextField(null=False)
    type               = models.TextField(null=False)
    upgrade_code       = models.TextField(null=False)
    version            = models.TextField(null=False)
    id                 = models.TextField(null=False)

#***********************************************************

class WindowsPatchInfo(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_windows_patch'

    view_name = 'SurveyWindowsPatchInfo'
    _xobj = xobj.XObjMetadata(tag='windows_patch_info',
         attributes = { 'id' : str }
    )
    summary_view = [ 
        'display_name', 'uninstallable', 'patch_code',
        'product_code', 'transforms', 'windows_packages'
    ]    
    
    windows_patch_id = models.AutoField(primary_key=True)
    display_name     = models.TextField(null=False)
    uninstallable    = models.BooleanField(null=False)
    patch_code       = models.TextField(null=False)
    product_code     = models.TextField(null=False)
    transforms       = models.TextField(null=False)
    windows_packages = modellib.SyntheticField()

    def computeSyntheticFields(self, sender, **kwargs):
        self.windows_packages = WindowsPackageInfoList()
        links = SurveyWindowsPatchPackageLink.objects.filter(
            windows_patch_info = self
        )
        results = [ l.windows_package_info for l in links ]
        # forgive me
        results = [ FakeWindowsPackageInfo(
            publisher = wp.publisher, product_code = wp.product_code,
            package_code = wp.package_code, product_name = wp.product_name,
            type = wp.type, upgrade_code = wp.upgrade_code, version = wp.version,
            id = reverse('SurveyWindowsPackageInfo', args=[ wp.pk ])
        ) for wp in results ]
        self.windows_packages.window_package = results
 
    def get_url_key(self, *args, **kwargs):
        return [ self.windows_patch_id ] 

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

    def get_url_key(self, *args, **kwargs):
        return [ self.service_id ]

#***********************************************************

class WindowsServiceInfo(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_windows_service'

    view_name = 'SurveyWindowsServiceInfo'
    _xobj = xobj.XObjMetadata(tag='windows_service_info')

    summary_view = [
        'name', 'display_name', 'type', 'handle', 'required_services'
    ]

    windows_service_id = models.AutoField(primary_key=True)
    name               = models.TextField(null=False)
    display_name       = models.TextField(null=False)
    type               = models.TextField(null=False)
    handle             = models.TextField(null=False)
    _required_services = XObjHidden(models.TextField(null=False, db_column='required_services')) 

    required_services  = modellib.SyntheticField()

    def computeSyntheticFields(self, sender, **kwargs):
        self.required_services = WindowsRequiredServiceInfoList()
        services = []
        if services != "":
            services = self._required_services.split(",")
        results = WindowsServiceInfo.objects.filter(name__in=services)
        results = [ FakeWindowsServiceInfo(
            name = ws.name, display_name = ws.display_name,
            id = reverse('SurveyWindowsPackageInfo', args=[ ws.pk ])
        ) for ws in results ]
        self.required_services.window_service = results

#***********************************************************

class FakeWindowsServiceInfo(modellib.XObjIdModel):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
        tag="windows_package_info",
        attributes= { 'id' : str }
    )
    _xobj_no_register = True
    
    id                 = models.TextField(null=False)
    name               = models.TextField(null=False)
    display_name       = models.TextField(null=False)

#***********************************************************

class SurveyTag(modellib.XObjIdModel):
    ''' A survey can have multiple string tags assigned '''

    class Meta:
       db_table = 'inventory_survey_tags'

    _xobj = xobj.XObjMetadata(tag='tag')                 
    view_name = 'SurveyTag'

    tag_id = models.AutoField(primary_key=True)
    survey = modellib.ForeignKey(Survey, related_name='tags')
    name   = models.TextField()
    
    def get_url_key(self, *args, **kwargs):
        return [ self.tag_id ]

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
    install_date     = modellib.DateTimeUtcField(auto_now_add=False, null=True)

    def get_url_key(self, *args, **kwargs):
        return [ self.rpm_package_id ]

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
    install_date        = modellib.DateTimeUtcField(auto_now_add=False, null=True)
    is_top_level        = models.BooleanField(null=False, default=False)   
 
    def get_url_key(self, *args, **kwargs):
        return [ self.conary_package_id ] 

#***********************************************************

class SurveyWindowsPackage(modellib.XObjIdModel):

    class Meta:
        db_table = 'inventory_survey_windows_package'
    _xobj                = xobj.XObjMetadata(tag='windows_package')
    view_name            = 'SurveyWindowsPackage'
    
    windows_package_id   = models.AutoField(primary_key=True, db_column='map_id')
    survey               = XObjHidden(modellib.ForeignKey(Survey, related_name='windows_packages', null=False))
    windows_package_info = modellib.ForeignKey(WindowsPackageInfo, related_name='survey_windows_packages', db_column='windows_package_id', null=False)
    
    install_source       = models.TextField(null=False)
    local_package        = models.TextField(null=False)
    install_date         = modellib.DateTimeUtcField(auto_now_add=False, null=True)
 
    def get_url_key(self, *args, **kwargs):
        return [ self.windows_package_id ] 

#***********************************************************

class SurveyWindowsPatch(modellib.XObjIdModel):

    class Meta:
        db_table = 'inventory_survey_windows_patch'
    _xobj                = xobj.XObjMetadata(tag='windows_patch')
    view_name            = 'SurveyWindowsPatch'

    windows_patch_id     = models.AutoField(primary_key=True, db_column='map_id')
    survey               = XObjHidden(modellib.ForeignKey(Survey, related_name='windows_patches'))
    windows_patch_info   = modellib.ForeignKey(WindowsPatchInfo, 
        related_name='+',
        db_column='windows_patch_id', null=False)
    local_package        = models.TextField(null=False)
    install_date         = modellib.DateTimeUtcField(auto_now_add=False, null=True)
    is_installed         = models.BooleanField(null=False)

    def get_url_key(self, *args, **kwargs):
        return [ self.windows_patch_id ] 
   

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
    
    def get_url_key(self, *args, **kwargs):
        return [ self.service_id ] 

#***********************************************************

class SurveyWindowsService(modellib.XObjIdModel):
    
    class Meta:
        db_table = 'inventory_survey_windows_service'
    _xobj = xobj.XObjMetadata(tag='windows_service')
    view_name       = 'SurveyWindowsService'

    windows_service_id   = models.AutoField(primary_key=True, db_column='map_id')
    survey               = XObjHidden(modellib.ForeignKey(Survey, related_name='windows_services', null=False))
    windows_service_info = modellib.ForeignKey(WindowsServiceInfo, related_name='survey_windows_services', db_column='windows_service_id', null=False)
    running              = models.BooleanField()
    status               = models.TextField(null=False)
 
    def get_url_key(self, *args, **kwargs):
        return [ self.windows_service_id ]
        

class SurveyWindowsPatchPackageLink(modellib.XObjIdModel):
  
    class Meta:
        db_table = 'inventory_windows_patch_windows_package'
    
    link_id              = models.AutoField(primary_key=True, db_column='map_id')
    windows_package_info = modellib.ForeignKey(WindowsPackageInfo, db_column='windows_package_id', related_name='+')
    windows_patch_info   = modellib.ForeignKey(WindowsPatchInfo, db_column='windows_patch_id', related_name='+')
    

#***********************************************************
    
for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj') and not getattr(mod_obj, '_xobj_no_register', False):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
