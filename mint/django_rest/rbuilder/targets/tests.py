#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

import collections
import re

from mint import buildtypes
from mint.django_rest.test_utils import XMLTestCase, RepeaterMixIn
from mint.django_rest.rbuilder.inventory import zones as zmodels
from mint.django_rest.rbuilder.inventory import models as invmodels
from mint.django_rest.rbuilder.images import models as imgmodels
from mint.django_rest.rbuilder.users import models as umodels
from mint.django_rest.rbuilder.jobs import models as jmodels
from mint.django_rest.rbuilder.targets import models
from mint.django_rest.rbuilder.targets import testsxml
from xobj import xobj
from mint.django_rest.rbuilder.rbac import models as rbacmodels
from mint.django_rest.rbuilder.querysets import models as querymodels
from mint.django_rest.rbuilder.users import models as usermodels
from mint.django_rest.rbuilder.rbac.tests import RbacEngine
from mint.django_rest import timeutils


# TODO: would be nice to make RbacSetup more of a mixin
class BaseTargetsTest(RbacEngine):

    def setUp(self):
        RbacEngine.setUp(self)
        self._initTestFixtures()
        self._mock()
        self._setupRbac()

    def _initTestFixtures(self):
        sampleTargetTypes = [ models.TargetType.objects.get(name=x)
            for x in ['vmware', 'ec2', 'xen-enterprise', 'openstack'] ]

        lz = zmodels.Zone.objects.get(name=zmodels.Zone.LOCAL_ZONE)

        nameTempl = 'Target Name %s'
        descrTempl = 'Target Description %s'
        sampleTargets = []
        for targetType in sampleTargetTypes:
            sampleTargets.append(
                models.Target.objects.create(name=nameTempl % targetType.name,
                    description=descrTempl % targetType.name,
                    target_type=targetType, state=0,
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
        
        user = self.getUser('testuser')

        jobs = []
        jobs.append(self._newSystemJob(system, eventUuid1, jobUuid1,
            jmodels.EventType.SYSTEM_REGISTRATION, createdBy=user))
        jobs.append(self._newSystemJob(system, eventUuid2, jobUuid2,
            jmodels.EventType.SYSTEM_POLL, createdBy=user))
        jobs.append(self._newSystemJob(system, eventUuid3, jobUuid3,
            jmodels.EventType.SYSTEM_POLL_IMMEDIATE, createdBy=user))

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
        tmgr = self.mgr.targetsManager
        fakeAuth = collections.namedtuple("FakeAuth", "userId")
        self.mock(tmgr.mgr, '_auth', fakeAuth(1))

    # invalidate the querysets so tags can be applied
    def _retagQuerySets(self):
        self.mgr.retagQuerySetsByType('project')
        self.mgr.retagQuerySetsByType('images')

    def _setupRbac(self):

        # RbacEngine test base class has already done a decent amount of setup
        # now just add the grants for the things we are working with

        role              = rbacmodels.RbacRole.objects.get(name='developer')
        self.all_targets  = querymodels.QuerySet.objects.get(name='All Targets')
        self.all_images   = querymodels.QuerySet.objects.get(name='All Images')
        modmembers        = rbacmodels.RbacPermissionType.objects.get(name='ModMembers')
        readset           = rbacmodels.RbacPermissionType.objects.get(name='ReadSet')
        createresource    = rbacmodels.RbacPermissionType.objects.get(name='CreateResource')
        admin             = usermodels.User.objects.get(user_name='admin')

        for queryset in [ self.all_targets, self.all_images ]:
            for permission in [ modmembers, createresource, readset  ]:
                rbacmodels.RbacPermission(
                    queryset      = queryset,
                    role          = role,
                    permission    = permission,
                    created_by    = admin,
                    modified_by   = admin,
                    created_date  = timeutils.now(),
                    modified_date = timeutils.now()
                ).save()

        self._retagQuerySets()

class TargetsTestCase(BaseTargetsTest, RepeaterMixIn):
    def _mock(self):
        RepeaterMixIn.setUpRepeaterClient(self)
        BaseTargetsTest._mock(self)

    def testGetDescriptorTargetsCreation(self):
        zmodels.Zone.objects.create(name='other zone', description = "Other Zone")
        response = self._get('descriptors/targets/create',
            username='testuser', password='password')
        self.failUnlessEqual(response.status_code, 200)
        document = xobj.parse(response.content)
        self.failUnlessEqual(document.descriptor.metadata.rootElement,
            'descriptor_data')
        fields = document.descriptor.dataFields.field
        self.failUnlessEqual([ x.name for x in fields ],
            ['name', 'description', 'target_type_name', 'zone_name'])
        self.failUnlessEqual(
            [ x.key for x in fields[2].enumeratedType.describedValue ],
            ['ec2', 'eucalyptus', 'openstack', 'vcloud', 'vmware', 'xen-enterprise'])
        self.failUnlessEqual(
            [ x.key for x in fields[3].enumeratedType.describedValue ],
            ['Local rBuilder', 'other zone'])

    def testGetTargetConfigurationDescriptor(self):
        response = self._get('targets/1/target_configuration/',
            username='admin', password='password')
        configDescriptor = xobj.parse(response.content)
        ### FIXME: Finish damnit

    def testGetTargets(self):
        targets = models.Target.objects.order_by('target_id')
        response = self._get('targets/', username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        targets_gotten = xobj.parse(response.content)
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
                'Create target of type xen-enterprise',
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
        self.failUnlessEqual(targets_gotten.targets.descriptor_create.id,
            'http://testserver/api/v1/descriptors/targets/create')

    def testGetTarget_credentials_valid(self):
        # Remove credentials for one of the targets
        # openstack won't have creds anyway
        models.TargetUserCredentials.objects.get(target__name = 'Target Name xen-enterprise').delete()
        response = self._get('targets/', username='testuser', password='password')
        targetsObj = xobj.parse(response.content)
        self.failUnlessEqual([ x.name for x in targetsObj.targets.target ],
            [
                'Target Name vmware',
                'Target Name ec2',
                'Target Name xen-enterprise',
                'Target Name openstack',
            ])
        self.failUnlessEqual([ x.credentials_valid for x in targetsObj.targets.target ],
            ['true', 'true', 'false', 'false', ])

    def testGetTarget(self):
        target = models.Target.objects.get(name = 'Target Name openstack')
        response = self._get('targets/%s' % target.pk,
            username='testuser', password='password')
        target_gotten = xobj.parse(response.content).target
        self.assertEquals(response.status_code, 200)
        self.assertEquals(target.name, target_gotten.name)
        self.assertXMLEquals(response.content, testsxml.target_GET)

    def testGetTargetConfigurationDescriptor(self):
        target = models.Target.objects.get(name = 'Target Name openstack')
        response = self._get('targets/%s/descriptors/configuration' % target.pk,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.descriptor.metadata.rootElement, 'descriptor_data')
        self.failUnlessEqual(
            [ x.name for x in obj.descriptor.dataFields.field ],
            [
                'name',
                'nova_port',
                'glance_server',
                'glance_port',
                'alias',
                'description',
                'zone',
        ])

    def testCreateTarget(self):
        zmodels.Zone.objects.create(name='other zone', description = "Other Zone")
        response = self._post('targets/', username='admin', password='password',
            data=testsxml.target_POST)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        target = obj.target
        self.failUnlessEqual(target.name, "Target Name 4")
        self.failUnlessEqual(target.description, "Target Description")
        actions = [ x for x in target.actions.action ]
        self.failUnlessEqual([ x.name for x in actions ],
          [
            'Configure target',
            'Configure user credentials for target',
            'Refresh images',
            'Refresh systems',
          ])
        self.failUnlessEqual([ x.enabled for x in actions ],
          [ 'true', 'false', 'false', 'false', ])
        dbobj = models.Target.objects.get(target_id=target.target_id)
        self.failUnlessEqual(dbobj.target_type.name, 'vmware')
        self.failUnlessEqual(dbobj.zone.name, 'other zone')


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

    def testGetTargetsForTargetType(self):
        targetType = models.TargetType.objects.get(name='openstack')
        models.Target.objects.filter(target_type=targetType).delete()
        models.Target.objects.create(target_type=targetType, state=0,
            name="test openstack", description="test openstack",
            zone=self.localZone)
        response = self._get('target_types/%s/targets' % targetType.pk,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        targets = [ obj.targets.target ]
        self.failUnlessEqual([ x.name for x in targets ],
            ["test openstack"])
        actions = [ obj.targets.actions.action ]
        self.failUnlessEqual([ x.name for x in actions ], [
            'Create target of type openstack',
        ])
        self.failUnlessEqual(
            [ x.descriptor.id for x in actions ],
            [
                'http://testserver/api/v1/target_types/3/descriptor_create_target',
            ])

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
        response = self._get('targets/1024/descriptors/configure_credentials',
            username='testuser', password='password')
        self.assertEquals(response.status_code, 404)
        response = self._get('targets/1/descriptors/configure_credentials',
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

    def testGetTargetDescriptorRefreshImages(self):
        response = self._get('targets/1024/descriptors/refresh_images',
            username='testuser', password='password')
        self.assertEquals(response.status_code, 404)
        response = self._get('targets/1/descriptors/refresh_images',
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.descriptor.metadata.rootElement, 'descriptor_data')
        self.failIf(hasattr(obj.descriptor.dataFields, 'field'))

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

    def testGetAllTargetJobs(self):
        response = self._get('target_jobs/', username='admin', password='password')
        self.assertXMLEquals(response.content, testsxml.all_target_jobs_GET)
        self.assertEquals(response.status_code, 200)


class JobCreationTest(BaseTargetsTest, RepeaterMixIn):

    def _mock(self):
        RepeaterMixIn.setUpRepeaterClient(self)
        BaseTargetsTest._mock(self)
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
            [ 'xen-enterprise' ],
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
        self.failUnlessEqual(job.status_code, "200")
        self.failUnlessEqual(job.status_text, "Done")

        # Post again. We shouldn't create it again
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.status_code, "400")
        self.failUnlessEqual(job.status_text, "Duplicate Target")

    def testTargetConfiguration(self):
        # Add credentials for admin
        target = models.Target.objects.filter(target_type__target_type_id=5)[0]
        testUser = self.getUser('testuser')
        adminUser = self.getUser('admin')
        models.TargetUserCredentials.objects.create(
            target=target,
            user=adminUser,
            target_credentials=models.TargetCredentials.objects.filter(
                target_user_credentials__user=testUser,
                target_user_credentials__target=target)[0])
        jobXml = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/22"/>
  <descriptor id="http://testserver/api/v1/targets/%(targetId)s/descriptors/configuration"/>
  <descriptor_data>
    <alias>newbie</alias>
    <description>Brand new cloud</description>
    <name>newbie.eng.rpath.com</name>
    <zone>Local rBuilder</zone>
  </descriptor_data>
</job>
""" % dict(targetId=target.target_id)
        response = self._post('targets/%s/jobs' % target.target_id, jobXml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 403)

        response = self._post('targets/%s/jobs' % target.target_id, jobXml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/targets/%d/descriptors/configuration" % target.target_id)

        dbjob = jmodels.Job.objects.get(job_uuid=job.job_uuid)
        # Make sure the job is related to the target type
        self.failUnlessEqual(
            [ x.target.name for x in dbjob.target_jobs.all() ],
            [ 'Target Name vmware' ],
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
        self.failUnlessEqual(job.results.id,
            "http://testserver/api/v1/targets/%s" % target.target_id)
        self.failUnlessEqual(job.status_code, "200")
        self.failUnlessEqual(job.status_text, "Done")

        target = models.Target.objects.get(target_id=target.target_id)
        self.failUnlessEqual(target.name, 'newbie.eng.rpath.com')

    def testTargetCredentialsConfiguration(self):
        jobType = jmodels.EventType.objects.get(name=jmodels.EventType.TARGET_CONFIGURE_CREDENTIALS)
        target = models.Target.objects.get(name='Target Name vmware')
        jobXml = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/targets/%(targetId)s/descriptors/configure_credentials"/>
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
            "http://testserver/api/v1/targets/%s/descriptors/configure_credentials" %  target.target_id)

        dbjob = jmodels.Job.objects.get(job_uuid=job.job_uuid)
        # Make sure the job is related to the target type
        self.failUnlessEqual(
            [ x.target.name for x in dbjob.target_jobs.all() ],
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

        # Make sure we can fetch credentials too
        url = "targets/%s/target_user_credentials" % target.target_id
        resp = self._get(url, username="admin", password="password")
        self.failUnlessEqual(resp.status_code, 200)
        doc = xobj.parse(resp.content)
        self.failUnlessEqual(doc.target_user_credentials.user.id,
            "http://testserver/api/v1/users/1")
        self.failUnlessEqual(doc.target_user_credentials.credentials.username,
            "forrest")

        # Reset user credentials
        resp = self._delete(url, username="admin", password="password")
        doc = xobj.parse(resp.content)
        self.failUnlessEqual(doc.target_user_credentials.user.id,
            "http://testserver/api/v1/users/1")
        self.failUnlessEqual(resp.status_code, 200)

        # Gone, baby, gone
        resp = self._get(url, username="admin", password="password")
        self.failUnlessEqual(resp.status_code, 404)

    def testRefreshTargetImages(self):
        jobType = jmodels.EventType.objects.get(name=jmodels.EventType.TARGET_REFRESH_IMAGES)
        target = models.Target.objects.get(name='Target Name vmware')
        jobXml = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/targets/%(targetId)s/descriptors/refresh_images"/>
  <descriptor_data/>
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
            "http://testserver/api/v1/targets/%s/descriptors/refresh_images" %  target.target_id)

        dbjob = jmodels.Job.objects.get(job_uuid=job.job_uuid)
        # Make sure the job is related to the target type
        self.failUnlessEqual(
            [ x.target.name for x in dbjob.target_jobs.all() ],
            [ target.name ],
        )

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            ['targets.TargetConfiguration', 'targets.TargetUserCredentials',
                'targets.configure', 'targets.listImages'])
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

        # No images initially
        models.TargetImage.objects.all().delete()

        # Grab token
        jobToken = dbjob.job_token
        jobUrl = "jobs/%s" % dbjob.job_uuid
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.status_code, '401')


        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Some status here</status_text>
  <results encoding="identity">
    <images>
      <image id="id1">
        <imageId>id1</imageId>
        <longName>long name for id1</longName>
        <shortName>short name for id1</shortName>
        <productName>product name for id1</productName>
        <internalTargetId>uuid1</internalTargetId>
      </image>
    </images>
  </results>
</job>
"""
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.job.id, "http://testserver/api/v1/" + jobUrl)

        images = models.TargetImage.objects.filter(target=target)
        self.failUnlessEqual([ x.name for x in images ],
            ['product name for id1'])
        self.failUnlessEqual([ x.description for x in images ],
            ['long name for id1'])

        # Add 2 more images
        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Some status here</status_text>
  <results encoding="identity">
    <images>
      <image id="id1">
        <imageId>id1</imageId>
        <longName>long name for id1</longName>
        <shortName>short name for id1</shortName>
        <productName>product name for id1</productName>
        <internalTargetId>uuid1</internalTargetId>
      </image>
      <image id="id2">
        <imageId>id2</imageId>
        <longName>long name for id2</longName>
        <shortName>short name for id2</shortName>
        <productName>product name for id2</productName>
        <internalTargetId>uuid2</internalTargetId>
      </image>
      <image id="id3">
        <imageId>id3</imageId>
        <longName>long name for id3</longName>
        <shortName>short name for id3</shortName>
        <productName>product name for id3</productName>
        <internalTargetId>uuid3</internalTargetId>
      </image>
    </images>
  </results>
</job>
"""

        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.job.id, "http://testserver/api/v1/" + jobUrl)

        images = models.TargetImage.objects.filter(target=target)
        self.failUnlessEqual([ x.name for x in images ],
            ['product name for id1', 'product name for id2', 'product name for id3'])
        self.failUnlessEqual([ x.description for x in images ],
            ['long name for id1', 'long name for id2', 'long name for id3'])

        # Remove first, modify second
        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Some status here</status_text>
  <results encoding="identity">
    <images>
      <image id="id2">
        <imageId>id2</imageId>
        <longName>long name for id2</longName>
        <shortName>short name for id2</shortName>
        <productName>modified product name for id2</productName>
        <internalTargetId>uuid2</internalTargetId>
      </image>
      <image id="id3">
        <imageId>id3</imageId>
        <longName>long name for id3</longName>
        <shortName>short name for id3</shortName>
        <productName>product name for id3</productName>
        <internalTargetId>uuid3</internalTargetId>
      </image>
    </images>
  </results>
</job>
"""
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.job.id, "http://testserver/api/v1/" + jobUrl)

        images = models.TargetImage.objects.filter(target=target)
        self.failUnlessEqual([ x.name for x in images ],
            ['modified product name for id2', 'product name for id3'])
        self.failUnlessEqual([ x.description for x in images ],
            ['long name for id2', 'long name for id3'])

        # Make sure we have proper linkage in target_image_credentials
        creds = models.TargetCredentials.objects.filter(
            target_user_credentials__user__user_name='testuser')[0]
        images = models.TargetImage.objects.filter(
            target_image_credentials__target_credentials=creds)
        self.failUnlessEqual([ x.name for x in images ],
            ['modified product name for id2', 'product name for id3'])

    def testRefreshTargetSystems(self):
        jobType = jmodels.EventType.objects.get(name=jmodels.EventType.TARGET_REFRESH_SYSTEMS)
        target = models.Target.objects.get(name='Target Name vmware')
        jobXml = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/targets/%(targetId)s/descriptors/refresh_systems"/>
  <descriptor_data/>
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
            "http://testserver/api/v1/targets/%s/descriptors/refresh_systems" %  target.target_id)

        dbjob = jmodels.Job.objects.get(job_uuid=job.job_uuid)
        # Make sure the job is related to the target type
        self.failUnlessEqual(
            [ x.target.name for x in dbjob.target_jobs.all() ],
            [ target.name ],
        )

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            ['targets.TargetConfiguration', 'targets.TargetUserCredentials',
                'targets.configure', 'targets.listInstances'])
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

        # No images initially
        models.TargetSystem.objects.all().delete()

        # Grab token
        jobToken = dbjob.job_token
        jobUrl = "jobs/%s" % dbjob.job_uuid
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.status_code, '401')


        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Some status here</status_text>
  <results encoding="identity">
    <instances>
      <instance id="/clouds/vmware/instances/vsphere.eng.rpath.com/instances/4234dc2c-6b91-5188-2a3c-5e6f88b61835" xmlNodeHash="7094de9821eaf555e995cd537f2af331bc434893">
        <dnsName>172.16.175.73</dnsName>
        <instanceDescription/>
        <instanceId>4234dc2c-6b91-5188-2a3c-5e6f88b61835</instanceId>
        <instanceName>Target System 1</instanceName>
        <launchTime>1312812708</launchTime>
        <publicDnsName>172.16.175.73</publicDnsName>
        <reservationId>4234dc2c-6b91-5188-2a3c-5e6f88b61835</reservationId>
        <state>poweredOn</state>
      </instance>
    </instances>
  </results>
