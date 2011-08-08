#import base64
#import cPickle
#import datetime
#import os
#import random
#from dateutil import tz
import testsxml
from xobj import xobj
#
#from conary import versions
#from conary.conaryclient.cmdline import parseTroveSpec
#
#from django.contrib.redirects import models as redirectmodels
#from django.db import connection
#from django.template import TemplateDoesNotExist

#from mint.django_rest.rbuilder import models as rbuildermodels
#from mint.django_rest.rbuilder.rbac import views
from mint.django_rest.rbuilder.rbac import models
#from mint.django_rest.rbuilder.manager import rbuildermanager
from mint.django_rest.rbuilder.users import models as usersmodels
#from mint.django_rest.rbuilder.inventory import models
#from mint.django_rest.rbuilder.jobs import models as jobmodels
#from mint.django_rest.rbuilder.inventory import testsxml
#from mint.lib import x509
#from mint.rest.api import models as restmodels

# Suppress all non critical msg's from output
# still emits traceback for failed tests
import logging
logging.disable(logging.CRITICAL)

from mint.django_rest import test_utils
XMLTestCase = test_utils.XMLTestCase

class RbacTestCase(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)

    def _xobj_list_hack(self, item):
        '''
        xobj hack: obj doesn't listify 1 element lists
        don't break tests if there is only 1 action
        '''
        if type(item) != type(item):
            return [item]
        else:
            return item

    def req(self, url, method='GET', expect=200, is_authenticated=False, is_admin=False, **kwargs):
        '''Test a HTTP operation and it's return value, return the contents'''
        method_map = {
           'GET'    : self._get,
           'POST'   : self._post,
           'DELETE' : self._delete,
           'PUT'    : self._put
        }
        
        if is_admin:
             response = method_map[method](url, username="admin", password="password", **kwargs)
        elif is_authenticated:
             response = method_map[method](url, username="testuser", password="password", **kwargs)
        else:
             response = method_map[method](url, **kwargs)
        if response.status_code != expect:
             print "RESPONSE: %s\n" % response.content
        self.failUnlessEqual(response.status_code, expect, "Expected status code of %s for %s" % (expect, url))
        return response.content

class RbacBasicTestCase(RbacTestCase):

    #def setUp(self):
    #    # just a stub for later...
    #    XMLTestCase.setUp(self)
    #    pass

    def testModelsForRbacRoles(self):
        '''verify django models for roles work'''

        sysadmin = models.RbacRole(pk='sysadmin')
        sysadmin.save()
        developer = models.RbacRole(pk='developer')
        developer.save()

        self.assertEquals(len(models.RbacRole.objects.all()), 2,
            'correct number of results'
        )

        developer2 = models.RbacRole.objects.get(pk='developer')
        self.assertEquals(developer2.role_id, 'developer', 
            'object fetched correctly'
        )

    def testModelsForRbacContexts(self):
        datacenter = models.RbacContext(pk='datacenter')
        datacenter.save()
        desktops = models.RbacContext(pk='desktops')
        desktops.save()
        self.assertEquals(len(models.RbacContext.objects.all()), 2,
           'correct number of results'
        ) 
        desktops2 = models.RbacContext.objects.get(pk='desktops')
        self.assertEqual(desktops2.context_id, 'desktops',
           'fetched correctly'
        )

    def testModelsForRbacPermissions(self):
        context1 = models.RbacContext(pk='datacenter')
        context1.save()
        role1    = models.RbacRole(pk='sysadmin')
        role1.save() 
        action_name = 'speak freely'
        permission = models.RbacPermission(
           rbac_context    = context1,
           rbac_role       = role1,
           # TODO: add choice restrictions
           action     = action_name,
        )
        permission.save()
        permissions2 = models.RbacPermission.objects.filter(
           rbac_context = context1
        )
        self.assertEquals(len(permissions2), 1, 'correct length')
        found = permissions2[0]
        self.assertEquals(found.action, action_name, 'saved ok')
        self.assertEquals(found.rbac_context.pk, 'datacenter', 'saved ok')
        self.assertEquals(found.rbac_role.pk, 'sysadmin', 'saved ok')

    def testModelsForUserRoleAssignment(self):
        # note -- we may also keep roles in AD, this is for the case
        # where we sync them or manage them internally.  This will 
        # probably need to be configurable
        # TODO -- test many to many relation in user
        user1 = usersmodels.User(
            user_name = "test",
            full_name = "test"
        )
        user1.save()
        role1 = models.RbacRole(pk='sysadmin')
        role1.save()
        mapping = models.RbacUserRole(
            user = user1,
            role = role1
        ) 
        mapping.save()
        mappings2  = models.RbacUserRole.objects.filter(
            user = user1
        )
        self.assertEquals(len(mappings2), 1, 'correct length')
        found = mappings2[0]
        self.assertEquals(found.user.user_name, 'test', 'saved ok')
        self.assertEquals(found.role.pk, 'sysadmin', 'saved ok')

    def testModelsForSystemContextAssignment(self):
        pass

