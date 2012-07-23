#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

# Image models -- may be heavily in flux as Target service evolves
# or may be replaced by target service.  Don't get attached.
# **THESE ARE CURRENTLY JUST STUBS TO UNBLOCK DEVELOPMENT**

from mint import buildtypes
from django.core.urlresolvers import reverse
from django.db import models
from mint import helperfuncs
from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from xobj import xobj
from conary import trovetup
from conary import versions
from conary.deps import deps
import sys
from mint.django_rest.rbuilder.images.manager import models_manager
from mint.django_rest.rbuilder.jobs import models as jobmodels

APIReadOnly = modellib.APIReadOnly

class Images(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['image']
    _xobj = xobj.XObjMetadata(tag='images', attributes={'id':str})
    
    actions = D(modellib.SyntheticField('jobs.Actions'),
        "actions available on the images")

    def get_url_key(self, *args, **kwargs):
        return self.url_key

class BuildLogHref(modellib.HrefFieldFromModel):
    def __init__(self, model):
        modellib.HrefFieldFromModel.__init__(self, model)

    def serialize_value(self, request=None):
        "Extracts the URL from the given model and builds an href from it"
        url = self.model.get_absolute_url(request)
        url = self._getRelativeHref(url=url)
        return modellib.XObjHrefModel(url + '/build_log')

class ImageTypes(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['image_type']

class ImageType(modellib.XObjIdModel):
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='image_type', attributes={'id':str})

    objects = models_manager.ImageTypeManager()
    image_type_id = D(models.IntegerField(), 'The id of the image type')
    key = D(models.CharField(), 'Key to image type')
    name = D(models.CharField(), 'Image type name')
    description = D(models.CharField(), 'Description')

    ImageTypeKeys = dict((y, x) for (x, y) in buildtypes.validBuildTypes.items())

    @classmethod
    def fromImageTypeId(cls, imageTypeId):
        # if imageTypeId is not known, we return an empty object
        return cls(
            image_type_id = imageTypeId,
            key = cls.ImageTypeKeys.get(imageTypeId),
            name = buildtypes.typeNamesShort.get(imageTypeId),
            description = buildtypes.typeNamesMarketing.get(imageTypeId))

    @classmethod
    def fromXobjModel(cls, xobjModel):
        imageTypeId = getattr(xobjModel, 'image_type_id', None)
        if imageTypeId is None:
            # Look up by key
            key = getattr(xobjModel, 'key', None)
            if key:
                imageTypeId = cls.ImageTypeKeys.get(key)
        else:
            # Get rid of xobj strings
            imageTypeId = str(imageTypeId)
        return cls.fromImageTypeId(imageTypeId)

    def get_url_key(self):
        return [ self.image_type_id ]

class Image(modellib.XObjIdModel):
    class Meta:
        db_table = u'builds'

    view_name ='Image'

    _xobj = xobj.XObjMetadata(tag='image')
    _xobj_explicit_accessors = set(['files'])
    _queryset_resource_type = 'image'

    def __unicode__(self):
        return self.name

    # FIXME: images need descriptions fleshed out so filter descriptors
    # and comments will be sensible

    image_id = D(models.AutoField(primary_key=True, db_column='buildid'), 'ID of image')
    project = D(modellib.DeferredForeignKey('projects.Project', db_column='projectid',
        related_name="images", view_name="ProjectImages"), 'Project attached to the image')
    # The images need to be linked to the project branch stages and the project
    # Until then, hide project_branch_stage. 
    # SERIOUSLY, THIS VALUE IS NULL BECAUSE NOTHING SETS IT, DO NOT ATTEMPT TO USE!
    project_branch_stage = modellib.XObjHidden(
        modellib.DeferredForeignKey('projects.Stage', db_column='stageid',
        related_name="images", view_name="ProjectBranchStageImages", null=True))
    release = D(modellib.ForeignKey('projects.Release', null=True,
        db_column='pubreleaseid', related_name="images", view_name='ProjectReleaseImages'),
        'Release attached to the image, by default is null')
    _image_type = modellib.XObjHidden(APIReadOnly(
        models.IntegerField(db_column="buildtype")))
    image_type = modellib.SyntheticField()

    job_uuid = D(models.CharField(max_length=64, null=True), 'ID of job to do, by default is null')
    name = D(models.CharField(max_length=255, null=True),
            "Image name, by default is null", short="Image name")
    description = D(models.TextField(null=True),
            "Image description, by default is null", short="Image description")
    trove_name = D(models.CharField(max_length=128, null=True,
        db_column='trovename'), "Image trove name, by default is null", short="Image trove name")
    trove_version = D(models.CharField(max_length=255, null=True,
        db_column='troveversion'), "Image trove version, by default is null", short="Image trove version")
    trove_flavor = D(models.CharField(max_length=4096, null=True,
        db_column='troveflavor'), "Image trove flavor, by default is null", short="Image trove flavor")
    trove_last_changed = D(modellib.DecimalTimestampField(null=True,
            db_column='trovelastchanged'),
            "Image trove last changed, by default is null", short="Image trove last changed")
    output_trove = D(models.TextField(null=True),
    "Image output trove, by default is null", short="Image output trove")
    time_created = D(modellib.DecimalTimestampField(db_column='timecreated'), "Image time created", short="Image time created")
    created_by = D(modellib.ForeignKey('users.User',
        db_column='createdby',null=True, related_name='created_images'), "Image created by", short="Image created by")
    time_updated = D(modellib.DecimalTimestampField(
        null=True, db_column='timeupdated'), "Image time updated", short="Image time updated")
    updated_by = D(modellib.ForeignKey('users.User', db_column='updatedby',
        related_name='updated_images', null=True), "Image updated by, by default is null", short="Image updated by")
    image_count = D(models.IntegerField(null=True, default=0,
        db_column="buildcount"), "Image count, by default is null", short="Image count")
    project_branch = D(models.ForeignKey('projects.ProjectVersion', null=True,
        related_name="images",
        db_column='productversionid'), 'Project Branch attached to the image, by default is null')
    stage_name = D(models.CharField(max_length=255, db_column='stagename',
        null=True, blank=True, default=''), "Image stage name, by default is null", short="Image stage name")
    status = D(models.IntegerField(null=True, default=-1), "Image status, by default is null", short="Image status")
    status_message = D(models.TextField(null=True, blank=True, default='',
        db_column="statusmessage"), "Image status message, by default is null", short="Image status message")
    base_image = D(modellib.DeferredForeignKey('Image', null=True,
        related_name='layered_images', db_column='base_image'), "Image base image, by default is null", short="Image base image")

    metadata = D(modellib.SyntheticField(), "Image metadata", short="Image metadata")
    architecture = D(modellib.SyntheticField(), "Image architecture", short="Image architecture")
    trailing_version = modellib.SyntheticField()
    released = modellib.SyntheticField()
    num_image_files = D(modellib.SyntheticField(), "Image file count", short="Image file count")
    build_log = modellib.SyntheticField()
    actions = D(modellib.SyntheticField(jobmodels.Actions),
        "actions available on the system")
    jobs = D(modellib.SyntheticField(modellib.HrefField()),
        "jobs for this system")
    upload_files = D(modellib.SyntheticField(modellib.HrefField()),
        "Upload image files by POSTing them to this URL")

    def computeSyntheticFields(self, sender, **kwargs):
        self._computeMetadata()

        if self.trove_flavor is not None:
            self.architecture = helperfuncs.getArchFromFlavor(str(self.trove_flavor))

        if self.trove_version is not None:
            tv_obj = helperfuncs.parseVersion(self.trove_version)
            if tv_obj is not None:
                self.trailing_version = str(tv_obj.trailingRevision())

        if self.release is not None:
            self.released = True
        else:
            self.released = False

        if self.files is not None:
            self.num_image_files = len(self.files.all())
        else:
            self.num_image_files = 0;

        self.build_log = self._getBuildLog()

        if self._image_type is not None:
            self.image_type = ImageType.fromImageTypeId(self._image_type)
        self.jobs = modellib.HrefFieldFromModel(self, "ImageJobs")

        image_data = ImageData.objects.filter(image=self.image_id,
                                              name="outputToken")
        if image_data:
            outputToken = image_data[0].value
            self.upload_files = modellib.HrefField(
                href= reverse('ImageUpload', args=[self.image_id, outputToken]))

        self._computeActions()

    def _getBuildLog(self):
        return BuildLogHref(self)

    def getMetadata(self):
        troveTup = self._getOutputTrove()
        if self._rbmgr is None or troveTup is None:
            return
        reposMgr = self._rbmgr.restDb.productMgr.reposMgr
        metadata = reposMgr.getKeyValueMetadata([troveTup])[0]
        return metadata

    def _computeMetadata(self):
        metadata = self.getMetadata()
        if metadata is None:
            return
        metaxml = xobj.XObj()
        for key, value in metadata.items():
            setattr(metaxml, key, value)
        self.metadata = metaxml

    def saveMetadata(self):
        if (self._rbmgr is None or self.output_trove is None
                or self.metadata is None):
            return
        # Commit a new image trove with updated metadata to repository and save
        # its NVF back to the output_trove field.
        metadata = self._getMetadataDict()
        oldTup = self._getOutputTrove()
        reposMgr = self._rbmgr.restDb.productMgr.reposMgr
        newTup = reposMgr.updateKeyValueMetadata([(oldTup, metadata)],
                admin=True)[0]
        self.output_trove = newTup.asString()
        self.save()
        # Log new image tuple
        msg = "Updated image committed as %s=%s/%s" % (newTup.name,
                newTup.version.trailingLabel(),
                newTup.version.trailingRevision())
        self._rbmgr.restDb.imageMgr._getImageLogger(self.project.short_name,
                self.image_id).info(msg)

    def _getOutputTrove(self):
        if self.output_trove is None:
            return None
        name, version, flavor = trovetup.TroveSpec.fromString(self.output_trove)
        version = versions.VersionFromString(version)
        if flavor is None:
            flavor = deps.Flavor()
        return trovetup.TroveTuple(name, version, flavor)

    def _getMetadataDict(self):
        if self.metadata is None:
            return None
        metadataDict = {}
        for name, value in self.metadata.__dict__.items():
            if name.startswith('_'):
                continue
            metadataDict[name] = str(value)
        return metadataDict

    def save(self):
        if self.image_type is not None:
            imageType = ImageType.fromXobjModel(self.image_type)
            if self._image_type != imageType.image_type_id:
                self._image_type = imageType.image_type_id
        return modellib.XObjIdModel.save(self)

    def _computeActions(self):
        if self._image_type == buildtypes.DEFERRED_IMAGE and self.base_image:
            self.actions = self._computeActionsForImage(self.base_image)
        else:
            self.actions = self._computeActionsForImage(self)

    def _computeActionsForImage(self, image):
        # Lazy import to prevent circular imports
        from mint.django_rest.rbuilder.targets import models as tgtmodels

        # Prime caches
        modellib.Cache.all(tgtmodels.TargetType)
        targets = modellib.Cache.all(tgtmodels.Target)

        # XXX avoid loading drivers, so for now we're whitelisting
        # target types that can deploy images
        targetTypesWithDeployImage = set(
            modellib.Cache.get(tgtmodels.TargetType, name=x).target_type_id
            for x in [ 'vmware', 'vcloud' ])
        targetsWithDeployImage = set(x.target_id for x in targets
            if x.target_type_id in targetTypesWithDeployImage)

        targetsWithCredentials = set()
        if self._rbmgr is not None:
            targetsWithCredentials.update(x.target_id
                for x in tgtmodels.TargetUserCredentials.objects.filter(
                    user=self._rbmgr.user))
        actions = jobmodels.Actions()
        actions.action = []
        # XXX FIXME REALLY BADLY: this needs to be cached
        uqDeploy = dict()
        uqLaunch = dict()
        for bfile in image.files.all():
            for tdi in bfile.target_deployable_images.all():
                # If target_image_id is None, the image is not deployed,
                # so we need to enable the action
                targetId = tdi.target_id
                enabled = targetId in targetsWithCredentials
                uqLaunch[tdi.target_id] = (bfile.file_id, enabled)
                enabled = enabled and targetId in targetsWithDeployImage
                uqDeploy[tdi.target_id] = (bfile.file_id, enabled)
        for targetId, (buildFileId, enabled) in sorted(uqDeploy.items()):
            tgt = modellib.Cache.get(tgtmodels.Target, pk=targetId)
            tgtType = modellib.Cache.get(tgtmodels.TargetType, pk=tgt.target_type_id)
            actionName = "Deploy image on '%s' (%s)" % (tgt.name, tgtType.name)
            action = jobmodels.EventType.makeAction(
                jobmodels.EventType.TARGET_DEPLOY_IMAGE,
                actionName=actionName,
                actionDescription=actionName,
                descriptorModel=tgt,
                descriptorHref="descriptors/deploy/file/%s" % ( buildFileId, ),
                enabled=enabled, resources = [ tgt ])
            actions.action.append(action)

        for targetId, (buildFileId, enabled) in sorted(uqLaunch.items()):
            tgt = modellib.Cache.get(tgtmodels.Target, pk=targetId)
            tgtType = modellib.Cache.get(tgtmodels.TargetType, pk=tgt.target_type_id)
            actionName = "Launch system on '%s' (%s)" % (tgt.name, tgtType.name)
            action = jobmodels.EventType.makeAction(
                jobmodels.EventType.TARGET_LAUNCH_SYSTEM,
                actionName=actionName,
                actionDescription=actionName,
                descriptorModel=tgt,
                descriptorHref="descriptors/launch/file/%s" % (buildFileId),
                enabled=enabled, resources = [ tgt ])
            actions.action.append(action)

        actionName = "Cancel image build"
        enabled = (self.status < 200)
        action = jobmodels.EventType.makeAction(
            jobmodels.EventType.IMAGE_CANCEL_BUILD,
            actionName=actionName,
            actionDescription=actionName,
            descriptorModel=self,
            descriptorHref="descriptors/cancel_build",
            enabled=enabled)
        actions.action.append(action)

        return actions

class BuildFiles(modellib.Collection):
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='files')
    list_fields = ['file']
    metadata = modellib.SyntheticField()