</job>
"""
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.job.id, "http://testserver/api/v1/" + jobUrl)

        systems = models.TargetSystem.objects.filter(target=target)
        self.failUnlessEqual([ x.name for x in systems ],
            ['Target System 1'])
        self.failUnlessEqual([ x.description for x in systems ],
            [''])

        # Add 2 more images
        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Some status here</status_text>
  <results encoding="identity">
    <instances>
      <instance id="/clouds/vmware/instances/vsphere.eng.rpath.com/instances/4234dc2c-6b91-5188-2a3c-5e6f88b61835" xmlNodeHash="7094de9821eaf555e995cd537f2af331bc434893">
        <dnsName>172.16.175.73</dnsName>
        <instanceDescription/>
        <instanceId>4234dc2c-6b91-5188-2a3c-5e6f88b61835</instanceId>
        <instanceName>Target System 1</instanceName>
        <launchTime>1312812708</launchTime>
        <publicDnsName>172.16.175.73</publicDnsName>
        <reservationId>4234dc2c-6b91-5188-2a3c-5e6f88b61835</reservationId>
        <state>poweredOn</state>
      </instance>
      <instance id="id2">
        <instanceId>id2</instanceId>
        <instanceName>name for id2</instanceName>
        <instanceDescription>long name for id2</instanceDescription>
        <launchTime>1234567890</launchTime>
        <state>suspended</state>
      </instance>
      <instance id="id3">
        <instanceId>id3</instanceId>
        <instanceName>name for id3</instanceName>
        <instanceDescription>long name for id3</instanceDescription>
        <launchTime>1234567891</launchTime>
        <state>blabbering</state>
      </instance>
    </instances>
  </results>
</job>
"""

        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.job.id, "http://testserver/api/v1/" + jobUrl)

        systems = models.TargetSystem.objects.filter(target=target)
        self.failUnlessEqual([ x.name for x in systems ],
            ['Target System 1', 'name for id2', 'name for id3', ])
        self.failUnlessEqual([ x.description for x in systems ],
            ['', 'long name for id2', 'long name for id3', ])

        # Remove first, modify second
        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Some status here</status_text>
  <results encoding="identity">
    <instances>
      <instance id="id2">
        <instanceId>id2</instanceId>
        <instanceName>name for id2</instanceName>
        <instanceDescription>long name for id2</instanceDescription>
        <launchTime>1234567890</launchTime>
        <state>blabbering</state>
      </instance>
      <instance id="id3">
        <instanceId>id3</instanceId>
        <instanceName>name for id3</instanceName>
        <instanceDescription>long name for id3</instanceDescription>
        <launchTime>1234567891</launchTime>
        <state>blabbering</state>
      </instance>
    </instances>
  </results>
