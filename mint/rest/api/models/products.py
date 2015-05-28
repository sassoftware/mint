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


class _RepositoryUrlField(fields.AbstractUrlField):
    name = None
    def _getUrl(self, parent, context):
        base = context.request.baseUrl
        if base.endswith('/api'):
            base = base[:-4]
        return '%s/repos/%s/%s' % (base, parent.hostname, self.name)


class RepositoryRestUrlField(_RepositoryUrlField):
    name = 'api'


class Product(Model):
    productId          = fields.IntegerField()
    hostname           = fields.CharField(required=True)
    name               = fields.CharField()
    namespace          = fields.CharField(displayName='nameSpace')
    domainname         = fields.CharField()
    shortname          = fields.CharField()
    projecturl         = fields.CharField()
    repositoryHostname = fields.CharField()
    repositoryUrl      = RepositoryRestUrlField()
    description        = fields.CharField()
    prodtype           = fields.CharField()
    commitEmail        = fields.EmailField(visibility='owner')
    backupExternal     = fields.BooleanField(visibility='owner')
    timeCreated        = fields.DateTimeField(editable=False)
    timeModified       = fields.DateTimeField(editable=False)
    hidden             = fields.BooleanField()
    role               = fields.CharField()
    version            = fields.CharField()
    versions           = fields.UrlField('products.versions', ['hostname'])
    members            = fields.UrlField('products.members', ['hostname'])
    creator            = fields.UrlField('users', 'creator')
    images             = fields.UrlField('products.images', ['hostname'])
    id                 = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('products', self.hostname)

    def getFQDN(self):
        return self.repositoryHostname

    def __repr__(self):
        return 'models.Product(%r, %r)' % (self.productId,
                self.repositoryHostname)

class ProductSearchResultList(Model):
    class Meta(object):
        name = 'products'

    products = fields.ListField(Product, displayName='product')

class AuthInfo(Model):
    authType = fields.CharField()
    username = fields.CharField()
    password = fields.ProtectedField()
    entitlement = fields.CharField()
