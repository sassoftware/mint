#
# Copyright (c) 2011 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

from mint.django_rest.rbuilder.users import models
from mint.django_rest.rbuilder.inventory.tests import XMLTestCase
from mint.django_rest.rbuilder.users import testsxml

from xobj import xobj
from lxml import etree

class UsersTestCase(XMLTestCase):

    fixtures = ['users']

    def xobjResponse(self, url):
        response = self._get(url, username="admin", password="password")
        return self.toXObj(response.content)

    def toXObj(self, xml):
        xobjModel = xobj.parse(xml)
        root_name = etree.XML(xml).tag
        return getattr(xobjModel, root_name)

    def testGetUsers(self):
        users = models.Users.objects.all()
        users_gotten = self.xobjResponse('/api/users/')
        self.assertEquals(len(list(users)), len(users_gotten))
        
    def testGetUser(self):
        user = models.User.objects.get(pk=1)
        user_gotten = self.xobjResponse('/api/users/1')
        self.assertEquals(unicode(user.user_name), user_gotten.user_name)
        self.assertEquals(unicode(user.full_name), user_gotten.full_name)
        
    def testAddUser(self):
        response = self._post('/api/users/',
            data=testsxml.users_post_xml,
            username='admin', password='password'
        )
        user_posted = self.toXObj(response.content)
        self.assertEquals(200, response.status_code)
        self.assertEquals(u'dcohn', user_posted.user_name)
        self.assertEquals(u'Dan Cohn', user_posted.full_name)
        
    def testUpdateUser(self):
        response = self._put('/api/users/1',
            data=testsxml.users_put_xml,
            username='admin', password='password')
        user_putted = self.toXObj(response.content)
        self.assertEquals(200, response.status_code)
        self.assertEquals(u'Super Devil', user_putted.full_name)
        self.assertEquals(u'fear me', user_putted.blurb)
    
    def testGetUserGroups(self):
        user_groups = models.UserGroups.objects.all()
        user_groups_gotten = self.xobjResponse('/api/user_groups/')
        self.assertEquals(len(list(user_groups)), len(user_groups_gotten))
        
    def testGetUserGroup(self):
        user_group = models.UserGroup.objects.get(pk=1)
        user_group_gotten = self.xobjResponse('/api/user_groups/1')
   
    def testGetUserGroupMembers(self):
        pass
        # user_group_members = models.UserGroupMembers.objects.get(user_group_id=1)
        #         user_group_members_gotten = self.xobjResponse('/api/user_groups/1/user_group_members')
        #         self.assertEquals(len(user_group_members_gotten), len(user_group_members))