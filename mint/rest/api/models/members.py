from mint.rest.modellib import Model
from mint.rest.modellib import fields

class UpdateMembership(Model):
    level      = fields.CharField()

class Membership(Model):
    hostname   = fields.CharField()
    productUrl = fields.UrlField('products', 'hostname')
    userUrl    = fields.UrlField('users', 'username')
    username   = fields.CharField()
    level      = fields.CharField()

class MemberList(Model):
    members = fields.ListField(Membership, itemName='member')
