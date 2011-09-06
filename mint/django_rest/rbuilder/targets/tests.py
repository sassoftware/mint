from mint.django_rest.rbuilder.inventory.tests import XMLTestCase
from mint.django_rest.rbuilder.targets import models
from mint.django_rest.rbuilder.targets import testsxml
from xobj import xobj
from testutils import mock

class TargetsTestCase(XMLTestCase):
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
    
    def _initTestFixtures(self):
        sample_target_types = \
            [
            models.TargetType.objects.create(type='VMWare', description='VMWare TargetType'), 
            models.TargetType.objects.create(type='EC2', description='EC2 TargetType'),
            models.TargetType.objects.create(type='Heffer', description='Moo goes the cow')
            ]

        name = 'Target Name %s'
        sample_targets = []
        for idx, target_type in enumerate(sample_target_types):
            sample_targets.append(
                models.Target.objects.create(target_name=name % idx, target_type=target_type))
        self.target_types = sample_target_types
        self.targets = sample_targets
        
    def testGetTargets(self):
        self._initTestFixtures()
        targets = models.Target.objects.all()
        response = self._get('targets/', username='admin', password='password')
        targets_gotten = xobj.parse(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(targets), len(targets_gotten.targets.target))
        
    def testGetTarget(self):
        self._initTestFixtures()
        target = models.Target.objects.get(pk=1)
        response = self._get('targets/1', username='admin', password='password')
        target_gotten = xobj.parse(response.content).target
        self.assertEquals(response.status_code, 200)
        self.assertEquals(target.target_name, target_gotten.target_name)
        self.assertXMLEquals(response.content, testsxml.target_GET)
        
    def testCreateTarget(self):
        # NOTE:
        # models.Target has target_id as IntegerField not an AutoField
        # so integer id must be explictly passed into the xml
        response = self._post('targets/', username='admin', password='password',
            data=testsxml.target_POST)
        self.assertEquals(response.status_code, 200)
        target_posted = xobj.parse(response.content)
        target = models.Target.objects.get(pk=4)
        self.assertEquals(str(target.target_id), target_posted.target.target_id)
        
    def testUpdateTarget(self):
        self._initTestFixtures()
        response = self._put('targets/1', username='admin', password='password',
            data=testsxml.target_PUT)
        target_putted = xobj.parse(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(target_putted.target.target_name, "Target 1 renamed")
        
    def testDeleteTarget(self):
        self._initTestFixtures()
        response = self._delete('targets/1', username='admin', password='password')
        self.assertEquals(response.status_code, 204)
        
    def testGetTargetTypes(self):
        self._initTestFixtures()
        response = self._get('target_types/', username='admin', password='password')
        self.assertXMLEquals(response.content, testsxml.target_types_GET)
        
    def testGetTargetType(self):
        self._initTestFixtures()
        response = self._get('target_types/1', username='admin', password='password')
        self.assert
        
    def testGetTargetCredentialsForTargetByUserId(self):
        pass
    