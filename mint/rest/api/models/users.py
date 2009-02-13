from mint.rest.modellib import Model
from mint.rest.modellib import fields

class UserGroupMember(Model):
    groupName = fields.CharField()
    userName = fields.CharField()
    userUrl = fields.UrlField('users', 'userName')


class User(Model):
    id = fields.IntegerField(required=True)
    url = fields.UrlField('users', 'username')
    username = fields.CharField()
    fullName = fields.CharField()
    email = fields.EmailField()
    displayEmail = fields.EmailField()
    blurb = fields.CharField()
    active = fields.BooleanField()
    timeCreated = fields.DateTimeField()
    timeAccessed = fields.DateTimeField()

class UserGroupMemberList(Model):
    groups = fields.ListField(UserGroupMember, itemName='group')

class UserList(Model):
    users = fields.ListField(User, itemName='user')

