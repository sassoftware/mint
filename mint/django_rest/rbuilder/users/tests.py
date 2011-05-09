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

from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder.users import views as usersviews
from mint.django_rest.rbuilder.users import manager as usersmanager
from mint.django_rest.rbuilder.inventory.tests import XMLTestCase

class UsersTestCase(XMLTestCase):

    fixtures = ['users']

    def testGetUsers(self):
        assert(False)
        
    def testGetUser(self):
        assert(False)
        
    def testAddUser(self):
        assert(False)
        
    def testUpdateUser(self):
        assert(False)


class UserGroupsTestCase(XMLTestCase):
    
    fixtures = ['users']
    
    def testGetUserGroups(self):
        pass
        
    def testGetUserGroup(self):
        pass
        

class UserGroupMembersTestCase(XMLTestCase):
    
    fixtures = ['users']
    
    def testGetUserGroupMembers(self):
        pass
    