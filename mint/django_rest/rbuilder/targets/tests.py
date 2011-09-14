from mint.django_rest.rbuilder.inventory.tests import XMLTestCase
from mint.django_rest.rbuilder.inventory import zones as zmodels
from mint.django_rest.rbuilder.users import models as umodels
from mint.django_rest.rbuilder.jobs import models as jmodels
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

        eventUuid1 = 'eventuuid001'
        jobUuid1 = 'rmakeuuid001'
        eventUuid2 = 'eventuuid002'
        jobUuid2 = 'rmakeuuid002'
        eventUuid3 = 'eventuuid003'
        jobUuid3 = 'rmakeuuid003'
        system = self._saveSystem()
        
        jobs = []
        jobs.append(self._newSystemJob(system, eventUuid1, jobUuid1,
            jmodels.EventType.SYSTEM_REGISTRATION))
        jobs.append(self._newSystemJob(system, eventUuid2, jobUuid2,
            jmodels.EventType.SYSTEM_POLL))
        jobs.append(self._newSystemJob(system, eventUuid3, jobUuid3,
            jmodels.EventType.SYSTEM_POLL_IMMEDIATE))

        self.system = system
        self.jobs = jobs

        for i in range(2):
            for j in range(1,3):
                models.JobTargetType.objects.create(
                    job=self.jobs[i], target_type=self.targetTypes[j-1])       
        self.jobTargetTypes = models.JobTargetType.objects.all()

        for i in range(3):
            targetCredentials = models.TargetCredentials.objects.create(credentials='abc%s' % i)
            models.TargetUserCredentials.objects.create(
                target_id=sampleTargets[i],
                user_id=umodels.User.objects.get(user_name='testuser'),
                target_credentials_id=targetCredentials)
                
        self.target_credentials = models.TargetCredentials.objects.all()
        self.target_user_credentials = models.TargetUserCredentials.objects.all()

    def testGetTargets(self):
        targets = models.Target.objects.order_by('target_id')
        response = self._get('targets/', username='testuser', password='password')
        targets_gotten = xobj.parse(response.content)
        self.assertEquals(response.status_code, 200)
        self.failUnlessEqual([ x.name for x in targets_gotten.targets.target ],
            [ x.name for x in targets ])
        self.failUnlessEqual([ x.id for x in targets_gotten.targets.target ],
            [
                'http://testserver/api/v1/targets/1',
                'http://testserver/api/v1/targets/2',
                'http://testserver/api/v1/targets/3',
                'http://testserver/api/v1/targets/4',
            ])
        actions = targets_gotten.targets.actions.action
        self.failUnlessEqual(
            [ x.name for x in actions ],
            [
                'Create target of type ec2',
                'Create target of type eucalyptus',
                'Create target of type openstack',
                'Create target of type vcloud',
                'Create target of type vmware',
                'Create target of type xenent',
            ])
        self.failUnlessEqual(
            [ x.descriptor.id for x in actions ],
            [
                'http://testserver/api/v1/target_types/1/descriptor_create_target',
                'http://testserver/api/v1/target_types/2/descriptor_create_target',
                'http://testserver/api/v1/target_types/3/descriptor_create_target',
                'http://testserver/api/v1/target_types/4/descriptor_create_target',
                'http://testserver/api/v1/target_types/5/descriptor_create_target',
                'http://testserver/api/v1/target_types/6/descriptor_create_target',
            ])
        self.failUnlessEqual(
            [ x.job_type.id for x in actions ],
            [
                'http://testserver/api/v1/inventory/event_types/19',
                'http://testserver/api/v1/inventory/event_types/19',
                'http://testserver/api/v1/inventory/event_types/19',
                'http://testserver/api/v1/inventory/event_types/19',
                'http://testserver/api/v1/inventory/event_types/19',
                'http://testserver/api/v1/inventory/event_types/19',
            ])
        self.failUnlessEqual(targets_gotten.targets.jobs.id,
            'http://testserver/api/v1/target_jobs')

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
        response = self._get('targets/1/target_types',
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.target_type_by_target_id_GET)

    def testGetTargetTypeDescriptorCreateTarget(self):
        response = self._get('target_types/1024/descriptor_create_target',
            username='testuser', password='password')
        self.assertEquals(response.status_code, 404)
        response = self._get('target_types/1/descriptor_create_target',
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(
            [ x.name for x in obj.descriptor.dataFields.field ],
            [
                'name',
                'cloudAlias',
                'fullDescription',
                'accountId',
                'publicAccessKeyId',
                'secretAccessKey',
                'certificateData',
                'certificateKeyData',
                's3Bucket',
                'zone',
        ])

    def testGetJobsByTargetType(self):
        url = 'target_type_jobs/%s'
        response = self._get(url % 1, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.jobs_by_target_type_GET)