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
           context    = context1,
           role       = role1,
           # TODO: add choice restrictions
           action     = action_name,
        )
        permission.save()
        permissions2 = models.RbacPermission.objects.filter(
           context = context1
        )
        self.assertEquals(len(permissions2), 1, 'correct length')
        found = permissions2[0]
        self.assertEquals(found.action, action_name, 'saved ok')
        self.assertEquals(found.context.pk, 'datacenter', 'saved ok')
        self.assertEquals(found.role.pk, 'sysadmin', 'saved ok')

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
 
    def testCanGetSingleRole(self):

        url = 'rbac/roles/developer'
        content = self.req(url, method='GET', expect=401, is_authenticated=True)
        content = self.req(url, method='GET', expect=200, is_admin=True)
        obj = xobj.parse(content)
        self.assertEqual(obj.rbac_role.role_id, 'developer')

    def testCanAddRoles(self):
        
        url = 'rbac/roles'
        input = testsxml.role_put_xml_input   
        output = testsxml.role_put_xml_output
        content = self.req(url, method='POST', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='POST', data=input, expect=200, is_admin=True)
        found_items = models.RbacRole.objects.get(pk='rocket surgeon')
        self.assertEqual(found_items.pk, 'rocket surgeon')
        self.assertXMLEquals(content, output)

    def testCanDeleteRoles(self):

        url = 'rbac/roles/sysadmin'
        content = self.req(url, method='DELETE', expect=401, is_authenticated=True)
        content = self.req(url, method='DELETE', expect=204, is_admin=True)
        self.failUnlessRaises(models.RbacRole.DoesNotExist,
            lambda: models.RbacRole.objects.get(pk='sysadmin'))

    def testCanUpdateRoles(self):
        
        url = 'rbac/roles/sysadmin'
        input = testsxml.role_put_xml_input   # reusing put data is fine here
        output = testsxml.role_put_xml_output
        content = self.req(url, method='PUT', data=input, expect=401, is_authenticated=True)
        content = self.req(url, method='PUT', data=input, expect=200, is_admin=True)
        found_items = models.RbacRole.objects.get(pk='rocket surgeon')
        self.failUnlessRaises(models.RbacRole.DoesNotExist,
            lambda: models.RbacRole.objects.get(pk='sysadmin'))
        self.assertEqual(found_items.pk, 'rocket surgeon')
        self.assertXMLEquals(content, output)

class RbacPermissionViews(RbacTestCase):
    def testCanListPermissions(self):
        pass
    def testCanGetSinglePermission(self):
        pass
    def testCanAddPermissions(self):
        pass
    def testCanDeletePermissions(self):
        pass
    def testCanUpdatePermissions(self):
        pass

class RbacContextViews(RbacTestCase):
    def testCanListContexts(self):
        pass
    def testCanGetSingleContext(self):
        pass
    def testCanAddContexts(self):
        pass
    def testCanDeleteContexts(self):
        pass
    def testCanUpdatePermissions(self):
        pass

class RbacUserViewTests(RbacTestCase):
    def testCanAssignUserToRole(self):
        pass
    def testCanRemoveUserRole(self):
        pass
   
class RbacSystemViewTests(RbacTestCase):
    def testCanAssignSystemToContext(self):
        pass
    def testCanRemoveSystemContext(self):
        pass

class AccessControlSystemTests(RbacTestCase):
    # inventory tests will also help cover this
    # may want to add AccessControl tests there instead (probably do)
    def testAdminsCanAccessSystemWithContext(self):
       pass
    def testAdminsCanAccessSystemWithoutContext(self):
       pass
    def testUserCanAccessSystemWithContext(self):
       pass
    def testUserCannotAccessSystemWithWrongContext(self):
       pass
    def testUserCanAccessSystemWithoutContext(self):
       pass

class AccessControlImageTests(RbacTestCase):
    pass

class AccessControlPlatformTests(RbacTestCase):
    pass
