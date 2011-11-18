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

import time
from lxml import etree
from xobj import xobj
from django.db.utils import IntegrityError
from django.db import connection

from conary.lib import digestlib

from mint import mint_error
from mint.django_rest.rbuilder.users import models
from mint.django_rest.rbuilder.rbac import models as rbacmodels
from mint.django_rest.rbuilder.querysets import models as querymodels
from mint.django_rest.rbuilder.rbac.tests import RbacEngine
from mint.django_rest.rbuilder.users import testsxml

class UsersTestCase(RbacEngine):

    fixtures = ['users']

    def xobjResponse(self, url):
        response = self._get(url, username="admin", password="password")
        self.failUnlessEqual(response.status_code, 200)
        return self.toXObj(response.content)

    def toXObj(self, xml):
        xobjModel = xobj.parse(xml)
        root_name = etree.XML(xml).tag
        return getattr(xobjModel, root_name)

    def testGetUsers(self):
        users = models.User.objects.all()
        users_gotten = self.xobjResponse('users')
        self.assertEquals(len(list(users)), len(users_gotten.user))

    def testGetUser(self):
        user = models.User.objects.get(pk=1)
        user_gotten = self.xobjResponse('users/1')
        self.assertEquals(unicode(user.user_name), user_gotten.user_name)
        self.assertEquals(unicode(user.full_name), user_gotten.full_name)

    @classmethod
    def _mungePassword(cls, password):
        salt = '\000' * 4
        m = digestlib.md5()
        m.update(salt)
        m.update(password)
        return salt.encode('hex'), m.hexdigest()

    def mockMint(self):
        class FakeUsers(object):
            def registerNewUser(slf, userName, password, fullName,
                    email, displayEmail, blurb, active):
                now = time.time()
                salt, pw = self._mungePassword(password)
                cu = connection.cursor()
                try:
                    cu.execute("""
                        INSERT INTO users (username, fullname, salt, passwd,
                            email, displayemail, timecreated, timeaccessed,
                            active, blurb)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        [ userName, fullName, salt, pw, email, displayEmail,
                            now, now, active, blurb ])
                except IntegrityError:
                    raise mint_error.UserAlreadyExists()
                    
            def changePassword(slf, username, password):
                salt, passwd = self._mungePassword(password)
                cu = connection.cursor()
                cu.execute(
                    "UPDATE users SET salt=%s, passwd=%s WHERE username=%s",
                    [ salt, passwd, username ])
            def _mungePassword(slf, password):
                return self._mungePassword(password)
        class FakeMintServer(object):
            def __init__(slf, *args, **kwargs):
                slf.users = FakeUsers()
            def setPassword(slf, userId, password):
                u = models.User.objects.get(pk=userId)
                slf.users.changePassword(u.user_name, password)
        from mint import server
        self.mock(server, 'MintServer', FakeMintServer)

    def testAddUser(self):
        self.mockMint()
        response = self._post('users/',
            data=testsxml.users_post_xml,
        )
        self.assertEquals(401, response.status_code)

        # Create new user, now as an admin
        xml = testsxml.users_post_xml.replace('dcohn', 'testuser001')
        response = self._post('users/',
            data=xml,
            username='admin', password='password'
        )
        self.failUnlessEqual(response.status_code, 200)
        user = self.toXObj(response.content)
        self.failUnlessEqual(user.is_admin, 'true')
        user = models.User.objects.get(user_name=user.user_name)
        self.failUnlessEqual(user.is_admin, True)

    def testAddUserWithMyQuerysets(self):
        self.mockMint()
        response = self._post('users/',
            data=testsxml.users_post_xml_can_create,
            username='admin', password='password'
        )
        self.assertEquals(200, response.status_code)

        user = self.toXObj(response.content)
        self.failUnlessEqual(user.can_create, 'true')

        # verify identity role exists
        rbacmodels.RbacRole.objects.get(
            name        = "user:%s" % user.user_name,
            is_identity = True,
        )
        # verify personal querysets exist
        sets = querymodels.QuerySet.objects.filter(
            personal_for__user_name = user.user_name
        )
        self.failUnlessEqual(len(sets), 4)
        for qs in sets:
            grants = rbacmodels.RbacPermission.objects.filter(
                queryset = qs
            )
            # should have create, modmember, and readset
            self.failUnlessEqual(len(grants), 3)

        # verify 3 grants exist for each personal queryset
        # update the user to verify that nothing is mangled
        # by re-saving with the can_create bit still set.
        response = self._put("users/%s" % user.user_id,
            data=testsxml.users_post_xml_can_create,
            username='admin', password='password'
        )
        self.failUnlessEqual(response.status_code, 200)

        # verify querysets are still present
        rbacmodels.RbacRole.objects.get(
            name        = "user:%s" % user.user_name,
            is_identity = True,
        )
 
        # now save user back without the can create
        # bit and see if things go away
        cannot_create = testsxml.users_post_xml_can_create.replace(
            '<can_create>true</can_create>',
            '<can_create>false</can_create>'
        )
        response = self._put('users/%s' % user.user_id,
            data=cannot_create,
            username='admin', password='password'
        )
        self.failUnlessEqual(response.status_code, 200)

        # verify my querysets are now missing
        sets = querymodels.QuerySet.objects.filter(
            personal_for__user_name = user.user_name
        )
        self.failUnlessEqual(len(sets), 0)
        grants = rbacmodels.RbacPermission.objects.filter(
            queryset__personal_for__user_name = user.user_name
        )
        self.failUnlessEqual(len(grants), 0)

        # reinstate can create bits
        response = self._put("users/%s" % user.user_id,
            data=testsxml.users_post_xml_can_create,
            username='admin', password='password'
        )
        self.failUnlessEqual(response.status_code, 200)
        # delete the user
        response = self._delete("users/%s" % user.user_id,
            username='admin', password='password')
        self.failUnlessEqual(response.status_code, 204)

        # model in database is now marked deleted and name
        # was changed to allow username reuse
        deletedUser = models.User.objects.get(pk=user.user_id)
        self.failUnlessEqual(deletedUser.deleted, True)
        self.assertTrue(deletedUser.user_name != user.user_name)
        response = self._get("users/%s" % user.user_id,
            username='admin', password='password')
        self.failUnlessEqual(response.status_code, 200)
        deletedUser = self.toXObj(response.content)

        # no personal querysets remain (these would prevent 
        # creation of new QSes with the same name)
        remaining = querymodels.QuerySet.objects.filter(
            personal_for__pk = deletedUser.user_id
        )
        self.failUnlessEqual(len(remaining), 0)

    def testUpdateUser(self):
        self.mockMint()
        response = self._put('users/10000',
            data=testsxml.users_put_xml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 400)

        # Unauthenticated
        response = self._put('users/1',
            data=testsxml.users_put_xml)
        self.failUnlessEqual(response.status_code, 401)

        response = self._put('users/1',
            data=testsxml.users_put_xml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        user_put = self.toXObj(response.content)
        self.assertEquals(user_put.full_name, 'Changed Full Name')
        self.assertEquals(user_put.blurb, 'fear me')

        xml = "<user><user_name>foo</user_name></user>"
        response = self._put('users/1',
            data=xml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 403)

        # Admin sets its own password
        xml = "<user><password>abc</password></user>"
        response = self._put('users/1',
            data=xml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        user = models.User.objects.get(pk=1)
        self.failUnlessEqual(user.salt, '0' * 8)

        # This is still using the old password, should fail
        xml = "<user><full_name>blabbedy</full_name></user>"
        response = self._put('users/1',
            data=xml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 401)
        # This works
        response = self._put('users/1',
            data=xml,
            username='admin', password='abc')
        self.assertEquals(response.status_code, 200)
        user = models.User.objects.get(pk=1)
        self.failUnlessEqual(user.full_name, 'blabbedy')

        # Non-admin user updates another user
        response = self._put('users/1',
            data=testsxml.users_put_xml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 403)

        xml = "<user><user_name>admin</user_name><full_name>foo</full_name></user>"
        response = self._put('users/2000',
            data=xml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 403)

        # Non-admin user updates itself
        xml = "<user><full_name>foo</full_name></user>"
        response = self._put('users/2000',
            data=xml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        user = self.toXObj(response.content)
        self.failUnlessEqual(user.full_name, 'foo')
        user = models.User.objects.get(pk=user.user_id)
        self.failUnlessEqual(user.full_name, 'foo')

        # Non-admin sets its own password
        xml = "<user><password>abcd</password></user>"
        response = self._put('users/2000',
            data=xml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        user = models.User.objects.get(pk=user.user_id)
        self.failUnlessEqual(user.salt, '0' * 8)

        # This is still using the old password, should fail
        xml = "<user><full_name>blabbedy</full_name></user>"
        response = self._put('users/2000',
            data=xml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 401)
        # This works
        response = self._put('users/2000',
            data=xml,
            username='testuser', password='abcd')
        self.assertEquals(response.status_code, 200)
        user = models.User.objects.get(pk=1)
        self.failUnlessEqual(user.full_name, 'blabbedy')

    def testUpdateUserIsAdmin(self):
        self.mockMint()

        # Non-admin user setting is_admin
        xml = "<user><is_admin>true</is_admin></user>"
        response = self._put('users/2000',
            data=xml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        user = self.toXObj(response.content)
        self.failUnlessEqual(user.is_admin, 'false')
        user = models.User.objects.get(pk=user.user_id)
        self.failUnlessEqual(user.is_admin, False)

        # admin user unsetting is_admin
        xml = "<user><is_admin>false</is_admin></user>"
        response = self._put('users/1',
            data=xml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        user = self.toXObj(response.content)
        self.failUnlessEqual(user.is_admin, 'true')
        user = models.User.objects.get(pk=1)
        self.failUnlessEqual(user.is_admin, True)

        # admin user promoting user to admin
        xml = "<user><is_admin>true</is_admin></user>"
        response = self._put('users/2000',
            data=xml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        user = self.toXObj(response.content)
        self.failUnlessEqual(user.is_admin, 'true')
        user = models.User.objects.get(pk=user.user_id)
        self.failUnlessEqual(user.is_admin, True)

        # And doing it again
        response = self._put('users/2000',
            data=xml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        user = models.User.objects.get(pk=user.user_id)
        self.failUnlessEqual(user.is_admin, True)

        # admin user demoting user from admin
        xml = "<user><is_admin>0</is_admin></user>"
        response = self._put('users/2000',
            data=xml,
            username='admin', password='password')
        user = self.toXObj(response.content)
        self.failUnlessEqual(user.is_admin, 'false')
        user = models.User.objects.get(pk=user.user_id)
        self.failUnlessEqual(user.is_admin, False)

    def testDeleteUser(self):
        # Can't delete yourself
        response = self._delete('users/1',
            username='admin', password='password')
        self.assertEquals(response.status_code, 403)
        fault = self.toXObj(response.content)
        self.failUnlessEqual(fault.code, '403')
        self.failUnlessEqual(fault.message, 'Users are not allowed to remove themselves')

        # Non-admin
        response = self._delete('users/2000',
            username='testuser', password='password')
        self.failUnlessEqual(response.status_code, 403)

        # Admin deleting another user
        response = self._delete('users/2000',
            username='admin', password='password')
        self.assertEquals(response.status_code, 204)

        # User no longer exists
        response = self._delete('users/2000',
            username='admin', password='password')
        self.assertEquals(response.status_code, 404)
        fault = self.toXObj(response.content)
        self.failUnlessEqual(fault.code, '404')
        self.failUnlessEqual(fault.message, 'The specified user does not exist')

    def testUserGetIsAdmin(self):
        user = models.User.objects.get(user_name='admin')
        self.failUnlessEqual(user.is_admin, True)
        user = models.User.objects.get(user_name='testuser')
        self.failUnlessEqual(user.is_admin, False)
        # New user, not saved yet
        user = models.User(user_name='blah')
        self.failUnlessEqual(user.is_admin, False)

    def testIsAdmin(self):
        user = self.xobjResponse('users/1')
        self.failUnlessEqual(user.is_admin, 'true')
        user = self.xobjResponse('users/2000')
        self.failUnlessEqual(user.is_admin, 'false')

    def testGetSession(self):
        # Unauthenticated. We get back an empty <user/>
        response = self._get('session')
        self.failUnlessEqual(response.status_code, 200)
        sess = self.toXObj(response.content)
        self.assertXMLEquals(xobj.toxml(sess.user, xml_declaration=False),
            "<user/>")

        # Authenticated
        response = self._get('session', username="testuser", password="password")
        self.failUnlessEqual(response.status_code, 200)
        sess = self.toXObj(response.content)
        self.failUnlessEqual(sess.user.user_id, '2000')

    def testChangePasswordAuthenticatedNonAdmin(self):
        self.mockMint()
        user = models.User()
        user.user_name = 'jphoo'
        user.full_name = 'Jim Phoo'
        user.email = 'jphoo@noreply.com'
        user.password = 'abc'
        user.deleted = False
        self.mgr.addUser(user, user)
        user = models.User.objects.get(user_name='jphoo')
        response = self._get('users/%s' % user.pk, username=user.user_name, password='abc')
        self.assertEquals(response.status_code, 200)
        
        new_password = 'cba'
        # should fail with 401, password hasn't changed yet
        response = self._get('users/%s' % user.pk, username='jphoo', password=new_password)
        self.assertEquals(response.status_code, 401)
        
        # changing password, should be 200 if everything works
        response = self._put('users/%s' % user.pk,
            username=user.user_name, password='abc', data=testsxml.user_update_password % new_password)
        self.assertEquals(response.status_code, 200)
        
        # try getting user with new password
        response = self._get('users/%s' % user.pk, username='jphoo', password=new_password)
        self.assertEquals(response.status_code, 200)