</job>
"""
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.job.id, "http://testserver/api/v1/" + jobUrl)

        systems = models.TargetSystem.objects.filter(target=target)
        self.failUnlessEqual([ x.name for x in systems ],
            ['name for id2', 'name for id3', ])
        self.failUnlessEqual([ x.description for x in systems ],
            ['long name for id2', 'long name for id3', ])
        self.failUnlessEqual([ x.state for x in systems ],
            ['blabbering', 'blabbering', ])

        # Make sure we have proper linkage in target_image_credentials
        creds = models.TargetCredentials.objects.filter(
            target_user_credentials__user__user_name='testuser')[0]
        systems = models.TargetSystem.objects.filter(
            target_system_credentials__target_credentials=creds)
        self.failUnlessEqual([ x.name for x in systems ],
            ['name for id2', 'name for id3', ])

    def testCaptureSystem(self):
        invmodels.System.objects.all().delete()
        targetType = models.TargetType.objects.get(name='vmware')
        target = models.Target.objects.filter(target_type=targetType)[0]
        system = self._saveSystem()
        system.target = target
        system.target_system_id = "efe28c20-bbda-434c-87ae-9f4006114a1f"
        system.save()
        self.mgr.retagQuerySetsByType('system')

        targetCredentials = dict(username="vmwareuser", password="sikrit")
        # Add target user credentials for admin
        self.mgr.setTargetUserCredentials(target, targetCredentials)

        # Use admin for now, rbac write is required
        response = self._get('inventory/systems/%s/descriptors/capture' % 1999,
            username='admin', password='password')
        self.assertEquals(response.status_code, 404)
        response = self._get('inventory/systems/%s/descriptors/capture' % system.system_id,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.descriptor.metadata.rootElement, 'descriptor_data')
        self.failUnlessEqual(
            [ x.name for x in obj.descriptor.dataFields.field ],
            [
                'instanceId', 'imageTitle', 'architecture', 'stageId',
                'metadata_owner', 'metadata_admin',
        ])
        stageDescs = obj.descriptor.dataFields.field[3].enumeratedType.describedValue
        self.failUnlessEqual(
            [ x.descriptions.desc for x in stageDescs ],
            [
                'chater-foo / 1 / Development',
                'chater-foo / 1 / QA',
                'chater-foo / 1 / Release',
            ])
        self.failUnlessEqual(
            [ x.key for x in stageDescs ],
            [ '1', '2', '3', ])
        self.failUnlessEqual(obj.descriptor.dataFields.field[0].default,
            system.target_system_id)
        self.failUnlessEqual(obj.descriptor.dataFields.field[3].default, '1')

        # Post a job
        jobXmlTmpl = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/inventory/systems/%(systemId)s/descriptors/capture"/>
  <descriptor_data>
    <imageTitle>%(imageTitle)s</imageTitle>
    <instanceId>%(instanceId)s</instanceId>
    <stageId>%(stageId)s</stageId>
    <architecture>%(arch)s</architecture>
    <metadata_owner>%(owner)s</metadata_owner>
    <metadata_admin>%(admin)s</metadata_admin>
  </descriptor_data>
</job>
"""
        systemId = system.system_id
        jobXml = jobXmlTmpl % dict(jobTypeId=21, systemId=systemId,
            instanceId=system.target_system_id,
            imageTitle="Captured image from system 1",
            arch='x86_64',
            owner="Owner",
            admin="Admin",
            stageId='1')
        jobUrl = "inventory/systems/%s/jobs" % systemId
        response = self._post(jobUrl, jobXml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/inventory/systems/%s/descriptors/capture"
                % systemId)

        dbjob = jmodels.Job.objects.get(job_uuid=job.job_uuid)
        jobToken = dbjob.job_token
        self.failUnlessEqual(dbjob.job_type.name, dbjob.job_type.SYSTEM_CAPTURE)
        self.failUnlessEqual(
            [ x.system.name for x in dbjob.systems.all() ],
            [ 'testsystemname' ],
        )

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            [
                'targets.TargetConfiguration', 'targets.TargetUserCredentials',
                'targets.configure', 'targets.captureSystem',
            ])
        realCall = calls[-1]
        params = {
            'architecture' : 'x86_64',
            'imageName': u'Captured_image_from_system_1.ova',
            'imageTitle': u'Captured image from system 1',
            'instanceId': 'efe28c20-bbda-434c-87ae-9f4006114a1f',
            'metadata_admin': u'Admin',
            'metadata_owner': u'Owner',
            'image_id': 'https://bubba.com/api/v1/images/1',
            'imageUploadUrl': 'https://bubba.com/uploadBuild/1',
            'imageFilesCommitUrl': u'https://bubba.com/api/products/chater-foo/images/1/files',
        }
        from ..images import models as imgmodels
        outputToken = imgmodels.ImageData.objects.filter(name='outputToken')[0].value
        params['outputToken'] = outputToken
        # XXX get around stipid siteHost being mocked by who knows whom
        self.failUnlessEqual(realCall.args[0], system.target_system_id)
        mungedParams = self._mungeDict(realCall.args[1])
        self.failUnlessEqual(mungedParams, params)
        self.failUnlessEqual(realCall.kwargs, {})
        self.mgr.repeaterMgr.repeaterClient.reset()

        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Some status here</status_text>
  <results encoding="identity">
    <image id="/1"/>
  </results>