class BuildFile(modellib.XObjIdModel):
    class Meta:
        db_table = 'buildfiles'

    _xobj_explicit_accessors = set()
    _xobj = xobj.XObjMetadata(tag='file')

    file_id = D(models.AutoField(primary_key=True, db_column='fileid'), 'ID of the build file')
    image = D(models.ForeignKey('Image', null=False, db_column='buildid', related_name='files'),
                'Image attached to the Build File, cannot be null')
    idx = D(models.IntegerField(null=False, default=0), 'cannot be null, default is 0')
    title = D(models.CharField(max_length=255, null=False), 'File title')
    size = D(models.IntegerField(), 'Size of file')
    sha1 = D(models.CharField(max_length=40),
        'sha1 associated with the build file, max length is 40 characters')
    file_name = modellib.SyntheticField()
    url = modellib.SyntheticField()
    target_images = modellib.XObjHidden(modellib.SyntheticField())

    def serialize(self, request=None):
        fileUrls = BuildFilesUrlsMap.objects.filter(file=self.file_id
                ).order_by('url').all()
        if fileUrls and request:
            # Not actually a URL, but a path to the image file.
            fileUrl = fileUrls[0].url
            self.url = request.build_absolute_uri(
                    '/downloadImage?fileId=%d&urlType=%d' % (self.file_id,
                        fileUrl.url_type))
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        return xobjModel


