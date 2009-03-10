from mint.rest.modellib import Model
from mint.rest.modellib import fields

class RbuilderStatus(Model):
    version       = fields.CharField()
    conaryVersion = fields.CharField()
    products      = fields.UrlField('products', None)
    users         = fields.UrlField('users', None)

from mint.rest.api.models.members import *
from mint.rest.api.models.users import *
from mint.rest.api.models.products import *
from mint.rest.api.models.productversions import *
from mint.rest.api.models.images import *
from mint.rest.api.models.repos import *
