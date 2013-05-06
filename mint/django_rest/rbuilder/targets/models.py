#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.db import models
from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.jobs import models as jobmodels
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder.images import models as imagemodels
from mint.django_rest.rbuilder.inventory import zones as zmodels
from xobj import xobj, xobj2
import sys

XObjHidden = modellib.XObjHidden

class TargetType(modellib.XObjIdModel):
    class Meta:
         db_table = 'target_types'
    _xobj = xobj.XObjMetadata(tag='target_type')

    summary_view = [ 'name', 'description' ] 

    _xobj_explicit_accessors = set(['targets'])

    target_type_id = D(models.AutoField(primary_key=True), 'ID of the target')
    name = D(models.TextField(unique=True), "Target Type name, must be unique", short="Target Type name")
    description = D(models.TextField(null=False),
        "Target Type description, null by default", short="Target Type description")
    build_type_id = XObjHidden(models.IntegerField(null=False))
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the resource was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the resource was modified (UTC)")
    descriptor_create_target = modellib.SyntheticField(modellib.HrefField())

    def computeSyntheticFields(self, sender, **kwargs):
        self.descriptor_create_target = modellib.HrefFieldFromModel(self,
            viewName='TargetTypeCreateTarget')

class Targets(modellib.Collection):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(tag='targets')
    list_fields = ['target']
    actions = D(modellib.SyntheticField(jobmodels.Actions),
        "actions available for targets")
    jobs = modellib.SyntheticField(modellib.HrefField())
    descriptor_create = modellib.SyntheticField(modellib.HrefField())

    def __init__(self, targetTypeFilter=None):
        # Initialize our own fields before anything else, or else the
        # postInit signal fires up
        self.targetTypeFilter = targetTypeFilter
        modellib.Collection.__init__(self)

    def computeSyntheticFields(self, sender, **kwargs):
        self.actions = actions = jobmodels.Actions()
        targetTypes = sorted(x.pk for x in modellib.Cache.all(TargetType))
        if self.targetTypeFilter is not None:
            targetTypes = [ x for x in targetTypes if x in self.targetTypeFilter ]
        targetTypes = [ modellib.Cache.get(TargetType, pk=x) for x in targetTypes ]
        actions.action = [ self._newAction(x) for x in targetTypes ]
        self.jobs = modellib.HrefFieldFromModel(viewName="AllTargetJobs")
        self.descriptor_create = modellib.HrefFieldFromModel(viewName="DescriptorsTargetsCreate")

    @classmethod
    def _newAction(cls, targetType):
        actionName = "Create target of type %s" % targetType.name
        action = jobmodels.EventType.makeAction(
                jobTypeName=jobmodels.EventType.TARGET_CREATE,
                actionName=actionName,
                descriptorModel=targetType, descriptorHref="descriptor_create_target")
        return action

