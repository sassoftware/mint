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

    summary_view = [ 'name', 'description' ] 

    _xobj_explicit_accessors = set(['targets'])

    target_type_id = models.AutoField(primary_key=True)
    name = D(models.TextField(unique=True), "Target Type Name")
    description = D(models.TextField(null=False), "Target Type Description")
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
        self.jobs = modellib.HrefField("../target_jobs")

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
    _xobj_explicit_accessors = set()

    class Meta:
        db_table = u'targets'

    target_id = models.AutoField(primary_key=True, db_column='targetid')
    target_type = modellib.DeferredForeignKey(TargetType, null=False,
        related_name='targets', view_name='TargetTypeTargets')
    zone = modellib.DeferredForeignKey(zmodels.Zone, null=False,
        related_name='targets')
    name = models.TextField(null=False)
    description = models.TextField(null=False)
    unique_together = (target_type, name)
    credentials_valid = modellib.SyntheticField(models.BooleanField())
    target_user_credentials = modellib.SyntheticField()
    target_configuration = modellib.SyntheticField()

    actions = D(modellib.SyntheticField(jobmodels.Actions),
        "actions available for this target")
    jobs = modellib.SyntheticField(modellib.HrefField())
    state = XObjHidden(models.IntegerField(null=False))

    def computeSyntheticFields(self, sender, **kwargs):
        self.actions = actions = jobmodels.Actions()
        actions.action = []
        actions.action.append(self._actionConfigure())
        actions.action.append(self._actionConfigureUserCredentials())
        actions.action.append(self._actionRefreshImages())
        self.jobs = modellib.HrefFieldFromModel(self, "TargetJobs")
        self.target_user_credentials = modellib.HrefFieldFromModel(self,
            "TargetUserCredentials")
        self._setCredentialsValid()
        
    def serialize(self, request=None):
        self.target_configuration = modellib.HrefField(
            href='target_configuration')
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        return xobjModel
        

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
                descriptorModel=self, descriptorHref="descriptor_configure_credentials")
        return action

    def _actionRefreshImages(self):
        actionName = "Refresh images"
        enabled = (self.state != self.States.UNCONFIGURED)
        action = jobmodels.EventType.makeAction(
                jobTypeName=jobmodels.EventType.TARGET_REFRESH_IMAGES,
                actionName=actionName,
                enabled=enabled,
                descriptorModel=self, descriptorHref="descriptor_refresh_images")
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
        
    targetdata_id = models.AutoField(primary_key=True, db_column='targetdataid')    
    target = models.ForeignKey(Target, db_column="targetid")
    name = models.CharField(max_length=255, null=False)
    value = models.TextField()

class TargetConfiguration(modellib.XObjIdModel):
    class Meta:
        abstract = True
    
    view_name = 'TargetConfiguration'

    def __init__(self, target_id):
        self._target = Target.objects.get(pk=target_id)
        
    def serialize(self, request=None):
        xobjModel = modellib.XObjModel.serialize(self, request)
        getTargetConfig = self._rbmgr.targetsManager.getTargetConfiguration
        for k, v in getTargetConfig(self._target).items():
            setattr(xobjModel, k, v)
        return xobjModel
        
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
    target_credentials_id = models.AutoField(primary_key=True,
        db_column="targetcredentialsid")
    credentials = models.TextField(null=False, unique=True)

class TargetUserCredentials(modellib.XObjModel):
    target = models.ForeignKey(Target, db_column="targetid", related_name='_target_user_credentials')
    user = models.ForeignKey(usersmodels.User, db_column="userid",
        related_name='target_user_credentials')
    target_credentials = models.ForeignKey('TargetCredentials',
        db_column="targetcredentialsid", related_name='target_user_credentials')
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
    target = models.ForeignKey(Target, db_column="targetid")
    build_file = models.ForeignKey(imagemodels.BuildFile, db_column='fileid')
    target_image_id = models.CharField(max_length=128, db_column='targetimageid')
    class Meta:
        db_table = u'targetimagesdeployed'

class TargetImage(modellib.XObjModel):
    """
    A representation of all images from a target
    """
    class Meta:
        db_table = "target_image"

    _xobj_explicit_accessors = set()

    target_image_id = models.AutoField(primary_key=True)
    name = D(models.TextField(unique=True), "Image Name")
    description = D(models.TextField(null=False), "Image Description")
    target = D(models.ForeignKey(Target, related_name='target_images'),
        "Target the image is part of")
    target_internal_id = D(models.TextField(null=False), "Image identifier on the target")
    rbuilder_image_id = D(models.TextField(null=True),
        "Image identifier on the rbuilder, as reported by the target")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the resource was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the resource was modified (UTC)")
    unique_together = (target, target_internal_id)

class TargetDeployableImage(modellib.XObjModel):
    class Meta:
        db_table = "target_deployable_image"

    target_deployable_image_id = models.AutoField(primary_key=True)
    target = D(models.ForeignKey(Target, related_name='target_deployable_images'),
        "Target the image is part of")
    target_image = D(models.ForeignKey(TargetImage,
        related_name='target_deployable_images', null=True),
        "Image representation pn the target")
    build_file = D(models.ForeignKey(imagemodels.BuildFile,
        related_name='target_deployable_images', db_column='file_id'),
        "Build file")

class TargetImageCredentials(modellib.XObjModel):
    """
    Links an image to the credentials that were used to fetch it
    """
    class Meta:
        db_table = "target_image_credentials"

    target_image = models.ForeignKey(TargetImage,
        related_name="target_image_credentials")
    target_credentials = models.ForeignKey('TargetCredentials',
        related_name='target_image_credentials')
    unique_together = (target_image, target_credentials)

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


for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
