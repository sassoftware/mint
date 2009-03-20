from mint.rest.modellib import Model
from mint.rest.modellib import fields

class Platform(Model):
    name               = fields.CharField()
    label              = fields.CharField()
        
class Platforms(Model):
    platforms = fields.ListField(Platform, displayName='platform')