class Target(modellib.XObjIdModel):
    class States(object):
        OPERATIONAL = 0
        UNCONFIGURED = 1
    _xobj = xobj.XObjMetadata(tag='target')
    _xobj_explicit_accessors = set()

    class Meta:
        db_table = u'targets'

    target_id = D(models.AutoField(primary_key=True, db_column='targetid'), 'The ID of the target')
    target_type = D(modellib.DeferredForeignKey(TargetType, null=False,
        related_name='targets', view_name='TargetTypeTargets'),
        'Type of target, cannot be null, unique together with name')
    zone = D(modellib.DeferredForeignKey(zmodels.Zone, null=False,
        related_name='targets'), 'Zone for the target, cannot be null')
    name = D(models.TextField(null=False),
            "Target name, cannot be null unique with target type", short="Target name")
    description = D(models.TextField(null=False),
            "Target description, cannot be null", short="Target description")
    unique_together = (target_type, name)
    is_configured = D(modellib.SyntheticField(models.BooleanField()),
        'True if the target is configured')
    credentials_valid = D(modellib.SyntheticField(models.BooleanField()),
        'True if the current user has credentials configured on the target')
    target_user_credentials = modellib.SyntheticField()
    target_configuration = modellib.SyntheticField()

    actions = D(modellib.SyntheticField(jobmodels.Actions),
        "actions available for this target")
    jobs = modellib.SyntheticField(modellib.HrefField())
    state = XObjHidden(models.IntegerField(null=False))
    # Needed for creation from descriptor data
    target_type_name = XObjHidden(modellib.SyntheticField())
    zone_name = XObjHidden(modellib.SyntheticField())

    def computeSyntheticFields(self, sender, **kwargs):
        self.actions = actions = jobmodels.Actions()
        actions.action = []
        actions.action.append(self._actionConfigure())
        actions.action.append(self._actionConfigureUserCredentials())
        actions.action.append(self._actionRefreshImages())
        actions.action.append(self._actionRefreshSystems())
        actions.action.append(self._actionCreateLaunchProfile())
        self.jobs = modellib.HrefFieldFromModel(self, "TargetJobs")
        self.target_user_credentials = modellib.HrefFieldFromModel(self,
            viewName="TargetUserCredentials")
        self.target_configuration = modellib.HrefFieldFromModel(self,
            viewName="TargetConfiguration")
        self._setCredentialsValid()
        self.is_configured = (self.state != self.States.UNCONFIGURED)

    def _setCredentialsValid(self):
        if self._rbmgr is None:
            return
        # XXX FIXME: we should not repeatedly hit the DB here. We should
        # intelligently cache data, especially for multiple targets.
        self.credentials_valid = bool(len(TargetUserCredentials.objects.filter(target=self, user=self._rbmgr.user)))

    def _actionConfigure(self):
        actionName = "Configure target"
        enabled = True
        action = jobmodels.EventType.makeAction(
                jobTypeName=jobmodels.EventType.TARGET_CONFIGURE,
                actionName=actionName,
                enabled=enabled,
                descriptorModel=self, descriptorViewName="TargetConfigurationDescriptor")
        return action

    def _actionConfigureUserCredentials(self):
        actionName = "Configure user credentials for target"
        enabled = (self.state != self.States.UNCONFIGURED)
        action = jobmodels.EventType.makeAction(
                jobTypeName=jobmodels.EventType.TARGET_CONFIGURE_CREDENTIALS,
                actionName=actionName,
                enabled=enabled,
                descriptorModel=self, descriptorViewName="TargetConfigureCredentials")
        return action

    def _actionRefreshImages(self):
        actionName = "Refresh images"
        enabled = (self.state != self.States.UNCONFIGURED)
        action = jobmodels.EventType.makeAction(
                jobTypeName=jobmodels.EventType.TARGET_REFRESH_IMAGES,
                actionName=actionName,
                enabled=enabled,
                descriptorModel=self, descriptorViewName="TargetRefreshImages")
        return action

    def _actionRefreshSystems(self):
        actionName = "Refresh systems"
        enabled = (self.state != self.States.UNCONFIGURED)
        action = jobmodels.EventType.makeAction(
                jobTypeName=jobmodels.EventType.TARGET_REFRESH_SYSTEMS,
                actionName=actionName,
                enabled=enabled,
                descriptorModel=self, descriptorViewName="TargetRefreshSystems")
        return action

    def _actionCreateLaunchProfile(self):
        actionName = "Create launch profile"
        enabled = (self._rbmgr is not None and
                self.state != self.States.UNCONFIGURED)
        if enabled:
            creds = self._rbmgr.targetsManager.getTargetCredentialsForCurrentUser(self)
            enabled &= (creds is not None)
        action = jobmodels.EventType.makeAction(
                jobTypeName=jobmodels.EventType.TARGET_CREATE_LAUNCH_PROFILE,
                actionName=actionName,
                enabled=enabled,
                descriptorModel=self, descriptorViewName="TargetCreateLaunchProfile")
        return action


    @classmethod
    def getDriverClassForTargetId(cls, targetId):
        from .manager import CatalogServiceHelper
        targetsMap = dict((x.pk, x)
            for x in modellib.Cache.all(Target))
        targetTypesMap = dict((x.pk, x)
            for x in modellib.Cache.all(TargetType))
        target = targetsMap[targetId]
        targetType = targetTypesMap[target.target_type_id]
        drvCls = CatalogServiceHelper.getDriverClass(targetType)
        return drvCls

class TargetData(modellib.XObjModel):
    class Meta:
        db_table = u'targetdata'
        
    targetdata_id = D(models.AutoField(primary_key=True, db_column='targetdataid'),
        'ID of target data')
    target = D(models.ForeignKey(Target, db_column="targetid"), 'Associated target')
    name = D(models.CharField(max_length=255, null=False), 'Data name, cannot be null')
    value = D(models.TextField(), 'Value of the data')

