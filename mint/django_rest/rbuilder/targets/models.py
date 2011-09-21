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
from mint.django_rest.rbuilder.inventory import zones as zmodels
from xobj import xobj
import sys

XObjHidden = modellib.XObjHidden

class TargetType(modellib.XObjIdModel):
    class Meta:
         db_table = 'target_types'

    _xobj_hidden_accessors = set(["jobtargettype_set"])

    target_type_id = models.AutoField(primary_key=True)
    name = D(models.TextField(unique=True), "Target Type Name")
    description = D(models.TextField(null=False), "Target Type Description")
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

    def computeSyntheticFields(self, sender, **kwargs):
        self.actions = actions = jobmodels.Actions()
        targetTypes = sorted(x.pk for x in modellib.Cache.all(TargetType))
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
    _xobj_hidden_accessors = set(
        ['targetdata_set', 'targetimagesdeployed_set', 'targetusercredentials_set', 'system_set', 'jobtarget_set'])

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

    actions = D(modellib.SyntheticField(jobmodels.Actions),
        "actions available for this target")
    jobs = modellib.SyntheticField(modellib.HrefField())

    def computeSyntheticFields(self, sender, **kwargs):
        self.actions = actions = jobmodels.Actions()
        actions.action = []
        actions.action.append(self._actionConfigureUserCredentials())
        self.jobs = modellib.HrefField("jobs")

    def _actionConfigureUserCredentials(self):
        actionName = "Configure user credentials for target"
        action = jobmodels.EventType.makeAction(
                jobTypeName=jobmodels.EventType.TARGET_CONFIGURE_CREDENTIALS,
                actionName=actionName,
                descriptorModel=self, descriptorHref="descriptor_configure_credentials")
        return action

class TargetData(modellib.XObjModel):
    class Meta:
        db_table = u'targetdata'
        
    targetdata_id = models.AutoField(primary_key=True, db_column='targetdataid')    
    target = models.ForeignKey('Target', db_column="targetid")
    name = models.CharField(max_length=255, null=False)
    value = models.TextField()

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
    target = models.ForeignKey('Target', db_column="targetid")
    user = models.ForeignKey(usersmodels.User, db_column="userid",
        related_name='target_user_credentials')
    target_credentials = models.ForeignKey('TargetCredentials',
        db_column="targetcredentialsid", related_name='target_user_credentials')
    unique_together = ( target, user, )

    class Meta:
        db_table = u'targetusercredentials'

class TargetImagesDeployed(modellib.XObjModel):
    target_id = models.ForeignKey('Target', db_column="targetid")
    file_id = models.IntegerField(null=False, db_column='fileid')
    target_image_id = models.CharField(max_length=128, db_column='targetimageid')
    class Meta:
        db_table = u'targetimagesdeployed'

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
