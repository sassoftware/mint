from mint.django_rest.rbuilder.inventory.tests import XMLTestCase
from mint.django_rest.rbuilder.inventory import zones as zmodels
from mint.django_rest.rbuilder.targets import models
from mint.django_rest.rbuilder.targets import testsxml
from xobj import xobj
# from testutils import mock

class TargetsTestCase(XMLTestCase):
    def setUp(self):
        XMLTestCase.setUp(self)
        self._initTestFixtures()
    
    def _initTestFixtures(self):
        sampleTargetTypes = [ models.TargetType.objects.get(name=x)
            for x in ['vmware', 'ec2', 'xenent', 'openstack'] ]

        lz = zmodels.Zone.objects.get(name=zmodels.Zone.LOCAL_ZONE)

        nameTempl = 'Target Name %s'
        descrTempl = 'Target Description %s'
        sampleTargets = []
        for targetType in sampleTargetTypes:
            sampleTargets.append(
                models.Target.objects.create(name=nameTempl % targetType.name,
                    description=descrTempl % targetType.name,
                    target_type=targetType,
                    zone=lz))
        self.targetTypes = sampleTargetTypes
        self.targets = sampleTargets

    def testGetTargets(self):
        targets = models.Target.objects.order_by('target_id')
        response = self._get('targets/', username='testuser', password='password')
        targets_gotten = xobj.parse(response.content)
        self.assertEquals(response.status_code, 200)
        self.failUnlessEqual([ x.name for x in targets_gotten.targets.target ],
            [ x.name for x in targets ])

    def testGetTarget(self):
        target = models.Target.objects.get(name = 'Target Name openstack')
        response = self._get('targets/%s' % target.pk,
            username='testuser', password='password')
        target_gotten = xobj.parse(response.content).target
        self.assertEquals(response.status_code, 200)
        self.assertEquals(target.name, target_gotten.name)
        self.assertXMLEquals(response.content, testsxml.target_GET)

    def testCreateTarget(self):
        response = self._post('targets/', username='admin', password='password',
            data=testsxml.target_POST)
        # Target creation is done via actions
        self.assertEquals(response.status_code, 405)

    def testUpdateTarget(self):
        response = self._put('targets/1', username='admin', password='password',
            data=testsxml.target_PUT)
        # Target updates are done via actions
        self.assertEquals(response.status_code, 405)

    def testDeleteTarget(self):
        response = self._delete('targets/1', username='testuser', password='password')
        self.assertEquals(response.status_code, 401)
        response = self._delete('targets/1', username='admin', password='password')
        self.assertEquals(response.status_code, 204)

    def testGetTargetTypes(self):
        targetTypesExpected = models.TargetType.objects.order_by('target_type_id')
        response = self._get('target_types/', username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        targetTypes = xobj.parse(response.content)
        self.failUnlessEqual(
            [ x.name for x in targetTypes.target_types.target_type ],
            [ x.name for x in targetTypesExpected ])

    def testGetTargetType(self):
        targetType = models.TargetType.objects.get(name='openstack')
        response = self._get('target_types/%s' % targetType.pk,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.target_type_GET)

    def testGetTargetTypeByTargetId(self):
        target = models.Target.objects.get(pk=1)
        response = self._get('targets/1/target_types',
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.target_type_by_target_id_GET)
    
    # Finish
    def testGetTargetCredentialsForTargetByUserId(self):
        pass
