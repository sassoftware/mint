from mint.django_rest.rbuilder.inventory.tests import XMLTestCase

from mint.django_rest.rbuilder.projects import manager # pyflakes=ignore
from mint.django_rest.rbuilder.projects import models # pyflakes=ignore
from mint.django_rest.rbuilder.projects import testsxml # pyflakes=ignore
from mint.django_rest.rbuilder.repos import manager as reposmanager
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager import rbuildermanager
from xobj import xobj
from mint.django_rest.rbuilder.rbac.tests import RbacEngine
from testutils import mock


class TargetsTestCase(RbacEngine):
    def setUp(self):
        RbacEngine.setUp(self)
        
    def testGetTargets(self):
        pass
        
    def testGetTarget(self):
        pass