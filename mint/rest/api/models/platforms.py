import products
from mint.rest.modellib import Model
from mint.rest.modellib import fields

class Platform(Model):
    hostname = fields.CharField()
    platformTroveName = fields.CharField()
    label = fields.CharField()
    platformVersion = fields.CharField()
    productVersion = fields.CharField()
    platformName = fields.CharField()
    enabled = fields.BooleanField()
    repositoryUrl  = products.RepositoryRestUrlField()

class Platforms(Model):
    platforms = fields.ListField(Platform, displayName='platform')
