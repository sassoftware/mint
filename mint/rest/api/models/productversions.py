from mint.rest.modellib import Model
from mint.rest.modellib import fields

class ProductVersion(Model):
    id = fields.AbsoluteUrlField(isAttribute=True)
    versionId = fields.IntegerField()
    hostname = fields.CharField()
    name = fields.CharField()
    productUrl = fields.UrlField('products', ('hostname',))
    namespace = fields.CharField()
    description = fields.CharField()
    platformLabel = fields.CharField()
    platform = fields.UrlField('products.versions.platform', 
                                ('hostname', 'name'))
    stages = fields.UrlField('products.versions.stages', ('hostname', 'name'))
    definition = fields.UrlField('products.versions.definition', ('hostname', 'name'))

    def get_absolute_url(self):
        return 'products.versions', self.hostname, self.name

class ProductVersionList(Model):
    versions = fields.ListField(ProductVersion, itemName='productVersion')
    def addProductVersion(self, id, namespace, name, description,
                          hostname):
        self.versions.append(ProductVersion(id=id, namespace=namespace,
                                            name=name, description=description,
                                            hostname=hostname))

class Stage(Model):
    name  = fields.CharField()
    label = fields.CharField()


class Stages(Model):
    stages = fields.ListField(Stage, itemName='stage')

class Platform(Model):
    name = fields.CharField()
    label = fields.CharField()
    version = fields.CharField()
