from mint.rest.modellib import Model
from mint.rest.modellib import fields

class Product(Model):
    productId          = fields.IntegerField()
    hostname           = fields.CharField(required=True)
    name               = fields.CharField()
    namespace          = fields.CharField(displayName='nameSpace')
    shortname          = fields.CharField() 
    repositoryHostname = fields.CharField()
    description        = fields.CharField()
    projecturl         = fields.CharField()
    isAppliance        = fields.BooleanField(default=True)
    prodtype           = fields.CharField()
    commitEmail        = fields.EmailField(visibility='owner')
    backupExternal     = fields.BooleanField(visibility='owner')
    timeCreated        = fields.DateTimeField(editable=False)
    timeModified       = fields.DateTimeField(editable=False)
    hidden             = fields.BooleanField()
    version            = fields.CharField()
    versions           = fields.UrlField('products.versions', ['hostname'])
    members            = fields.UrlField('products.members', ['hostname'])
    creator            = fields.UrlField('users', 'creator')
    releases           = fields.UrlField('products.releases', ['hostname'])
    images             = fields.UrlField('products.images', ['hostname'])
    id                 = fields.AbsoluteUrlField(isAttribute=True)
        
    def get_absolute_url(self):
        return ('products', self.hostname)

    def getFQDN(self):
        return self.hostname + '.' + self.domainname
            
class ProductSearchResultList(Model):
    class Meta(object):
        name = 'products'

    products = fields.ListField(Product, displayName='product')

    def addProduct(self, id, hostname, name):
        self.products.append(ProductSearchResult(productId=id, 
                                                 hostname=hostname,
                                                 domainname=domainname,
                                                 name=name))
