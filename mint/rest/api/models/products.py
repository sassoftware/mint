from mint.rest.modellib import Model
from mint.rest.modellib import fields

class Product(Model):
    id = fields.IntegerField()
    hostname = fields.CharField(required=True)
    name = fields.CharField()
    namespace = fields.CharField()
    domainname = fields.CharField()
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
    hidden = fields.BooleanField()
    version = fields.CharField()
    versions = fields.UrlField('products.versions', ['hostname']) # not modifiable

    def get_absolute_url(self):
        return ('products', self.hostname)

    def getFQDN(self):
        return self.hostname + '.' + self.domainname
            
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
