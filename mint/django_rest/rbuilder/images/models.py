#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.db import models
from xobj import xobj
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.projects import models as projmodels
from django.core.urlresolvers import reverse
import urlparse

class Images(modellib.XObjIdModel):
    class Meta:
        abstract = True
    
    _xobj = xobj.XObjMetadata(tag="images")

    image_definition_descriptors = modellib.HrefField(href='./image_definition_descriptors')

class ImageDefinitionDescriptors(modellib.Collection):
    '''Collection of available image definition descriptor types'''

    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(tag="image_definition_descriptors")
    view_name = 'ImageDefinitionDescriptors'
    list_fields = [ 'image_definition_descriptor' ]

class ImageDefinitionDescriptor(modellib.XObjIdModel):
    '''Image definition descriptor for a sepcific image type'''

    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(tag='image_definition_descriptor')

    name = models.TextField()
    description = models.TextField()
    architecture = models.TextField()
    id  = modellib.HrefField()
    view_name = 'ImageDefinitionDescriptor'

    def serialize(self, request):
        xobj_model = modellib.XObjIdModel.serialize(self, request)
        xobj_model.id = self.get_absolute_url(request)
        return xobj_model

    def get_absolute_url(self, request, *args, **kwargs):
        segment =  reverse(ImageDefinitionDescriptor.view_name, args=[self.name, self.architecture])
        if request is not None:
            fullpath = request.get_full_path()
            return request.build_absolute_uri(
                urlparse.urljoin(fullpath, segment)
            )
        return segment

###########################################################################
# BELOW THIS LINE -- unfinished effort to add images into Django
# these do not have tests and this code didn't use to compile, so DO
# verify correctness of items below and add tests before using these,
# and mark which remain untested/unfinished
##########################################################################

# UNTESTED/UNUSED:        
class TargetImage(modellib.XObjIdModel): 
    class Meta:
        db_table = u'targets'
        
    target_imageid = models.AutoField(primary_key=True,
        db_column="targetid")
    target_name = models.CharField(max_length=255, db_column="targetName")
    target_type = models.CharField(max_length=255, db_column="targetType")

# UNTESTED/UNUSED:        
class FileUrl(modellib.XObjIdModel):
    class Meta:
        db_table = u'FilesUrls'
        
    file_id = models.AutoField(primary_key=True,
        db_column="urlId")  
    url_type = models.IntegerField(db_column='urlType') 
    url =  models.CharField(max_length=255)


# UNTESTED/UNUSED:        
class ImageFiles(modellib.Collection):
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(
        tag="imageFileList")
    #view_name = ""   
    
    host_name = models.CharField()
    image_id = models.IntegerField()
    #not sure how to map ModelField
    #metadata = fields.ModelField(ImageMetadata)     


# UNTESTED/UNUSED:        
class ImageFile(modellib.XObjIdModel):
    class Meta:
        db_table= u'BuildFiles'
        
    file_id = models.AutoField(primary_key=True,
        db_column="fileId")  
    imade_id = modellib.DeferredForeignKey(projmodels.Image, db_column='buildid')
    idx = models.SmallIntegerField(default=0)
    title= models.TextField()
    size     = models.BigIntegerField(null=True)
    sha1     = models.TextField(null=True)


# UNTESTED/UNUSED:        
class Urls(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['FileUrl']
    _xobj = xobj.XObjMetadata(tag='url')
    

# UNTESTED/UNUSED:        
class TargetImages(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['TargetImage']  
    
    
# UNTESTED/UNUSED:        
class Files(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['ImageFile']               
    _xobj = xobj.XObjMetadata(tag='file')

# UNTESTED/UNUSED:        
class ImageMetadata(modellib.XObjIdModel):
    class Meta:
        abstract = True
    
    #changing charFields to textField as textField has no limit    
    owner = models.TextField()
    billingCode= models.TextField()
    deptCode = models.TextField()
    cost = models.TextField()

    #copied directly from old code, not sure at all
    def getValues(self):
        vals = ((x, getattr(self, x)) for x in self._elements)
        vals = [ (x, str(y)) for (x, y) in vals if y ]
        return vals

    def __repr__(self):
        vals = self.getValues()
        return "<images.%s: %s>" % (self.__class__.__name__,
            ', '.join("%s:%s" % x for x in vals))

    def __nonzero__(self):
        return bool(self.getValues())   
        
# UNTESTED/UNUSED:        
class UpdateRelease(modellib.XObjIdModel):
    class Meta:
        abstract = True
        
    host_name= models.CharField()
    name= models.CharField(max_length=255, blank=True, default='')
    version= models.CharField(max_length=32, blank=True, default='')
    #not sure how to handle the imageIds
    #imageIds = fields.ListField(ImageId)
    description= models.TextField()
    is_published = models.BooleanField(default=False)
    should_mirror= models.BooleanField(default=False)                 


   
   
    
    
        



   
        

                
