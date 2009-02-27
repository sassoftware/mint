from mint.rest.modellib import Model
from mint.rest.modellib import fields
 
class FileUrl(Model):
    urlType = fields.IntegerField(isAttribute=True)
    url = fields.CharField(isText=True)


class BuildFile(Model):
    fileId   = fields.IntegerField()
    buildId  = fields.IntegerField()
    filename = fields.CharField()
    title    = fields.CharField()
    size     = fields.IntegerField()
    sha1     = fields.CharField()
    urls     = fields.ListField(FileUrl, itemName='url')

class BuildFileList(Model):
    class Meta(object):
        name = 'files'

    files = fields.ListField(BuildFile, itemName='file')


  

class Release(Model):
    id = fields.AbsoluteUrlField(isAttribute=True)
    releaseId = fields.IntegerField()
    hostname = fields.CharField()
    name = fields.CharField()
    version = fields.CharField()
    description = fields.CharField()
    builds = fields.UrlField('products.releases.builds', 
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

class Build(Model):
    id = fields.AbsoluteUrlField(isAttribute=True)
    buildId = fields.IntegerField()
    hostname = fields.CharField()
    release = fields.UrlField('products.releases', ['hostname', 'release']) 
    buildType = fields.IntegerField()
    name = fields.CharField()
    description = fields.CharField()
    troveName = fields.CharField()
    troveVersion = fields.CharField()
    troveFlavor = fields.CharField()
    troveLastChanged = fields.IntegerField()
    creator = fields.UrlField('users', 'creator') # not modifiable
    updater = fields.UrlField('users', 'updater') # not modifiable
    timeCreated = fields.DateTimeField(editable=False) # not modifiable
    timeUpdated = fields.DateTimeField(editable=False) # not modifiable
    buildCount = fields.IntegerField()
    files = fields.ModelField(BuildFileList)

    def get_absolute_url(self):
        return ('products.builds', self.hostname, str(self.buildId))

class BuildList(Model):
    class Meta(object):
        name = 'builds'

    builds = fields.ListField(Build, itemName='build')

class ReleaseList(Model):
    class Meta(object):
        name = 'releases'

    releases = fields.ListField(Release, itemName='release')

