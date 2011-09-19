#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint.rest.modellib import Model
from mint.rest.modellib import fields


class User(Model):
    id = fields.AbsoluteUrlField(isAttribute=True)
    userId = fields.IntegerField(required=True)
    username = fields.CharField()
    fullName = fields.CharField()
    email = fields.EmailField()
    displayEmail = fields.CharField()
    blurb = fields.CharField()
    active = fields.BooleanField()
    timeCreated = fields.DateTimeField()
    timeAccessed = fields.DateTimeField()
    products = fields.UrlField('users.products', 'username')

    def get_absolute_url(self):
        return ('users', self.username)


class UserList(Model):
    class Meta(object):
        name = 'users'

    users = fields.ListField(User, displayName='user')

