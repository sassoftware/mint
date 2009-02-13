from mint.rest.modellib import Model
from mint.rest.modellib import fields

class Product(Model):
    id = fields.IntegerField()
    hostname = fields.CharField(required=True)
    name = fields.CharField()
    url = fields.AbsoluteUrlField() # not modifiable
    shortname = fields.CharField() 
    description = fields.CharField()
    projecturl = fields.CharField()
    isAppliance = fields.BooleanField(default=True)
    prodtype = fields.CharField()
    commitEmail = fields.EmailField(visibility='owner')
    backupExternal = fields.BooleanField(visibility='owner')
    creator    = fields.CharField(editable=False) # not modifiable
    creatorUrl = fields.UrlField('users', 'creator') # not modifiable
    timeCreated = fields.DateTimeField(editable=False) # not modifiable
    timeModified = fields.DateTimeField(editable=False) # not modifiable
    versions = fields.UrlField('products.versions', ['hostname']) # not modifiable

    def get_absolute_url(self):
        return ('products', self.hostname)
            
class ProductSearchResult(Model):
    id = fields.IntegerField(required=True)
    hostname = fields.CharField(required=True)
    name = fields.CharField()
    url = fields.AbsoluteUrlField()

    def get_absolute_url(self):
        return ('products', self.hostname)

class ProductSearchResultList(Model):
    products = fields.ListField(ProductSearchResult, itemName='product')
    def addProduct(self, id, hostname, name):
        self.products.append(ProductSearchResult(id=id, hostname=hostname,
                                                 name=name))

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