class RbacRoleViews(RbacTestCase):

    def setUp(self):
        RbacTestCase.setUp(self)
        self.seed_data = [ 'sysadmin', 'developer', 'intern' ]
        for item in self.seed_data:
            models.RbacRole(item).save()
       
    def testCanListRoles(self):

        url = 'rbac/roles'
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)

        obj = xobj.parse(content)
        found_items = self._xobj_list_hack(obj.rbac_roles.rbac_role)
        found_items = [ item.role_id for item in found_items ] 
        for expected in self.seed_data:
            self.assertTrue(expected in found_items, 'found item')
        self.assertEqual(len(found_items), len(self.seed_data), 'right number of items')
        self.assertXMLEquals(content, testsxml.role_list_xml)
 
    def testCanGetSingleRole(self):

        url = 'rbac/roles/developer'
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        obj = xobj.parse(content)
        self.assertEqual(obj.rbac_role.role_id, 'developer')
        self.assertXMLEquals(content, testsxml.role_get_xml)

    def testCanAddRoles(self):
        
        url = 'rbac/roles'
        input = testsxml.role_put_xml_input   
        output = testsxml.role_put_xml_output
        content = self.req(url, method='POST', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='POST', data=input, expect=200, is_admin=True)
        found_items = models.RbacRole.objects.get(pk='rocketsurgeon')
        self.assertEqual(found_items.pk, 'rocketsurgeon')
        self.assertXMLEquals(content, output)

    def testCanDeleteRoles(self):

        url = 'rbac/roles/sysadmin'
        self.req(url, method='DELETE', expect=401, is_authenticated=True)
        self.req(url, method='DELETE', expect=204, is_admin=True)
        self.failUnlessRaises(models.RbacRole.DoesNotExist,
            lambda: models.RbacRole.objects.get(pk='sysadmin'))

    def testCanUpdateRoles(self):
        
        url = 'rbac/roles/sysadmin'
        input = testsxml.role_put_xml_input   # reusing put data is fine here
        output = testsxml.role_put_xml_output
        content = self.req(url, method='PUT', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='PUT', data=input, expect=200, is_admin=True)
        found_items = models.RbacRole.objects.get(pk='rocketsurgeon')
        self.failUnlessRaises(models.RbacRole.DoesNotExist,
            lambda: models.RbacRole.objects.get(pk='sysadmin'))
        self.assertEqual(found_items.pk, 'rocketsurgeon')
        self.assertXMLEquals(content, output)