class TargetConfiguration(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag='target_configuration')

    view_name = 'TargetConfiguration'
    properties = []

    def __init__(self, targetId):
        self.target_id = targetId

    def serialize(self, request=None, **kwargs):
        etreeModel = modellib.XObjModel.serialize(self, request, **kwargs)
        for k, v in self.properties:
            modellib.Etree.Node(k, parent=etreeModel, text=v)
        return etreeModel

    def get_url_key(self, *args, **kwargs):
        return [self.target_id]

class Credentials(modellib.Collection):
    class Meta:
        abstract = True
    # xobj can take two list fields.  we include both here because
    # we'd like to use Credentials as the collection for both
    # TargetCredentials and TargetUserCredentials.  This is
    # necessary because I can't think of a better way to name
    # the *Credential's models to otherwise include a collection
    # for each.
    list_fields = ['target_credentials', 'target_user_credentials']
    _xobj = xobj.XObjMetadata(tag='credentials')


class TargetCredentials(modellib.XObjModel):
    class Meta:
        db_table = u'targetcredentials'
        ordering = [ 'target_credentials_id' ]
    target_credentials_id = models.AutoField(primary_key=True,
        db_column="targetcredentialsid")
    credentials = D(models.TextField(null=False, unique=True),
        'The credentials for a target, cannot be null and must be unique')

class TargetUserCredentials(modellib.XObjModel):
    target = D(models.ForeignKey(Target, db_column="targetid", related_name='_target_user_credentials'),
        'Target belonging to these credentials, unique with user')
    user = D(models.ForeignKey(usersmodels.User, db_column="userid",
        related_name='target_user_credentials'), 'User having credentials for this target, unique with target')
    target_credentials = D(models.ForeignKey('TargetCredentials',
        db_column="targetcredentialsid", related_name='target_user_credentials'),
        'Actual credentials')
    unique_together = ( target, user, )

    class Meta:
        db_table = u'targetusercredentials'

class TargetUserCredentialsModel(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag='target_user_credentials')
    user = models.ForeignKey(usersmodels.User)
    credentials = modellib.SyntheticField()

    def setCredentials(self, credentials):
        self.credentials = xobj2.Document(root=credentials, rootName='credentials')

class TargetImagesDeployed(modellib.XObjModel):
    """
    Images deployed from the rBuilder onto a target get recorded in this table
    """
    target = D(models.ForeignKey(Target, db_column="targetid"), 'Target on deployed images')
    build_file = D(models.ForeignKey(imagemodels.BuildFile, db_column='fileid'), 'The build file')
    target_image_id = D(models.CharField(max_length=128, db_column='targetimageid'),
        'The ID of the deployed target image')
    class Meta:
        db_table = u'targetimagesdeployed'

class TargetImage(modellib.XObjModel):
    """
    A representation of all images from a target
    """
    class Meta:
        db_table = "target_image"
        ordering = [ "target_image_id" ]

    _xobj_explicit_accessors = set()

    target_image_id = D(models.AutoField(primary_key=True), 
        'The target image ID')
    name = D(models.TextField(unique=True), "Image Name, must be unique")
    description = D(models.TextField(null=False), "Image Description, cannot be null")
    target = D(models.ForeignKey(Target, related_name='target_images'),
        "Target the image is part of, is unique with target_internal_id")
    target_internal_id = D(models.TextField(null=False),
        "Image identifier on the target, cannot be null, is unique with target")
    rbuilder_image_id = D(models.TextField(null=True),
        "Image identifier on the rbuilder, as reported by the target, is null by default")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the resource was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the resource was modified (UTC)")
    unique_together = (target, target_internal_id)