</job>
"""
        jobUrl = "jobs/%s" % dbjob.job_uuid
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.job.id, "http://testserver/api/v1/" + jobUrl)
        self.failUnlessEqual(obj.job.results.id, "http://testserver/api/v1/images/1")

        response = self._get("images/1",
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.image.name, params['imageTitle'])
        self.failUnlessEqual(obj.image.image_type.key, 'VMWARE_ESX_IMAGE')
        self.failUnlessEqual(obj.image.job_uuid, dbjob.job_uuid)

    def _mungeDict(self, dictObj):
        r = re.compile('https://([^/]*)/')
        mungedParams = dict((x, r.sub('https://bubba.com/', y))
            for (x, y) in dictObj.items()
                if isinstance(y, basestring))
        mungedParams.update((x, y) for (x, y) in dictObj.items()
                if not isinstance(y, basestring))
        return mungedParams

    def _setupImages(self):
        targetType = models.TargetType.objects.get(name='vmware')
        target1 = models.Target.objects.filter(target_type=targetType)[0]
        targetType = models.TargetType.objects.get(name='openstack')
        target2 = models.Target.objects.filter(target_type=targetType)[0]

        targetData = [
            (target1, buildtypes.VMWARE_ESX_IMAGE),
            (target2, buildtypes.RAW_HD_IMAGE),
        ]

        # We need to set a user, image creation needs it
        user = self.getUser('testuser')
        self.mgr.user = user

        # Create a project for the images
        branch = self.getProjectBranch(label='chater-foo.eng.rpath.com@rpath:chater-foo-1')
        stage = self.getProjectBranchStage(branch=branch, name="Development")

        targetImageIdTempl = "target-internal-id-%02d"
        imgmgr = self.mgr.imagesManager
        for i in range(4):
            for target, imageType in targetData:
                image = imgmgr.createImage(
                    _image_type=imageType,
                    name = "image %02d" % i,
                    description = "image %02d description" % i,
                    project_branch_stage=stage,
                )
                imgmgr.createImageBuild(image)
                bf = imgmgr.createImageBuildFile(image,
                    url="filename-%02d-%02d" % (imageType, i),
                    title="Image File Title %02d" % i,
                    size=100+i,
                    sha1="%040d" % i)
                if i % 2 == 0:
                    imgbuild = imgmgr.recordTargetInternalId(
                        buildFile=bf, target=target,
                        targetInternalId=targetImageIdTempl % i)

                # Add a bunch of target images
                j = i + 2
                models.TargetImage.objects.create(
                    target = target,
                    name="target image name %02d" % j,
                    description="target image description %02d" % j,
                    target_internal_id=targetImageIdTempl % j)

                # Create deferred images too
                self.createDefferredImage(image,
                    "Deferred image based on %s" % image.image_id,
                    projectBranchStage=stage)

        return [ target1, target2 ]

    def createDefferredImage(self, baseImage, name, description=None,
            projectBranchStage=None):
        imgmgr = self.mgr.imagesManager
        image = imgmgr.createImage(_image_type=buildtypes.DEFERRED_IMAGE,
            name=name, description=None,
            project_branch_stage=projectBranchStage,
            base_image=baseImage)
        imgmgr.createImageBuild(image)
        # Deferred images have no build files
        return image

    def testRecomputeTargetDeployableImages(self):
        targets = self._setupImages()
        self.mgr.targetsManager.recomputeTargetDeployableImages()

        target1 = targets[0]

        for imgName in [ "image 00", "image 01", "image 03" ]:
            img = imgmodels.Image.objects.get(name=imgName, _image_type=buildtypes.VMWARE_ESX_IMAGE)
            self.failUnlessEqual(
                [
                    [ tdi.target_image
                        for tdi in imgfile.target_deployable_images.all() ]
                    for imgfile in img.files.all() ],
                [[None]]
            )

        imgName = "image 02"
        img = imgmodels.Image.objects.get(name=imgName, _image_type=buildtypes.VMWARE_ESX_IMAGE)
        self.failUnlessEqual(
            [
                [ tdi.target_image.target_internal_id
                    for tdi in imgfile.target_deployable_images.all() ]
                for imgfile in img.files.all() ],
            [['target-internal-id-02']]
        )

        url = "images/%s" % img.image_id
        resp = self._get(url, username="testuser", password="password")
        self.failUnlessEqual(resp.status_code, 200)
        doc = xobj.parse(resp.content)
        actions = doc.image.actions.action
        self.failUnlessEqual([ x.name for x in actions ],
            ["Deploy image on 'Target Name vmware' (vmware)",
             "Launch system on 'Target Name vmware' (vmware)",
            ])
        file1 = img.files.all()[0]
        self.failUnlessEqual([ x.descriptor.id for x in actions ],
            [
            'http://testserver/api/v1/targets/%s/descriptors/deploy/file/%s' %
                (target1.target_id, file1.file_id),
            'http://testserver/api/v1/targets/%s/descriptors/launch/file/%s' %
                (target1.target_id, file1.file_id),
            ])
        self.failUnlessEqual(doc.image.jobs.id,
            'http://testserver/api/v1/images/%s/jobs' % img.image_id)

        # Fetch deployment descriptor
        url = 'targets/%s/descriptors/deploy/file/%s' % (target1.target_id,
            file1.file_id)

        self.mgr.repeaterMgr.repeaterClient.setJobData("""\
