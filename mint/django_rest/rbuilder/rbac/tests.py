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

    def setUp(self):
        # just a stub for later...
        XMLTestCase.setUp(self)
        a = models.RbacContext()
        b = models.RbacRole()
        c = models.RbacPermission()
        pass

    def testFoo(self):
        pass