class TargetSystem(modellib.XObjModel):
    """
    A representation of all systems from a target
    """
    class Meta:
        db_table = "target_system"

    _xobj_explicit_accessors = set()

    target_system_id = models.AutoField(primary_key=True)
    name = D(models.TextField(unique=True), "System Name, is unique")
    description = D(models.TextField(null=False), "System Description")
    target = D(models.ForeignKey(Target, related_name='target_systems'),
        "Target the system is part of, unique with target_internal_id")
    target_internal_id = D(models.TextField(null=False), "System identifier on the target, cannot be null")
    ip_addr_1 = D(models.TextField(null=True), "IP address 1, is null by default")
    ip_addr_2 = D(models.TextField(null=True), "IP address 2, is null by default")
    state = D(models.TextField(null=False), "State, cannot be null")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the resource was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the resource was modified (UTC)")
    _credentials = XObjHidden(modellib.SyntheticField())
    unique_together = (target, target_internal_id)

class TargetDeployableImage(modellib.XObjModel):
    class Meta:
        db_table = "target_deployable_image"
        ordering = [ "target_deployable_image_id" ]

    target_deployable_image_id = models.AutoField(primary_key=True)
    target = D(models.ForeignKey(Target, related_name='target_deployable_images'),
        "Target the image is part of")
    target_image = D(models.ForeignKey(TargetImage,
        related_name='target_deployable_images', null=True),
        "Image representation on the target, is null by default")
    build_file = D(models.ForeignKey(imagemodels.BuildFile,
        related_name='target_deployable_images', db_column='file_id'),
        "Build file")

class TargetImageCredentials(modellib.XObjModel):
    """
    Links an image to the credentials that were used to fetch it
    """
    class Meta:
        db_table = "target_image_credentials"

    target_image = D(models.ForeignKey(TargetImage,
        related_name="target_image_credentials"), 'Target image, is unique with target_credentials')
    target_credentials = D(models.ForeignKey('TargetCredentials',
        related_name='target_image_credentials'), 'is unique with target_image')
    unique_together = (target_image, target_credentials)

class TargetSystemCredentials(modellib.XObjModel):
    """
    Links a system to the credentials that were used to fetch it
    """
    class Meta:
        db_table = "target_system_credentials"

    target_system = D(models.ForeignKey(TargetSystem,
        related_name="target_system_credentials"), 'Target system credentials, unique with target_credentials')
    target_credentials = D(models.ForeignKey('TargetCredentials',
        related_name='target_system_credentials'), 'The target credentials, unique with target_system')
    unique_together = (target_system, target_credentials)

class TargetTypes(modellib.Collection):
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='target_types')
    list_fields = ['target_type']


class JobTargetType(modellib.XObjModel):
    class Meta:
        db_table = u'jobs_job_target_type'

    id = models.AutoField(primary_key=True)
    job = models.ForeignKey(jobmodels.Job)
    target_type = models.ForeignKey('TargetType')


class JobTarget(modellib.XObjModel):
    class Meta:
        db_table = u'jobs_job_target'

    _xobj = xobj.XObjMetadata(tag='job_target')

    id = models.AutoField(primary_key=True)
    job = models.ForeignKey(jobmodels.Job, related_name='target_jobs')
    target = models.ForeignKey('Target')

class TargetLaunchProfiles(modellib.Collection):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(tag='launch_profiles')
    list_fields = ['launch_profiles']

class TargetLaunchProfile(modellib.XObjIdModel):
    class Meta:
        db_table = "target_launch_profile"
        unique_together = [ 'name' ]
    _xobj_explicit_accessors = set()

    _xobj = xobj.XObjMetadata(tag='launch_profile')
    id = models.AutoField(primary_key=True)
    target = D(models.ForeignKey('Target'), "Target")
    name = D(models.TextField(null=False), "Profile Name")
    description = D(models.TextField(null=False), "Profile Description")
    descriptor_data = D(modellib.XMLField(), "Descriptor data")
    created_by = D(modellib.ForeignKey(usersmodels.User, null=True,
            related_name='+', db_column='created_by',
            on_delete=models.SET_NULL),
        "User who created system")

class JobLaunchProfile(modellib.XObjModel):
    class Meta:
        db_table = 'jobs_job_launch_profile'
        unique_together = [ 'job', 'launch_profile' ]
    view_name = "TargetLaunchProfile"

    _xobj = xobj.XObjMetadata(tag='launch_profile')

    id = models.AutoField(primary_key=True)
    job = models.ForeignKey(jobmodels.Job, related_name='created_launch_profiles')
    launch_profile = models.ForeignKey(TargetLaunchProfile)

    def get_url_key(self, *args, **kwargs):
        return [self.launch_profile.target.target_id, self.launch_profile.id]

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
