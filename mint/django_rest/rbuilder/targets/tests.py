from mint.django_rest.rbuilder.inventory.tests import XMLTestCase
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
            models.TargetType.create(type='VMWare', description='VMWare TargetType'), 
            models.TargetType.create(type='EC2', description='EC2 TargetType'),
            models.TargetType.create(type='Heffer', description='Moo goes the cow')
            ]

        name = 'Target Name %s'
        sample_targets = []
        for idx, target_type in enumerate(sample_target_types):
            sample_targets[idx] = \
                models.Target.create(name=name % idx, target_type=target_type)
        self.target_types = sample_target_types
        self.targets = sample_targets
        
    def testGetTargets(self):
        self._initTestFixtures()
        targets = models.Target.objects.all()
        response = self._get('targets/', username='admin', password='password')
        targets_gotten = xobj.parse(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(targets), len(targets_gotten))
        
    def testGetTarget(self):
        self._initTestFixtures()
        target = models.Target.objects.get(pk=1)
        response = self._get('targets/1', username='admin', password='password')
        target_gotten = xobj.parse(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(target.target_name, target_gotten.target_name)
        self.assertEquals(target.target_type, target_gotten.target_type)
        
    def testCreateTarget(self):
        pass
        
    def testUpdateTarget(self):
        pass
        
    def testDeleteTarget(self):
        pass
        
    def testGetTargetTypes(self):
        pass
        
    def testGetTargetType(self):
        pass
        
    def testGetTargetCredentialsForTargetByUserId(self):
        pass
    