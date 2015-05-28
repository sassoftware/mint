#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from mint import jobstatus

from mint.rest.modellib import Model
from mint.rest.modellib import fields

class FileUrl(Model):
    fileId = fields.IntegerField(isAttribute=True, display=False)
    urlType = fields.IntegerField(isAttribute=True)
    # It is a bit weird that a field is set to be both isAttribute and isText
    # But this is because xobj only sets the text value of a node if it
    # contains no child elements (i.e. all fields are attributes).
    # This won't cause problems on the way out, because we test for isText
    # before we attempt to write the field as an attribute.
    url = fields.ImageDownloadField(isAttribute=True, isText=True)

    def __repr__(self):
        return "images.FileUrl(fileId=%r, urlType=%r)" % (self.fileId, self.urlType)

class TargetImage(Model):
    targetType = fields.CharField()
    targetName = fields.CharField()
    targetImageId = fields.CharField()

class ImageFile(Model):
    fileId   = fields.IntegerField()
    imageId  = fields.IntegerField(display=False)
    idx      = fields.IntegerField(display=False)
    title    = fields.CharField()
    size     = fields.IntegerField()
    sha1     = fields.CharField()
    fileName = fields.CharField()
    urls     = fields.ListField(FileUrl, displayName='url')
    targetImages = fields.ListField(TargetImage)

    def __repr__(self):
        return "images.ImageId(fileId=%r, size=%r)" % (self.fileId, self.size)


class ImageFileList(Model):
    class Meta(object):
        name = 'files'

    id = fields.AbsoluteUrlField(isAttribute=True)
    hostname = fields.CharField(display=False)
    imageId = fields.IntegerField(display=False)
    files = fields.ListField(ImageFile, displayName='file')

    def get_absolute_url(self):
        return ('products.images.files', self.hostname, str(self.imageId))


class ImageId(Model):
    class Meta(object):
        name = 'image'
    id = fields.AbsoluteUrlField(isAttribute=True)
    imageId = fields.IntegerField()


class ImageStatus(Model):
    id = fields.AbsoluteUrlField(isAttribute=True)
    hostname = fields.CharField(display=False)
    imageId = fields.IntegerField(display=False)
    code = fields.IntegerField()
    message = fields.CharField()
    isFinal = fields.BooleanField(editable=False)

    def __init__(self, *args, **kwargs):
        Model.__init__(self, *args, **kwargs)
        self.set_status()

    def get_absolute_url(self):
        return ('products.images.status', self.hostname, str(self.imageId))

    def set_status(self, code=None, message=None):
        if code is not None:
            self.code = code
        if message is not None:
            self.message = message
        elif code is not None:
            # Use a default message if the code changed but no message was
            # provided.
            self.message = jobstatus.statusNames[self.code]
        self.isFinal = self.code in jobstatus.terminalStatuses

class Image(Model):
    id = fields.AbsoluteUrlField(isAttribute=True)
    imageId = fields.IntegerField()
    hostname = fields.CharField()
    imageType = fields.CharField()
    imageTypeName = fields.CharField()
    name = fields.CharField()
    description = fields.CharField()
    architecture = fields.CharField()
    troveName = fields.CharField()
    troveVersion = fields.VersionField()
    trailingVersion = fields.CharField()
    troveFlavor = fields.FlavorField()
    troveLastChanged = fields.DateTimeField()
    version = fields.UrlField('products.versions', 
                             ['hostname', 'version'])
    stage = fields.UrlField('products.versions.stages', 
                            ['hostname', 'version', 'stage'])
    creator = fields.UrlField('users', 'creator') # not modifiable
    updater = fields.UrlField('users', 'updater') # not modifiable
    timeCreated = fields.DateTimeField(editable=False) # not modifiable
    timeUpdated = fields.DateTimeField(editable=False) # not modifiable
    buildCount = fields.IntegerField()
    buildLog = fields.UrlField('products.images.buildLog',
            ['hostname', 'imageId'])
    imageStatus = fields.ModelField(ImageStatus)
    files = fields.ModelField(ImageFileList)
    baseFileName = fields.CharField()

    # TODO: we want to expose all buildData via a dict.  But that requires
    # a DictField which doesn't exist yet.
    amiId    = fields.CharField()

    def get_absolute_url(self):
        return ('products.images', self.hostname, str(self.imageId))

    def hasBuild(self):
        return self.imageType not in (None, 'imageless')

    def getNameVersionFlavor(self):
        return self.troveName, self.troveVersion, self.troveFlavor

    def __repr__(self):
        return "models.Image(%s, %r, '%s=%s[%s]')" % (
                    self.imageId, self.imageType,
                    self.troveName, self.troveVersion, self.troveFlavor)
                                                     

class ImageList(Model):
    class Meta(object):
        name = 'images'

    images = fields.ListField(Image, displayName='image')
