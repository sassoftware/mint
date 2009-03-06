from mint.rest.modellib import Model
from mint.rest.modellib import fields

class Trove(Model):
    id = fields.AbsoluteUrlField(isAttribute=True)
    hostname         = fields.CharField()
    name             = fields.CharField()
    version          = fields.CharField()
    label            = fields.CharField()
    trailingVersion  = fields.CharField()
    flavor           = fields.CharField()
    timeStamp        = fields.CharField()
    images           = fields.UrlField('products.repos.items.images',
                                      ['hostname', 'nvf'])

    def getNVF(self):
        return '%s=%s[%s]' % (self.name, self.version, self.flavor)
    nvf = property(getNVF)

    def get_absolute_url(self):
        return ('products.repos.items', self.hostname, 
                 '%s=%s[%s]' % (self.name, self.version, self.flavor))

class TroveList(Model):
    class Meta(object):
        name = 'troves'
    troves   = fields.ListField(Trove, displayName='trove')
