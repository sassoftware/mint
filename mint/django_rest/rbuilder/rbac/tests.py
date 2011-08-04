#import base64
#import cPickle
#import datetime
#import os
#import random
#from dateutil import tz
#from xobj import xobj
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
#from mint.django_rest.rbuilder.users import models as usersmodels
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
        pass

    def testModelsForRbacPermissions(self):
        pass

    def testModelsForUserRoleAssignment(self):
        pass

    def testModelsForSystemContextAssignment(self):
        pass

class RbacRoleViews(XMLTestCase):
    def testCanListRoles(self):
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
    def testCanAddPermissions(self):
        pass
    def testCanDeletePermissions(self):
        pass
    def testCanUpdatePermissions(self):
        pass

class RbacContextViews(XMLTestCase):
    def testCanListContexts(self):
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
