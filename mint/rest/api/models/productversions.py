from mint.rest.modellib import Model
from mint.rest.modellib import fields

class ProductVersion(Model):
    id = fields.IntegerField()
    hostname = fields.CharField()
    name = fields.CharField()
    url = fields.AbsoluteUrlField()
    productUrl = fields.UrlField('products', ('hostname',))
    namespace = fields.CharField()
    description = fields.CharField()

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
