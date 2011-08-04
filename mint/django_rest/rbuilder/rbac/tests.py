#import base64
#import cPickle
#import datetime
#import os
#import random
#from dateutil import tz
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

class RbacBasicTestCase(XMLTestCase):

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

def _xobj_list_hack(item):
    # xobj hack: obj doesn't listify 1 element lists
    # don't break tests if there is only 1 action
    if type(item) != type(item):
       return [item]
    else:
       return item

class RbacRoleViews(XMLTestCase):

    def setUp(self):
        XMLTestCase.setUp(self)
        models.RbacRole('sysadmin').save()
        models.RbacRole('developer').save()
        models.RbacRole('intern').save()

    def testCanListRoles(self):

        url = 'rbac/roles'
        response = self._get(url, username="testuser", password="password")
        self.assertEquals(response.status_code, 401, 'need to be an admin to list roles')

        response = self._get(url, username="admin", password="password")
        self.assertEquals(response.status_code, 200, 'able to access as admin')

        obj = xobj.parse(response.content)
        import epdb; epdb.st()
        items = _xobj_list_hack(obj.rbac_roles.role)

        for x in items:
            print items

        self.assertEquals(len(items), 3, 'right number of items')
 
    def testCanGetSingleRole(self):
        pass
    def testCanAddRoles(self):
        pass
    def testCanDeleteRoles(self):
        pass
    def testCanUpdateRoles(self):
        pass

class RbacPermissionViews(XMLTestCase):
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

class RbacContextViews(XMLTestCase):
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

class RbacUserViewTests(XMLTestCase):
    def testCanAssignUserToRole(self):
        pass
    def testCanRemoveUserRole(self):
        pass
   
class RbacSystemViewTests(XMLTestCase):
    def testCanAssignSystemToContext(self):
        pass
    def testCanRemoveSystemContext(self):
        pass

class AccessControlSystemTests(XMLTestCase):
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

class AccessControlImageTests(XMLTestCase):
    pass

class AccessControlPlatformTests(XMLTestCase):
    pass
