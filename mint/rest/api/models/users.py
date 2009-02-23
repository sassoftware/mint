from mint.rest.modellib import Model
from mint.rest.modellib import fields

class UserGroupMember(Model):
    groupName = fields.CharField()
    userName = fields.CharField()
    userUrl = fields.UrlField('users', 'userName')


class User(Model):
    id = fields.AbsoluteUrlField(isAttribute=True)
    userId = fields.IntegerField(required=True)
    username = fields.CharField()
    fullName = fields.CharField()
    email = fields.EmailField()
    displayEmail = fields.EmailField()
    blurb = fields.CharField()
    active = fields.BooleanField()
    timeCreated = fields.DateTimeField()
    timeAccessed = fields.DateTimeField()
    
    def get_absolute_url(self):
        return ('users', self.username)

class UserGroupMemberList(Model):
    groups = fields.ListField(UserGroupMember, itemName='group')

class UserList(Model):
    users = fields.ListField(User, itemName='user')