class RbacPermissionViews(RbacTestCase):
    
    def setUp(self):
        RbacTestCase.setUp(self)
        self.seed_data = [ 'datacenter', 'lab', 'tradingfloor' ]
        for item in self.seed_data:
            models.RbacContext(item).save()
        self.seed_data = [ 'sysadmin', 'developer', 'intern' ]
        for item in self.seed_data:
            models.RbacRole(item).save()
        models.RbacPermission(
            rbac_context  = models.RbacContext.objects.get(pk='datacenter'),
            rbac_role     = models.RbacRole.objects.get(pk='sysadmin'),
            action        = 'write'
        ).save()
        models.RbacPermission(
            rbac_context   = models.RbacContext.objects.get(pk='datacenter'),
            rbac_role      = models.RbacRole.objects.get(pk='developer'),
            action         = 'read'
        ).save()
        models.RbacPermission(
            rbac_context   = models.RbacContext.objects.get(pk='lab'),
            rbac_role      = models.RbacRole.objects.get(pk='developer'),
            action    = 'write'
        ).save()

    def testCanListPermissions(self):
        url = 'rbac/permissions'
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)

        obj = xobj.parse(content)
        found_items = self._xobj_list_hack(obj.rbac_permissions.rbac_permission)
        self.assertEqual(len(found_items), 3, 'right number of items')
        self.assertXMLEquals(content, testsxml.permission_list_xml)

    def testCanGetSinglePermission(self):
        url = 'rbac/permissions/1'
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        self.assertXMLEquals(content, testsxml.permission_get_xml)

    def testCanAddPermissions(self):
        url = 'rbac/permissions'
        input = testsxml.permission_post_xml_input
        output = testsxml.permission_post_xml_output
        content = self.req(url, method='POST', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='POST', data=input, expect=200, is_admin=True)
        self.assertXMLEquals(content, output)
        perm = models.RbacPermission.objects.get(pk=4)
        self.assertEqual(perm.rbac_role.pk, 'intern')
        self.assertEqual(perm.rbac_context.pk, 'tradingfloor')
        self.assertEqual(perm.action, 'write')

    def testCanDeletePermissions(self):
       
        all = models.RbacPermission.objects.all()
        url = 'rbac/permissions/1'
        self.req(url, method='DELETE', expect=401, is_authenticated=True)
        self.req(url, method='DELETE', expect=204, is_admin=True)
        all = models.RbacPermission.objects.all()
        self.assertEqual(len(all), 2, 'deleted an object')


    def testCanUpdatePermissions(self):
        
        url = 'rbac/permissions/1'
        input = testsxml.permission_put_xml_input
        output = testsxml.permission_put_xml_output
        content = self.req(url, method='PUT', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='PUT', data=input, expect=200, is_admin=True)
        self.assertXMLEquals(content, output)
        perm = models.RbacPermission.objects.get(pk=1)
        self.assertEqual(perm.rbac_role.pk, 'intern')
        self.assertEqual(perm.rbac_context.pk, 'tradingfloor')
        self.assertEqual(perm.action, 'write')

class RbacContextViews(RbacTestCase):

    def setUp(self):

        RbacTestCase.setUp(self)
        self.seed_data = [ 'datacenter', 'lab', 'tradingfloor' ]
        for item in self.seed_data:
            models.RbacContext(item).save()

    def testCanListContexts(self):

        url = 'rbac/contexts'
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)

        obj = xobj.parse(content)
        found_items = self._xobj_list_hack(obj.rbac_contexts.rbac_context)
        found_items = [ item.context_id for item in found_items ]
        for expected in self.seed_data:
            self.assertTrue(expected in found_items, 'found item')
        self.assertEqual(len(found_items), len(self.seed_data), 'right number of items')
        self.assertXMLEquals(content, testsxml.context_list_xml)

    def testCanGetSingleContext(self):

        url = 'rbac/contexts/datacenter'
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        obj = xobj.parse(content)
        self.assertEqual(obj.rbac_context.context_id, 'datacenter')
        self.assertXMLEquals(content, testsxml.context_get_xml)

    def testCanAddContext(self):

        url = 'rbac/contexts'
        input = testsxml.context_put_xml_input
        output = testsxml.context_put_xml_output
        content = self.req(url, method='POST', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='POST', data=input, expect=200, is_admin=True)
        found_items = models.RbacContext.objects.get(pk='datacenter2')
        self.assertEqual(found_items.pk, 'datacenter2')
        self.assertXMLEquals(content, output)

    def testCanDeleteContext(self):

        url = 'rbac/contexts/lab'
        self.req(url, method='DELETE', expect=401, is_authenticated=True)
        self.req(url, method='DELETE', expect=204, is_admin=True)
        self.failUnlessRaises(models.RbacContext.DoesNotExist,
            lambda: models.RbacContext.objects.get(pk='lab'))

    def testCanUpdateContext(self):

        url = 'rbac/contexts/datacenter'
        input = testsxml.context_put_xml_input   # reusing put data is fine here
        output = testsxml.context_put_xml_output
        content = self.req(url, method='PUT', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='PUT', data=input, expect=200, is_admin=True)
        found_items = models.RbacContext.objects.get(pk='datacenter2')
        self.failUnlessRaises(models.RbacContext.DoesNotExist,
            lambda: models.RbacContext.objects.get(pk='datacenter'))
        self.assertEqual(found_items.pk, 'datacenter2')
        self.assertXMLEquals(content, output)

