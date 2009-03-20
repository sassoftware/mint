from mint.rest.modellib import Model
from mint.rest.modellib import fields

#TODO: We've got a conflict - PlatformName here vs. Platform which is the
# platform used by the product definition.

class PlatformName(Model):
    name               = fields.CharField()
    label              = fields.CharField()
        
class PlatformsNames(Model):
    platforms = fields.ListField(Platform2, displayName='platformName')