class ImageData(modellib.XObjIdModel):
    class Meta:
        db_table = 'builddata'
        unique_together = ('image', 'name')

    image_data_id = models.AutoField(primary_key=True, db_column='builddataid')
    image = D(models.ForeignKey('Image', db_column='buildid', related_name="image_data"),
            'Attached image, is unique with name')
    name = D(models.CharField(max_length=32, null=False),
        'Name for image data, unique with image, max length is 32')
    value = D(models.TextField(), 'Image data value')
    data_type = D(models.SmallIntegerField(null=False, db_column='datatype'),
            'The data type assigned to the given image data, cannot be null')

class FileUrl(modellib.XObjIdModel):
    class Meta:
        db_table = 'filesurls'

    _xobj = xobj.XObjMetadata(tag='file_url')
    _xobj_explicit_accessors = set(['downloads'])

    file_url_id = D(models.AutoField(primary_key=True, db_column='urlid'), 'File url ID')
    url_type = D(models.SmallIntegerField(null=False, db_column='urltype'),
        'File type, is integer')
    url = D(models.CharField(max_length=255, null=False), 'Fully qualified url, cannot be null')


class BuildFilesUrlsMap(modellib.XObjModel):
    class Meta:
        db_table = 'buildfilesurlsmap'
        unique_together = ('file', 'url')
    
    build_files_urls_map_id = models.AutoField(primary_key=True, db_column='buildfilesurlsmapid')
    file = models.ForeignKey(BuildFile, null=False, db_column='fileid',
        related_name='urls_map')
    url = models.ForeignKey(FileUrl, null=False, db_column='urlid',
        related_name='urls_map')

class JobImage(modellib.XObjModel):
    class Meta:
        db_table = u'jobs_job_image'

    _xobj = xobj.XObjMetadata(tag='job_image')

    id = D(models.AutoField(primary_key=True), 'Job image ID')
    job = D(models.ForeignKey(jobmodels.Job, null=False, related_name='images'),
        'Job attached to the job image, cannot be null')
    image = D(models.ForeignKey(Image, null=False, related_name='_jobs'),
        'Image for the job, cannot be null')

class AuthTokens(modellib.XObjModel):
    class Meta:
        db_table = 'auth_tokens'
    id = D(models.AutoField(primary_key=True, db_column='token_id'),
            'Token ID')
    token = D(models.TextField(null=False, unique=True),
            'Token string')
    expires_date = D(modellib.DateTimeUtcField(null=False),
            'Token expiration date')
    user = D(modellib.ForeignKey('users.User', null=False,
            related_name='auth_tokens'),
            'User owning the token')
    image = D(modellib.ForeignKey(Image, null=True, related_name='auth_tokens'),
            'Image related to the token')

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj   