class RbacUserRoleViewTests(RbacTestCase):

    def setUp(self):

        RbacTestCase.setUp(self)
        #self.seed_data = [ 'datacenter', 'lab', 'tradingfloor' ]
        #for item in self.seed_data:
        #    models.RbacContext(item).save()

        self.seed_data = [ 'sysadmin', 'developer', 'intern' ]
        for item in self.seed_data:
            models.RbacRole(item).save()
        self.sysadmin   = models.RbacRole.objects.get(role_id='sysadmin')
        self.developer  = models.RbacRole.objects.get(role_id='developer')
        self.intern     = models.RbacRole.objects.get(role_id='intern')
        # this is a little off as admins are NOT subject to rbac, but
        # we're not testing the auth chain here, just the models and services
        # so it doesn't really matter what users we use in the tests.
        self.admin_user = usersmodels.User.objects.get(user_name='admin')
        self.test_user  = usersmodels.User.objects.get(user_name='testuser')

        # admin user has two roles
        models.RbacUserRole(
            role=self.sysadmin, user=self.admin_user,
        ).save()
        models.RbacUserRole(
            role=self.developer, user=self.admin_user,
        ).save()
        # test user is an intern, just one role
        models.RbacUserRole(
            role=self.intern, user=self.test_user
        ).save()

      
    def testCanListUserRoles(self):
        user_id = self.admin_user.pk
        url = "rbac/users/%s/roles/" % user_id
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        obj = xobj.parse(content)
        found_items = self._xobj_list_hack(obj.rbac_roles.rbac_role)
        self.assertEqual(len(found_items), 2, 'right number of items')
        self.assertXMLEquals(content, testsxml.user_role_list_xml)

    def testCanGetSingleUserRole(self):
        # this is admittedly a rather useless function, which only 
        # confirms/denies where a user is in a role.  More likely 
        # we'd ask if they had permission to do something, and more 
        # as an internals thing than a REST function.  Still, here, 
        # for completeness.

        user_id = self.admin_user.pk
        url = "rbac/users/%s/roles/developer" % user_id
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        self.assertXMLEquals(content, testsxml.user_role_get_xml)
        # now verify if the role isn't assigned to the user, we can't fetch it
        url = "rbac/users/%s/roles/intern" % user_id
        content = self.req(url, method='GET', expect=404, is_admin=True)
          
    def testCanAddUserRoles(self):
        user_id = self.admin_user.pk
        url = "rbac/users/%s/roles/" % user_id
        #url = 'rbac/permissions'
        #input = testsxml.permission_post_xml_input
        #output = testsxml.permission_post_xml_output
        #content = self.req(url, method='POST', data=input, expect=401, is_authenticated=True)
        #content = self.req(url, method='POST', data=input, expect=200, is_admin=True)
        #self.assertXMLEquals(content, output)
        #perm = models.RbacPermission.objects.get(pk=4)
        #self.assertEqual(perm.rbac_role.pk, 'intern')
        #self.assertEqual(perm.rbac_context.pk, 'tradingfloor')
        #self.assertEqual(perm.action, 'write')
        # TODO: should also test that we can't double-assign a role to a user
        pass

    def testCanDeleteUserRoles(self):
        user_id = self.admin_user.pk
        url = "rbac/users/%s/roles/developer" % user_id
        #all = models.RbacPermission.objects.all()
        #url = 'rbac/permissions/1'
        #self.req(url, method='DELETE', expect=401, is_authenticated=True)
        #self.req(url, method='DELETE', expect=204, is_admin=True)
        #all = models.RbacPermission.objects.all()
        #self.assertEqual(len(all), 2, 'deleted an object')
        pass

    # (UPDATE DOES NOT MAKE SENSE, AND IS NOT SUPPORTED)

class RbacSystemViewTests(RbacTestCase):

    def testCanAssignSystemToContext(self):
        # TODO 
        pass

    def testCanRemoveSystemContext(self):
        # TODO 
        pass

class AccessControlSystemTests(RbacTestCase):
    # inventory tests will also help cover this
    # may want to add AccessControl tests there instead (probably do)

    def testAdminsCanAccessSystemWithContext(self):
       # TODO 
       pass

    def testAdminsCanAccessSystemWithoutContext(self):
       # TODO 
       pass

    def testUserCanAccessSystemWithContext(self):
       # TODO 
       pass

    def testUserCannotAccessSystemWithWrongContext(self):
       # TODO 
       pass

    def testUserCanAccessSystemWithoutContext(self):
       # TODO 
       pass

class AccessControlImageTests(RbacTestCase):
    # TODO 
    pass

class AccessControlPlatformTests(RbacTestCase):
    # TODO 
    pass
