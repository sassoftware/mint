#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.db import models
from xobj import xobj
from mint.django_rest.rbuilder import modellib
import sys
from mint.django_field.rbuilder.projects import models as projmodels


class TargetImage(modellib.XObjIdModel): 
    class Meta:
        db_table = u'targets'
        
    target_imageid = models.AutoField(primary_key=True,
        db_column="targetid")
    target_name = models.CharField(max_length=255, db_column="targetName")
    target_type = models.CharField(max_length=255, db_column="targetType")
    
    

class FileUrl(modellib.XObjIdModel):
    class Meta:
        db_table = u'FilesUrls'
        
    file_id = models.AutoField(primary_key=True,
        db_column="urlId")  
    url_type = c(db_column='urlType') 
    url =  models.CharField(max_length=255)


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


class ImageFile(modellib.XOjIdModel):
    class Meta:
        db_table= u'BuildFiles'
        
    file_id = models.AutoField(primary_key=True,
        db_column="fileId")  
    imade_id = modellib.DeferredForeignKey(projmodels.Image, db_column='buildid')
    idx = models.SmallIntegerField(default=0)
    title= models.CharField(max_length=255)
    size     = models.bigIntegerField(null=True)
    sha1     = models.CharField(max_length=40, null=True)
    fileName = models.CharField(max_lenth=255, null=True)     #column not present in the DB
 


class Urls(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['FileUrl']
    _xobj = xobj.XObjMetadata(tag='url')
    
    

class TargetImages(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['TargetImage']  
    
    
class Files(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['ImageFile']               
    _xobj = xobj.XObjMetadata(tag='file')


class ImageMetadata(modellib.XOjIdModel):
    class Meta:
        abstract = True
    
    #changing charFields to textField as textField has no limit    
    owner = models.textField()
    billingCode= models.textField()
    deptCode = models.textField()
    cost = models.textField()

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
        
        
class UpdateRelease(modellib.XObIdModel):
    class Meta:
        abstract = True
        
    host_name= models.CharField()
    name= models.CharField(max_length=255, blank=True, default='')
    version= models.CharField(max_length=32, blank=True, default='')
    #not sure how to handle the imageIds
    #imageIds = fields.ListField(ImageId)
    description= models.textField()
    is_published = models.BooleanField(default=False)
    should_mirror= models.BooleanField(default=False)                 


   
   
    
    
        



   
        

                
