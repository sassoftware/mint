from mint.rest.modellib import Model
from mint.rest.modellib import fields
 
class FileUrl(Model):
    urlType = fields.IntegerField(isAttribute=True)
    url = fields.CharField(isText=True)


class ImageFile(Model):
    fileId   = fields.IntegerField()
    imageId  = fields.IntegerField()
    filename = fields.CharField()
    title    = fields.CharField()
    size     = fields.IntegerField()
    sha1     = fields.CharField()
    urls     = fields.ListField(FileUrl, displayName='url')

class ImageFileList(Model):
    class Meta(object):
        name = 'files'

    files = fields.ListField(ImageFile, displayName='file')


  

class Release(Model):
    id = fields.AbsoluteUrlField(isAttribute=True)
    releaseId = fields.IntegerField()
    hostname = fields.CharField()
    name = fields.CharField()
    version = fields.CharField()
    description = fields.CharField()
    images = fields.UrlField('products.releases.images', 
                              ['hostname', 'releaseId'])
    creator = fields.UrlField('users', 'creator') 
    updater = fields.UrlField('users', 'updater') 
    publisher = fields.UrlField('users', 'publisher') # not modifiable
    timeCreated = fields.DateTimeField(editable=False) # not modifiable
    timePublished = fields.DateTimeField(editable=False) # not modifiable
    timeMirrored = fields.DateTimeField(editable=False) # not modifiable
    timeUpdated = fields.DateTimeField(editable=False) # not modifiable
    shouldMirror = fields.BooleanField()

    def get_absolute_url(self):
        return ('products.releases', self.hostname, str(self.releaseId))

class Image(Model):
    id = fields.AbsoluteUrlField(isAttribute=True)
    imageId = fields.IntegerField()
    hostname = fields.CharField()
    release = fields.UrlField('products.releases', ['hostname', 'release']) 
    imageType = fields.CharField()
    name = fields.CharField()
    description = fields.CharField()
    troveName = fields.CharField()
    troveVersion = fields.CharField()
    trailingVersion = fields.CharField()
    troveFlavor = fields.CharField()
    troveLastChanged = fields.IntegerField()
    version = fields.UrlField('products.versions', 
                             ['hostname', 'version'])
    stage = fields.UrlField('products.versions.stages', 
                            ['hostname', 'version', 'stage'])
    creator = fields.UrlField('users', 'creator') # not modifiable
    updater = fields.UrlField('users', 'updater') # not modifiable
    timeCreated = fields.DateTimeField(editable=False) # not modifiable
    timeUpdated = fields.DateTimeField(editable=False) # not modifiable
    buildCount = fields.IntegerField()
    files = fields.ModelField(ImageFileList)

    def get_absolute_url(self):
        return ('products.images', self.hostname, str(self.imageId))

class ImageList(Model):
    class Meta(object):
        name = 'images'

    images = fields.ListField(Image, displayName='image')

class ReleaseList(Model):
    class Meta(object):
        name = 'releases'

    releases = fields.ListField(Release, displayName='release')

