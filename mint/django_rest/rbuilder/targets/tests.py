#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

import collections

from mint.django_rest.test_utils import XMLTestCase, RepeaterMixIn
from mint.django_rest.rbuilder.inventory import zones as zmodels
from mint.django_rest.rbuilder.users import models as umodels
from mint.django_rest.rbuilder.jobs import models as jmodels
from mint.django_rest.rbuilder.targets import models
from mint.django_rest.rbuilder.targets import testsxml
from xobj import xobj

class BaseTargetsTest(XMLTestCase):
    def setUp(self):
        XMLTestCase.setUp(self)
        self._initTestFixtures()
        self._mock()

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

        for i in range(2):
            for j in range(1,3):
                models.JobTarget.objects.create(
                    job=self.jobs[i], target=self.targets[j-1])       
        self.jobTargets = models.JobTarget.objects.all()

        for i in range(3):
            targetCredentials = models.TargetCredentials.objects.create(credentials='abc%s' % i)
            models.TargetUserCredentials.objects.create(
                target=sampleTargets[i],
                user=umodels.User.objects.get(user_name='testuser'),
                target_credentials=targetCredentials)
                
        self.target_credentials = models.TargetCredentials.objects.all()
        self.target_user_credentials = models.TargetUserCredentials.objects.all()

    def _mock(self):
        pass

class TargetsTestCase(BaseTargetsTest):
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
        self.failUnlessEqual(obj.descriptor.metadata.rootElement, 'descriptor_data')
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

    def testGetTargetDescriptorConfigureCredentials(self):
        response = self._get('targets/1024/descriptor_configure_credentials',
            username='testuser', password='password')
        self.assertEquals(response.status_code, 404)
        response = self._get('targets/1/descriptor_configure_credentials',
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.descriptor.metadata.rootElement, 'descriptor_data')
        self.failUnlessEqual(
            [ x.name for x in obj.descriptor.dataFields.field ],
            [
                'username',
                'password',
            ])

    def testGetJobsByTargetType(self):
        url = 'target_types/%s/jobs'
        response = self._get(url % 1, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.jobs_by_target_type_GET)

    def testGetAllTargetTypeJobs(self):
        url = 'target_type_jobs'
        response = self._get(url, username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual([ x.job_uuid for x in obj.jobs.job ],
            ['rmakeuuid002', 'rmakeuuid001'])


    def testGetJobsByTarget(self):
        url = 'targets/%s/jobs'
        response = self._get(url % 1, username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.jobs_by_target_GET)

class JobCreationTest(BaseTargetsTest, RepeaterMixIn):

    def _mock(self):
        RepeaterMixIn.setUpRepeaterClient(self)
        from mint.django_rest.rbuilder.inventory.manager import repeatermgr
        self.mock(repeatermgr.RepeaterManager, 'repeaterClient',
            self.mgr.repeaterMgr.repeaterClient)

    def testTargetCreationJob(self):
        jobXml = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/19"/>
  <descriptor id="http://testserver/api/v1/target_types/6/descriptor_create_target"/>
  <descriptor_data>
    <alias>newbie</alias>
    <description>Brand new cloud</description>
    <name>newbie.eng.rpath.com</name>
    <zone>Local rBuilder</zone>
  </descriptor_data>
</job>
"""
        response = self._post('target_type_jobs', jobXml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id, "http://testserver/api/v1/target_types/6/descriptor_create_target")

        dbjob = jmodels.Job.objects.get(job_uuid=job.job_uuid)
        # Make sure the job is related to the target type
        self.failUnlessEqual(
            [ x.target_type.name for x in dbjob.jobtargettype_set.all() ],
            [ 'xenent' ],
        )

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            ['targets.TargetConfiguration', 'targets.configure', 'targets.checkCreate'])
        realCall = calls[-1]
        self.failUnlessEqual(realCall.args, ())
        self.failUnlessEqual(realCall.kwargs, {})
        self.mgr.repeaterMgr.repeaterClient.reset()

        jobXml = """
<job>
  <job_state>Failed</job_state>
  <status_code>401</status_code>
  <status_text>Invalid target credentials</status_text>
</job>
"""
        # Grab token
        jobToken = dbjob.job_token
        jobUrl = "jobs/%s" % dbjob.job_uuid
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job

        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Done</status_text>
  <results>
    <target/>
  </results>
</job>
"""

        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.results.id, "http://testserver/api/v1/targets/5")

    def testTargetCredentialsConfiguration(self):
        jobType = jmodels.EventType.objects.get(name="configure target credentials")
        target = models.Target.objects.get(name='Target Name vmware')
        jobXml = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/targets/%(targetId)s/descriptor_configure_credentials"/>
  <descriptor_data>
    <username>bubba</username>
    <password>shrimp</password>
  </descriptor_data>
</job>
"""
        params = dict(targetId=target.target_id, jobTypeId=jobType.job_type_id)
        response = self._post('targets/%s/jobs' % target.target_id,
            jobXml % params,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/targets/%s/descriptor_configure_credentials" %  target.target_id)

        dbjob = jmodels.Job.objects.get(job_uuid=job.job_uuid)
        # Make sure the job is related to the target type
        self.failUnlessEqual(
            [ x.target.name for x in dbjob.jobtarget_set.all() ],
            [ target.name ],
        )

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            ['targets.TargetConfiguration', 'targets.TargetUserCredentials',
                'targets.configure', 'targets.checkCredentials'])
        realCall = calls[-1]
        self.failUnlessEqual(realCall.args, ())
        self.failUnlessEqual(realCall.kwargs, {})
        self.mgr.repeaterMgr.repeaterClient.reset()

        jobXml = """
<job>
  <job_state>Failed</job_state>
  <status_code>401</status_code>
  <status_text>Invalid target credentials</status_text>
</job>
"""
        # Grab token
        jobToken = dbjob.job_token
        jobUrl = "jobs/%s" % dbjob.job_uuid
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job

        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Done</status_text>
  <results>
    <target/>
  </results>
</job>
"""

        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.results.id, "http://testserver/api/v1/targets/1")

    def testSetTargetUserCredentials(self):
        target = models.Target.objects.get(pk=1)
        creds0 = dict(username="bubba", password="shrimp")
        creds1 = dict(username="forrest", password="jennay")
        tmgr = self.mgr.targetsManager
        fakeAuth = collections.namedtuple("FakeAuth", "userId")
        tmgr.mgr._auth = fakeAuth(1)
        tucreds = tmgr.setTargetUserCredentials(target, creds0)
        creds = sorted(models.TargetUserCredentials.objects.filter(
            user__user_id=1, target=target).values_list('id', flat=True))
        self.failUnlessEqual(creds, [tucreds.id])
        # Do it again, the credentials should be the same
        tucreds2 = tmgr.setTargetUserCredentials(target, creds0)
        self.failUnlessEqual(tucreds.id, tucreds2.id)

        tcredid = tucreds.target_credentials_id

        # New creds
        tucreds3 = tmgr.setTargetUserCredentials(target, creds1)
        self.failIf(tucreds.id == tucreds3.id)

        # Old creds should be gone
        self.failUnlessEqual([ x for x in
                models.TargetCredentials.objects.filter(
                    target_credentials_id=tcredid).values_list(
                        'target_credentials_id', flat=True)],
            [])
