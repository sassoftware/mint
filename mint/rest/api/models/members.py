#!/usr/bin/python
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


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
    id         = fields.UrlField('products.members', ['hostname', 'username'],
                                 isAttribute=True)

    def __repr__(self):
        return 'models.Membership(%r, %r, %r)' % (self.hostname, self.username, self.level)

class MemberList(Model):
    class Meta(object):
        name = 'members'
    members = fields.ListField(Membership, displayName='member')