<descriptor>
  <metadata>
    <displayName>FooDescriptor</displayName>
    <rootElement>blah</rootElement>
    <descriptions><desc>Description</desc></descriptions>
  </metadata>
  <dataFields>
    <field>
      <name>imageId</name>
      <descriptions>
        <desc>Image ID</desc>
      </descriptions>
      <type>str</type>
      <required>true</required>
      <hidden>true</hidden>
    </field>
  </dataFields>
</descriptor>""")
        resp = self._get(url, username="testuser", password="password")
        self.failUnlessEqual(resp.status_code, 200)
        doc = xobj.parse(resp.content)
        self.failUnlessEqual(doc.descriptor.metadata.displayName, "FooDescriptor")
        self.failUnlessEqual(doc.descriptor.metadata.rootElement, "descriptor_data")
        self.failUnlessEqual(doc.descriptor.dataFields.field.default, "5")

        baseImg = img

        # Check deferred image
        imgName = "image 02"
        img = imgmodels.Image.objects.get(
            name="Deferred image based on %s" % baseImg.image_id,
            _image_type=buildtypes.DEFERRED_IMAGE)

        url = "images/%s" % img.image_id
        resp = self._get(url, username="testuser", password="password")
        self.failUnlessEqual(resp.status_code, 200)
        doc = xobj.parse(resp.content)
        actions = doc.image.actions.action
        self.failUnlessEqual([ x.name for x in actions ],
            ["Deploy image on 'Target Name vmware' (vmware)",
             "Launch system on 'Target Name vmware' (vmware)",
            ])
        # We should be referring to the base image's files
        file1 = baseImg.files.all()[0]
        self.failUnlessEqual([ x.descriptor.id for x in actions ],
            [
            'http://testserver/api/v1/targets/%s/descriptors/deploy/file/%s' %
                (target1.target_id, file1.file_id),
            'http://testserver/api/v1/targets/%s/descriptors/launch/file/%s' %
                (target1.target_id, file1.file_id),
            ])
        self.failUnlessEqual(doc.image.jobs.id,
            'http://testserver/api/v1/images/%s/jobs' % img.image_id)

    def testDeployImage(self):
        targets = self._setupImages()
        imgName = "image 02"
        img = imgmodels.Image.objects.get(name=imgName, _image_type=buildtypes.VMWARE_ESX_IMAGE)
        self._testDeployImage(targets, img)

    def testDeployDeferredImage(self):
        targets = self._setupImages()
        imgName = "image 02"
        img = imgmodels.Image.objects.get(name=imgName, _image_type=buildtypes.VMWARE_ESX_IMAGE)
        deferredImg = imgmodels.Image.objects.get(base_image=img)
        self._testDeployImage(targets, deferredImg, img)

    def _testDeployImage(self, targets, img, baseImg=None):
        self.mgr.targetsManager.recomputeTargetDeployableImages()

        # Post a job
        jobXmlTmpl = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/targets/%(targetId)s/descriptors/deploy/file/%(buildFileId)s"/>
  <descriptor_data>
    <imageId>%(buildFileId)s</imageId>
  </descriptor_data>
</job>
"""

        if baseImg is None:
            baseImg = img

        buildFileId = baseImg.files.all()[0].file_id
        imageId = img.image_id
        targetId = targets[0].target_id
        jobTypeId = self.mgr.sysMgr.eventType(jmodels.EventType.TARGET_DEPLOY_IMAGE).job_type_id

        jobXml = jobXmlTmpl % dict(
                jobTypeId=jobTypeId,
                targetId=targetId,
                buildFileId = buildFileId,)
        jobUrl = "images/%s/jobs" % imageId
        response = self._post(jobUrl, jobXml,
            username='testuser', password='password')
        self.failUnlessEqual(response.status_code, 200)
        obj = xobj.parse(response.content)

        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/targets/%s/descriptors/deploy/file/%s"
                % (targetId, buildFileId))

        dbjob = jmodels.Job.objects.get(job_uuid=job.job_uuid)
        jobToken = dbjob.job_token
        self.failUnlessEqual(dbjob.job_type.name, dbjob.job_type.TARGET_DEPLOY_IMAGE)
        imageNames = [ 'image 02' ]
        if baseImg is not img:
            imageNames.append(img.name)
        self.failUnlessEqual(
            [ x.image.name for x in dbjob.images.all() ],
            imageNames)

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            [
                'targets.TargetConfiguration', 'targets.TargetUserCredentials',
                'targets.configure', 'targets.deployImage',
            ])
        realCall = calls[-1]
        self.failUnlessEqual(self._mungeDict(realCall.args[0]),
          {
            'imageFileInfo': {
                'fileId' : buildFileId,
                'name' : u'filename-09-02',
                'sha1' : u'0000000000000000000000000000000000000002',
                'size' : 102,
                'baseFileName' : 'chater-foo-1-',
            },
            'descriptorData': "<?xml version='1.0' encoding='UTF-8'?>\n<descriptor_data>\n  <imageId>%s</imageId>\n</descriptor_data>\n" % buildFileId,
            'imageDownloadUrl': 'https://bubba.com/downloadImage?fileId=%s' % buildFileId,
            'imageFileUpdateUrl': 'http://localhost/api/v1/images/%s/build_files/%s' % (baseImg.image_id, buildFileId),
            'targetImageXmlTemplate': '<file>\n  <target_images>\n    <target_image>\n      <target id="/api/v1/targets/1"/>\n      %(image)s\n    </target_image>\n  </target_images>\n</file>'
          })
        self.failUnlessEqual(realCall.args[1:], ())
        self.failUnlessEqual(realCall.kwargs, {})

        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Some status here</status_text>
  <results encoding="identity">
    <image id="/1">
      <baseFileName>cobbler-clone</baseFileName>
    </image>
  </results>
</job>
"""
        jobUrl = "jobs/%s" % dbjob.job_uuid
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.failUnlessEqual(response.status_code, 200)
