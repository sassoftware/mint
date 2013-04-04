#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

import json
import collections
import re
from lxml import etree

from mint import buildtypes
from mint.lib import data as mintdata
from mint.django_rest.test_utils import RepeaterMixIn
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
import mint.jobstatus as jobstatus

# TODO: would be nice to make RbacSetup more of a mixin
class BaseTargetsTest(RbacEngine):

    def setUp(self):
        RbacEngine.setUp(self)
        self._initTestFixtures()
        self._mock()
        self._setupRbac()

    def _markAllImagesAsFinished(self):
        # images are RBACed and images don't show up in querysets unless finished.
        # querysets are the basis of RBAC.  Ergo, make stuff not 403
        images = imgmodels.Image.objects.all()
        for x in images:
            x.status = jobstatus.FINISHED
            x.save()
        self._retagQuerySets() 

    def _initTestFixtures(self):
        sampleTargetTypes = [ models.TargetType.objects.get(name=x)
            for x in ['vmware', 'ec2', 'xen-enterprise', 'openstack', 'vcloud'] ]

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
        # Add another target with no credentials
        models.Target.objects.create(name="Target without credentials",
            description="Target without credentials",
            target_type=sampleTargetTypes[0],
            state=0, zone=lz)
        self.targetTypes = sampleTargetTypes
        self.targets = sampleTargets

        eventUuid1 = 'eventuuid001'
        jobUuid1 = 'rmakeuuid001'
        eventUuid2 = 'eventuuid002'
        jobUuid2 = 'rmakeuuid002'
        eventUuid3 = 'eventuuid003'
        jobUuid3 = 'rmakeuuid003'
        system = self._saveSystem()
        
        user = self.developer_user

        jobs = []
        jobs.append(self._newSystemJob(system, eventUuid1, jobUuid1,
            jmodels.EventType.SYSTEM_REGISTRATION, createdBy=user))
        jobs.append(self._newSystemJob(system, eventUuid2, jobUuid2,
            jmodels.EventType.SYSTEM_UPDATE, createdBy=user))
        jobs.append(self._newSystemJob(system, eventUuid3, jobUuid3,
            jmodels.EventType.SYSTEM_SCAN, createdBy=user))

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

        targetCredentials = []
        for i in range(2):
            creds = dict(username="username-%s" % i, password="password-%s" % i)
            targetCredentials.append(models.TargetCredentials.objects.create(
                credentials=mintdata.marshalTargetUserCredentials(None, creds)))

        u0 = user
        u1 = self.intern_user
        u2 = self.sysadmin_user
        tc0 = targetCredentials[0]
        tc1 = targetCredentials[1]
        # Share some of the creds between targets
        tucmap = [
            [ (u0, tc0), (u1, tc1), (u2, tc0) ],
            [ (u0, tc0), (u1, tc1), (u2, tc0) ],
            [ (u0, tc0), (u1, tc1), (u2, tc0) ],
        ]

        for i, tucList in enumerate(tucmap):
            tgt = sampleTargets[i]
            for u, tc in tucList:
                models.TargetUserCredentials.objects.create(
                    target=tgt,
                    user=u,
                    target_credentials=tc)

        self.target_credentials = models.TargetCredentials.objects.all()
        self.target_user_credentials = models.TargetUserCredentials.objects.all()
        self.mgr.user = user

    def _mock(self):
        tmgr = self.mgr.targetsManager
        fakeAuth = collections.namedtuple("FakeAuth", "userId")
        self.mock(tmgr.mgr, '_auth', fakeAuth(self.mgr.user.user_id))

    # invalidate the querysets so tags can be applied
    def _retagQuerySets(self):
        self.mgr.retagQuerySetsByType('project')
        self.mgr.retagQuerySetsByType('image')

    def _setupRbac(self):

        # RbacEngine test base class has already done a decent amount of setup
        # now just add the grants for the things we are working with

        role              = rbacmodels.RbacRole.objects.get(name='developer')
        self.all_targets  = querymodels.QuerySet.objects.get(name='All Targets')
        self.all_images   = querymodels.QuerySet.objects.get(name='All Images')
        self.all_systems  = querymodels.QuerySet.objects.get(name='All Systems')
        modmembers        = rbacmodels.RbacPermissionType.objects.get(name='ModMembers')
        readset           = rbacmodels.RbacPermissionType.objects.get(name='ReadSet')
        createresource    = rbacmodels.RbacPermissionType.objects.get(name='CreateResource')
        admin             = usermodels.User.objects.get(user_name='admin')

        for queryset in [ self.all_targets, self.all_images, self.all_systems ]:
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
            username='ExampleDeveloper', password='password')
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

    def testGetTargets(self):
        targets = models.Target.objects.order_by('target_id')
        response = self._get('targets/', username='ExampleDeveloper', password='password')
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
                'http://testserver/api/v1/targets/5',
                'http://testserver/api/v1/targets/6',
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
        models.TargetUserCredentials.objects.filter(target__name = 'Target Name xen-enterprise').delete()
        response = self._get('targets/', username='ExampleDeveloper', password='password')
        targetsObj = xobj.parse(response.content)
        self.failUnlessEqual([ x.name for x in targetsObj.targets.target ],
            [
                'Target Name vmware',
                'Target Name ec2',
                'Target Name xen-enterprise',
                'Target Name openstack',
                'Target Name vcloud',
                'Target without credentials',
            ])
        self.failUnlessEqual([ x.credentials_valid for x in targetsObj.targets.target ],
            ['true', 'true', 'false', 'false', 'false', 'false', ])
        self.failUnlessEqual([ x.is_configured for x in targetsObj.targets.target ],
            ['true', 'true', 'true', 'true', 'true', 'true', ])

    def testGetTarget(self):
        target = models.Target.objects.get(name = 'Target Name openstack')
        response = self._get('targets/%s' % target.pk,
            username='ExampleDeveloper', password='password')
        target_gotten = xobj.parse(response.content).target
        self.assertEquals(response.status_code, 200)
        self.assertEquals(target.name, target_gotten.name)
        self.assertXMLEquals(response.content, testsxml.target_GET)

    def testGetTargetConfigurationDescriptor(self):
        # #2289: multi-zone with no zone description should not break
        # the code
        zmodels.Zone.objects.create(name="zone without description")

        target = models.Target.objects.get(name = 'Target Name openstack')
        response = self._get('targets/%s/descriptors/configuration' % target.pk,
            username='ExampleDeveloper', password='password')
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
        self.failUnlessEqual(
            [ (x.key, x.descriptions.desc)
                for x in obj.descriptor.dataFields.field[-1].enumeratedType.describedValue ],
            [
                (u'Local rBuilder', u'Local rBuilder management zone'),
                (u'zone without description', u'zone without description'),
            ]
        )
        helpTemplate = '/help/targets/drivers/openstack/configuration/%s.html'
        self.failUnlessEqual(
            [ x.help.href for x in obj.descriptor.dataFields.field[:-1] ],
            [ helpTemplate % x for x in [
                'novaServerName',
                'novaPortNumber',
                'glanceServerName',
                'glancePortNumber',
                'alias',
                'description',
        ]])
        self.failUnlessEqual(
            getattr(obj.descriptor.dataFields.field[-1], 'help', None), None)

    def testCreateTarget(self):
        zmodels.Zone.objects.create(name='other zone', description = "Other Zone")

        img = self.addImage(name="image sample",
            imageType=buildtypes.VMWARE_ESX_IMAGE)
        self.mgr.retagQuerySetsByType('image')

        # No deployable images
        self.failUnlessEqual(
            [ x for x in models.TargetDeployableImage.objects.all() ],
            [])

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

        # Fetch target configuration
        response = self._get('targets/%s/target_configuration' % dbobj.target_id,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.target_configuration.description,
            'Target Description')
        self.failUnlessEqual(obj.target_configuration.name, 'Target Name 4')
        self.failUnlessEqual(obj.target_configuration.zone, 'other zone')

        tdi = models.TargetDeployableImage.objects.filter(target=dbobj)
        bf = img.files.all()[0]
        self.failUnlessEqual(
            [ x.build_file.file_id for x in tdi ],
            [ bf.file_id, ])

        # RCE-572 re-creating the target should fail with 409
        data = testsxml.target_POST.replace('Target Description',
            'New description')
        response = self._post('targets/', username='admin', password='password',
            data=data)
        self.assertEquals(response.status_code, 409)

    def testUpdateTarget(self):
        response = self._put('targets/1', username='admin', password='password',
            data=testsxml.target_PUT)
        # Target updates are done via actions
        self.assertEquals(response.status_code, 405)

    def testDeleteTarget(self):
        response = self._delete('targets/1', username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 403)
        response = self._delete('targets/1', username='admin', password='password')
        self.assertEquals(response.status_code, 204)

    def testGetTargetTypes(self):
        targetTypesExpected = models.TargetType.objects.order_by('target_type_id')
        response = self._get('target_types/', username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        targetTypes = xobj.parse(response.content)
        self.failUnlessEqual(
            [ x.name for x in targetTypes.target_types.target_type ],
            [ x.name for x in targetTypesExpected ])

    def testGetTargetType(self):
        targetType = models.TargetType.objects.get(name='openstack')
        response = self._get('target_types/%s' % targetType.pk,
            username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.target_type_GET)

    def testGetTargetsForTargetType(self):
        targetType = models.TargetType.objects.get(name='openstack')
        models.Target.objects.filter(target_type=targetType).delete()
        models.Target.objects.create(target_type=targetType, state=0,
            name="test openstack", description="test openstack",
            zone=self.localZone)
        response = self._get('target_types/%s/targets' % targetType.pk,
            username='ExampleDeveloper', password='password')
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
            username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.target_type_by_target_id_GET)

    def testGetTargetTypeDescriptorCreateTarget(self):
        response = self._get('target_types/1024/descriptor_create_target',
            username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 404)
        response = self._get('target_types/1/descriptor_create_target',
            username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.descriptor.metadata.rootElement, 'descriptor_data')
        self.failUnlessEqual(
            [ x.name for x in obj.descriptor.dataFields.field ],
            [
                'name',
                'alias',
                'description',
                'region',
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
            username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 404)
        response = self._get('targets/1/descriptors/configure_credentials',
            username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.descriptor.metadata.rootElement, 'descriptor_data')
        self.failUnlessEqual(
            [ x.name for x in obj.descriptor.dataFields.field ],
            [
                'username',
                'password',
            ])
        # RCE-807: no need to have help for username and password
        return
        helpTemplate = '/help/targets/drivers/vmware/credentials/%s.html'
        self.failUnlessEqual(
            [ x.help.href for x in obj.descriptor.dataFields.field ],
            [ helpTemplate % x for x in [
                'username',
                'password',
        ]])

    def testGetTargetDescriptorRefreshImages(self):
        response = self._get('targets/1024/descriptors/refresh_images',
            username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 404)
        response = self._get('targets/1/descriptors/refresh_images',
            username='ExampleDeveloper', password='password')
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
        response = self._get(url, username='ExampleDeveloper', password='password')
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
            username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id, "http://testserver/api/v1/target_types/6/descriptor_create_target")

        dbjob = jmodels.Job.objects.get(job_uuid=unicode(job.job_uuid))
        # Make sure the job is related to the target type
        self.failUnlessEqual(
            [ x.target_type.name for x in dbjob.jobtargettype_set.all() ],
            [ 'xen-enterprise' ],
        )

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            ['targets.configure', 'targets.checkCreate'])
        realCall = calls[-1]
        self.failUnlessEqual(realCall.args, ())
        self.failUnlessEqual(realCall.kwargs, dict(uuid=job.job_uuid))
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
        self.failUnlessEqual(job.results.target.id, "http://testserver/api/v1/targets/7")
        self.failUnlessEqual(job.status_code, "200")
        self.failUnlessEqual(job.status_text, "Done")

        # Post again. We shouldn't create it again
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.status_code, "409")
        self.failUnlessEqual(job.status_text, "Duplicate Target")

    def testTargetConfiguration(self):
        # Add credentials for admin
        targetType = self.mgr.getTargetTypeByName('vmware')
        target = models.Target.objects.filter(target_type=targetType)[0]
        testUser = self.getUser('ExampleDeveloper')
        adminUser = self.getUser('admin')
        models.TargetUserCredentials.objects.create(
            target=target,
            user=adminUser,
            target_credentials=models.TargetCredentials.objects.filter(
                target_user_credentials__user=testUser,
                target_user_credentials__target=target)[0])
        jobXmlTmpl  = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/22"/>
  <descriptor id="http://testserver/api/v1/targets/%(targetId)s/descriptors/configuration"/>
  <descriptor_data>
    <alias>%(targetAlias)s</alias>
    <description>%(targetDescription)s</description>
    <name>%(targetName)s</name>
    <zone>Local rBuilder</zone>
  </descriptor_data>
</job>
"""
        targetAlias = 'newbie'
        targetName = 'newbie.eng.rpath.com'
        targetDescription = 'Brand new cloud'
        jobXml = jobXmlTmpl % dict(targetId=target.target_id,
            targetName=targetName, targetDescription=targetDescription,
            targetAlias=targetAlias)
        response = self._post('targets/%s/jobs' % target.target_id, jobXml,
            username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 403)

        response = self._post('targets/%s/jobs' % target.target_id, jobXml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/targets/%d/descriptors/configuration" % target.target_id)

        dbjob = jmodels.Job.objects.get(job_uuid=unicode(job.job_uuid))
        # Make sure the job is related to the target type
        self.failUnlessEqual(
            [ x.target.name for x in dbjob.target_jobs.all() ],
            [ 'Target Name vmware' ],
        )

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            ['targets.configure', 'targets.checkCreate'])
        realCall = calls[-1]
        self.failUnlessEqual(realCall.args, ())
        self.failUnlessEqual(realCall.kwargs, dict(uuid=job.job_uuid))
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
        self.failUnlessEqual(job.results.target.id,
            "http://testserver/api/v1/targets/%s" % target.target_id)
        self.failUnlessEqual(job.status_code, "200")
        self.failUnlessEqual(job.status_text, "Done")

        target = models.Target.objects.get(target_id=target.target_id)
        self.failUnlessEqual(target.name, targetName)

    def testTargetConfigurationDuplicate(self):
        targetType = self.mgr.getTargetTypeByName('vmware')
        target = models.Target.objects.filter(target_type=targetType)[0]

        tmpName = str(self.uuid4())
        target1 = models.Target.objects.create(
            name=tmpName, description="description for %s" % tmpName,
            target_type=targetType,
            zone=self.localZone,
            state=0)

        jobXmlTmpl  = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/22"/>
  <descriptor id="http://testserver/api/v1/targets/%(targetId)s/descriptors/configuration"/>
  <descriptor_data>
    <alias>%(targetAlias)s</alias>
    <description>%(targetDescription)s</description>
    <name>%(targetName)s</name>
    <zone>Local rBuilder</zone>
  </descriptor_data>
</job>
"""
        # Try to reconfigure target using the same config as target1
        # We should catch the duplicate
        jobXml = jobXmlTmpl % dict(targetId=target.target_id,
            targetName=tmpName, targetDescription=tmpName, targetAlias=tmpName)

        response = self._post('targets/%s/jobs' % target1.target_id, jobXml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)

        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/targets/%d/descriptors/configuration" % target.target_id)

        dbjob = jmodels.Job.objects.get(job_uuid=unicode(job.job_uuid))

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
        # Grab token
        jobToken = dbjob.job_token
        jobUrl = "jobs/%s" % dbjob.job_uuid
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)

        response = self._get(jobUrl)
        self.assertEquals(response.status_code, 200)

        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.job_state, 'Failed')
        self.failUnlessEqual(job.status_code, '409')
        self.failUnlessEqual(job.status_text, 'Duplicate Target')

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
            username=self.developer_user.user_name, password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/targets/%s/descriptors/configure_credentials" %  target.target_id)

        dbjob = jmodels.Job.objects.get(job_uuid=unicode(job.job_uuid))
        # Make sure the job is related to the target type
        self.failUnlessEqual(
            [ x.target.name for x in dbjob.target_jobs.all() ],
            [ target.name ],
        )

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            ['targets.configure', 'targets.checkCredentials'])
        realCall = calls[-1]
        self.failUnlessEqual(realCall.args, ())
        self.failUnlessEqual(realCall.kwargs, dict(uuid=job.job_uuid))
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
        self.failUnlessEqual(job.results.target.id, "http://testserver/api/v1/targets/1")

    def testGetTargetConfiguration_ec2(self):
        config = dict([
            ('name', 'aws'),
            ('alias', 'ec2'),
            ('description', 'Amazon Elastic Compute Cloud'),
            ('accountId', '12345'),
            ('region', 'us-east-1'),
            ('publicAccessKeyId', 'public-access-key-id'),
            ('secretAccessKey', 'secret-access-key'),
            ('certificateData', """-----BEGIN CERTIFICATE-----
MIICeDCCAeGgAwIBAgIFberMQ1MwDQYJKoZIhvcNAQEFBQAwUzEhMB8GA1UEAxMYQVdTIExpbWl0
ZWQtQXNzdXJhbmNlIENBMQwwCgYDVQQLEwNBV1MxEzARBgNVBAoTCkFtYXpvbi5jb20xCzAJBgNV
BAYTAlVTMB4XDTA3MDcxMTEwNDcwMFoXDTA3MTAwOTEwNDcwMFowUjEVMBMGA1UEAxMMZDV1bjgy
bWxvM24zMRcwFQYDVQQLEw5BV1MtRGV2ZWxvcGVyczETMBEGA1UEChMKQW1hem9uLmNvbTELMAkG
A1UEBhMCVVMwgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAK8Dw8TXGkru2qTVRt3QPSW44/Qp
FKM4KWgtvzwlP+cnLmbuBJOl0eJKzLLC6C+S2ov4UykwXMPS9Yh7Gc1tP6+TKoHr72bhC4+/DKdw
ld2GYQofaZVxCaSULnkf1PZOizqOUixEvdfEuwLQmpbJ9Ow9nGWku5mt1cNvdhz9vhOvAgMBAAGj
WTBXMB8GA1UdIwQYMBaAFIY/Pp+MM/3BlYGZZk0oQNyotqOWMA4GA1UdDwEB/wQEAwIFoDAWBgNV
HSUBAf8EDDAKBggrBgEFBQcDAjAMBgNVHRMBAf8EAjAAMA0GCSqGSIb3DQEBBQUAA4GBALWp0pas
LeZxgGykmvzd5JzHt1KYSjIzwOUK3QqfMg/YJZRq2VqCFypJWt9E7W1yoctfC2Y2yZTbWoH5XWVI
e1s0OFJAVc0RWZY0wL/jjPpm2Adi+0Q9iwiG+HntH+u/nbrnZLdd+KbNNIDKftwvhQvPhYziAUUQ
9rIXl9/1m5sz
-----END CERTIFICATE----- """),
            ('certificateKeyData', """-----BEGIN PRIVATE KEY-----
MIICdQIBADANBgkqhkiG9w0BAQEFAASCAl8wggJbAgEAAoGBAK8Dw8TXGkru2qTVRt3QPSW44/Qp
FKM4KWgtvzwlP+cnLmbuBJOl0eJKzLLC6C+S2ov4UykwXMPS9Yh7Gc1tP6+TKoHr72bhC4+/DKdw
ld2GYQofaZVxCaSULnkf1PZOizqOUixEvdfEuwLQmpbJ9Ow9nGWku5mt1cNvdhz9vhOvAgMBAAEC
gYANQkbBkd4/EQtlc3bz9QO86N30MGyM1QNmDhkv0E6gD3rXd27HVMeq0inh3RxEBmciNYTvWOee
Okw5s8HHq2Aop88Lqtm6F/gpS1EHtUp9+56OErjYDJ91kxv/oZahXWwqpYwIBNwgg1k2bKTlWZPU
DXUelAnjH+gmG+uz2XTgCQJBAOlZ8NuUzquvxs6UfGq7AYCQHcXAgdUYXDwExmeo6uSraVdD+pw1
o/9GNJozAoIF81t4qyTt+FM197rCSqt3dFUCQQDAAFbOLk598XPkBsjIYku/3yt/gqztYe7bWxtb
m1DCooH7Dhz87gQNjXaeLiQCKZCCYc5Xj8zhzYeJ6qSG7wvzAkBvjNhQD83QUwIFxQPI/caVD8+7
tfAazz9gTaQO77gCQlLkLZIC1L2mDYid4h6jy3ZvVrrxt3TLSnQ3aiPJ3hvVAkAlsKtZpAtye7B1
RcOqWmlmS+fdCwjpPH1IADV5oR6UZpQ/dUDJgeu3wVpUqNgWuJQOlCaOV8MvXEpMD4ymlExzAkAs
ttl+RgIbVKA6m16gWvEsagKe2bD/BjVFz/cwSjpMBb4xuzqxSyK8g3A6W5Eqvl4f4pyy7G0a1Kr2
ZcY7o9aU
-----END PRIVATE KEY----- """),
            ('s3Bucket', 'my-bucket'),
            ('zone', 'Local rBuilder'),
        ])

        jobType = jmodels.EventType.objects.get(name=jmodels.EventType.TARGET_CONFIGURE)
        target = models.Target.objects.get(name='Target Name ec2')
        jobXml = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/targets/%(targetId)s/descriptors/configuration"/>
  <descriptor_data>
    %(descriptorData)s
  </descriptor_data>
</job>
"""
        descriptorData = '    \n'.join(
            "<%s>%s</%s>" % (x, y, x) for (x, y) in config.items())
        params = dict(targetId=target.target_id, jobTypeId=jobType.job_type_id,
            descriptorData=descriptorData)
        response = self._post('targets/%s/jobs' % target.target_id,
            jobXml % params,
            username=self.admin_user.user_name, password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/targets/%s/descriptors/configuration" %  target.target_id)

        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/targets/%s/descriptors/configuration" %  target.target_id)

        dbjob = jmodels.Job.objects.get(job_uuid=unicode(job.job_uuid))
        # Make sure the job is related to the target type
        self.failUnlessEqual(
            [ x.target.name for x in dbjob.target_jobs.all() ],
            [ target.name ],
        )

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            ['targets.configure', 'targets.checkCreate'])
        realCall = calls[-1]
        self.failUnlessEqual(realCall.args, ())
        self.failUnlessEqual(realCall.kwargs, dict(uuid=job.job_uuid))
        self.mgr.repeaterMgr.repeaterClient.reset()

        # Grab token
        jobToken = dbjob.job_token
        jobUrl = "jobs/%s" % dbjob.job_uuid

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
        self.failUnlessEqual(job.results.target.id,
            "http://testserver/api/v1/targets/%s" % target.target_id)

        # Check credentials
        tdata = models.TargetData.objects.filter(target__target_id=target.target_id)

        tdata = dict((x.name, x.value) for x in tdata)
        self.failUnlessEqual(json.loads(tdata['ec2AccountId']),
            config['accountId'])
        self.failUnlessEqual(json.loads(tdata['ec2PublicKey']),
            config['publicAccessKeyId'])
        self.failUnlessEqual(json.loads(tdata['ec2PrivateKey']),
            config['secretAccessKey'])

        # Now use the API to fetch the config
        response = self._get('targets/%s/target_configuration/' % target.target_id,
            username=self.admin_user.user_name, password='password')
        self.failUnlessEqual(response.status_code, 200)
        obj = xobj.parse(response.content)
        tconf = obj.target_configuration
        tconfMap = dict((x, getattr(tconf, x).strip()) for x in tconf._xobj.elements)
        self.failUnlessEqual(tconfMap,
            dict((x, unicode(y.strip())) for (x, y) in config.items()))

    def testSetTargetUserCredentials(self):
        user = self.getUser('ExampleDeveloper')
        self.mgr.user = user

        img = self.addImage(name="test 1",
            imageType=buildtypes.VMWARE_ESX_IMAGE)

        # No deployable image yet
        self.failUnlessEqual(
            [ x.build_file_id for x in models.TargetDeployableImage.objects.all() ],
            [])

        target = models.Target.objects.get(pk=1)
        creds0 = dict(username="bubba", password="shrimp")
        creds1 = dict(username="forrest", password="jennay")
        tmgr = self.mgr.targetsManager
        tucreds = tmgr.setTargetUserCredentials(target, creds0)
        creds = sorted(models.TargetUserCredentials.objects.filter(
            user__user_id=self.developer_user.user_id, target=target).values_list('id', flat=True))
        self.failUnlessEqual(creds, [tucreds.id])
        # Do it again, the credentials should be the same
        tucreds2 = tmgr.setTargetUserCredentials(target, creds0)
        self.failUnlessEqual(tucreds.id, tucreds2.id)

        bf = img.files.all()[0]

        # Make sure we've recomputed deployable images
        self.failUnlessEqual(
            [ x.build_file_id for x in models.TargetDeployableImage.objects.all() ],
            [ bf.file_id, bf.file_id, ])

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
        resp = self._get(url, username="ExampleDeveloper", password="password")
        self.failUnlessEqual(resp.status_code, 200)
        doc = xobj.parse(resp.content)
        self.failUnlessEqual(doc.target_user_credentials.user.id,
            "http://testserver/api/v1/users/%s" % self.developer_user.user_id)
        self.failUnlessEqual(doc.target_user_credentials.credentials.username,
            "forrest")

        # Reset user credentials
        resp = self._delete(url, username="ExampleDeveloper", password="password")
        doc = xobj.parse(resp.content)
        self.failUnlessEqual(doc.target_user_credentials.user.id,
            "http://testserver/api/v1/users/%s" % self.developer_user.user_id)
        self.failUnlessEqual(resp.status_code, 200)

        # Gone, baby, gone
        resp = self._get(url, username="ExampleDeveloper", password="password")
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
            username='ExampleDeveloper', password='password')

        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/targets/%s/descriptors/refresh_images" %  target.target_id)

        dbjob = jmodels.Job.objects.get(job_uuid=unicode(job.job_uuid))
        # Make sure the job is related to the target type
        self.failUnlessEqual(
            [ x.target.name for x in dbjob.target_jobs.all() ],
            [ target.name ],
        )

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            ['targets.configure', 'targets.listImages'])
        realCall = calls[-1]
        self.failUnlessEqual(realCall.args, ())
        self.failUnlessEqual(realCall.kwargs, dict(uuid=job.job_uuid))
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
            target_user_credentials__user__user_name='ExampleDeveloper')[0]
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
            username='ExampleDeveloper', password='password')

        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/targets/%s/descriptors/refresh_systems" %  target.target_id)

        dbjob = jmodels.Job.objects.get(job_uuid=unicode(job.job_uuid))
        # Make sure the job is related to the target type
        self.failUnlessEqual(
            [ x.target.name for x in dbjob.target_jobs.all() ],
            [ target.name ],
        )

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            ['targets.configure', 'targets.listInstances'])
        realCall = calls[-1]
        self.failUnlessEqual(realCall.args, ())
        self.failUnlessEqual(realCall.kwargs, dict(uuid=job.job_uuid))
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
        <credentials>
          <opaqueCredentialsId>1</opaqueCredentialsId>
          <opaqueCredentialsId>2</opaqueCredentialsId>
          <opaqueCredentialsId>3</opaqueCredentialsId>
        </credentials>
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
        <credentials>
          <opaqueCredentialsId>1</opaqueCredentialsId>
          <opaqueCredentialsId>2</opaqueCredentialsId>
          <opaqueCredentialsId>3</opaqueCredentialsId>
        </credentials>
      </instance>
      <instance id="id2">
        <instanceId>id2</instanceId>
        <instanceName>name for id2</instanceName>
        <instanceDescription>long name for id2</instanceDescription>
        <launchTime>1234567890</launchTime>
        <state>suspended</state>
        <credentials>
          <opaqueCredentialsId>1</opaqueCredentialsId>
          <opaqueCredentialsId>2</opaqueCredentialsId>
          <opaqueCredentialsId>3</opaqueCredentialsId>
        </credentials>
      </instance>
      <instance id="id3">
        <instanceId>id3</instanceId>
        <instanceName>name for id3</instanceName>
        <instanceDescription>long name for id3</instanceDescription>
        <launchTime>1234567891</launchTime>
        <state>blabbering</state>
        <credentials>
          <opaqueCredentialsId>1</opaqueCredentialsId>
          <opaqueCredentialsId>2</opaqueCredentialsId>
          <opaqueCredentialsId>3</opaqueCredentialsId>
        </credentials>
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
        <credentials>
          <opaqueCredentialsId>1</opaqueCredentialsId>
          <opaqueCredentialsId>2</opaqueCredentialsId>
          <opaqueCredentialsId>3</opaqueCredentialsId>
        </credentials>
      </instance>
      <instance id="id3">
        <instanceId>id3</instanceId>
        <instanceName>name for id3</instanceName>
        <instanceDescription>long name for id3</instanceDescription>
        <launchTime>1234567891</launchTime>
        <state>blabbering</state>
        <credentials>
          <opaqueCredentialsId>1</opaqueCredentialsId>
          <opaqueCredentialsId>2</opaqueCredentialsId>
          <opaqueCredentialsId>3</opaqueCredentialsId>
        </credentials>
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
            target_user_credentials__user__user_name='ExampleDeveloper')[0]
        systems = models.TargetSystem.objects.filter(
            target_system_credentials__target_credentials=creds).order_by(
                    'target_system_id')
        self.failUnlessEqual([ x.name for x in systems ],
            ['name for id2', 'name for id3', ])

    def testUpdateTargetSystems(self):
        invmodels.System.objects.all().delete()
        models.TargetSystem.objects.all().delete()

        # Add a system, and set its target ssytem id

        targetType = models.TargetType.objects.get(name='vmware')
        target = models.Target.objects.filter(target_type=targetType)[0]
        system = self._saveSystem()
        system.target = target
        system.target_system_id = str(self.uuid4())
        system.save()

        # Quick test for an internal function
        creds = self.mgr.getTargetAllUserCredentials(target)
        self.failUnlessEqual(creds, [
            (1, {u'username': 'username-0', u'password': 'password-0'}),
            (2, {u'username': 'username-1', u'password': 'password-1'}),
        ])

        instanceStanza = """\
<instance id="instances/%(instanceId)s">
  <dnsName>%(dnsName)s</dnsName>
  <instanceDescription>%(instanceDescription)s</instanceDescription>
  <instanceId>%(instanceId)s</instanceId>
  <instanceName>%(instanceName)s</instanceName>
  <launchTime>%(launchTime)s</launchTime>
  <publicDnsName>%(publicDnsName)s</publicDnsName>
  <state>%(state)s</state>
  <credentials>
    <opaqueCredentialsId>1</opaqueCredentialsId>
    <opaqueCredentialsId>2</opaqueCredentialsId>
    <opaqueCredentialsId>3</opaqueCredentialsId>
  </credentials>
</instance>"""

        data = [
            # New system
            dict(dnsName="10.1.1.1",
                instanceName="target instance name 1",
                instanceDescription="target instance description 1",
                instanceId=str(self.uuid4()),
                launchTime=1234567890.123,
                publicDnsName="dhcp001.example.com",
                state="poweredOn",
            ),
            # Existing system
            dict(dnsName="10.1.1.2",
                instanceName="target instance name 2",
                instanceDescription="target instance description 2",
                instanceId=system.target_system_id,
                # Force null launch time
                launchTime='',
                publicDnsName="dhcp002.example.com",
                state="poweredOn",
            ),
        ]
        systemModels = []
        for sdata in data:
            xmodel = etree.fromstring(instanceStanza % sdata)
            systemModels.append(xmodel)
        self.mgr.updateTargetSystems(target, systemModels)

        systems = invmodels.System.objects.order_by('-system_id')
        self.failUnlessEqual([ x.target_system_id for x in systems ],
            [ x['instanceId'] for x in data ])
        self.failUnlessEqual([ x.target_system_name for x in systems ],
            [ x['instanceName'] for x in data ])

        tsystems = models.TargetSystem.objects.order_by('name')
        self.failUnlessEqual([ x.created_date.year for x in tsystems ],
            [2009, timeutils.now().year])

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
        # Add target user credentials for the current user
        self.mgr.setTargetUserCredentials(target, targetCredentials)

        response = self._get('inventory/systems/%s/descriptors/capture' % 1999,
            username=self.developer_user.user_name, password='password')
        self.assertEquals(response.status_code, 404)
        response = self._get('inventory/systems/%s/descriptors/capture' % system.system_id,
            username=self.developer_user.user_name, password='password')
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
            username=self.developer_user.user_name, password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/inventory/systems/%s/descriptors/capture"
                % systemId)

        dbjob = jmodels.Job.objects.get(job_uuid=unicode(job.job_uuid))
        jobToken = dbjob.job_token
        self.failUnlessEqual(dbjob.job_type.name, dbjob.job_type.SYSTEM_CAPTURE)
        self.failUnlessEqual(
            [ x.system.name for x in dbjob.systems.all() ],
            [ 'testsystemname' ],
        )

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            [
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
            'imageFilesCommitUrl': u'https://bubba.com/api/v1/images/1/build_files',
        }
        from ..images import models as imgmodels
        imgdata = imgmodels.ImageData.objects.filter(name='outputToken')[0]
        outputToken = imgdata.value
        img = imgdata.image

        params['outputToken'] = outputToken
        # XXX get around stipid siteHost being mocked by who knows whom
        self.failUnlessEqual(realCall.args[0], system.target_system_id)
        mungedParams = self._mungeDict(realCall.args[1])
        self.failUnlessEqual(mungedParams, params)
        self.failUnlessEqual(realCall.kwargs, dict(uuid=job.job_uuid))
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
        self.failUnlessEqual(obj.job.results.image.id, "http://testserver/api/v1/images/1")

        # Refresh image
        img = imgmodels.Image.objects.get(image_id=img.image_id)
        self.failUnlessEqual(img.status, 300)
        self.failUnlessEqual(img.status_message, 'System captured')

        response = self._get("images/1",
            username=self.developer_user.user_name, password='password')
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

    def _setupImages(self, withEc2=False):
        targetType = models.TargetType.objects.get(name='vmware')
        target1 = models.Target.objects.filter(target_type=targetType)[0]
        targetType = models.TargetType.objects.get(name='openstack')
        target2 = models.Target.objects.filter(target_type=targetType)[0]
        targetType = models.TargetType.objects.get(name='vcloud')
        target3 = models.Target.objects.filter(target_type=targetType)[0]

        targetType = models.TargetType.objects.get(name='ec2')
        targetEc2 = models.Target.objects.filter(target_type=targetType)[0]

        targetData = [
            (target1, buildtypes.VMWARE_ESX_IMAGE, [ 'ova', 'tar.gz', ]),
            (target2, buildtypes.RAW_HD_IMAGE, [ 'tar.gz' ]),
        ]

        if withEc2:
            targetData.append((targetEc2, buildtypes.AMI, [ '.tar.gz', ]))

        # We need to set a user, image creation needs it
        user = self.getUser('ExampleDeveloper')
        self.mgr.user = user

        # Create a project for the images
        branch = self.getProjectBranch(label='chater-foo.eng.rpath.com@rpath:chater-foo-1')
        stage = self.getProjectBranchStage(branch=branch, name="Development")

        targetImageIdTempl = "target-internal-id-%02d"
        imgmgr = self.mgr.imagesManager
        trvFlavor = '1#x86:i486:i586:i686|5#use:~!xen'
        for i in range(5):
            for target, imageType, fileExtensions in targetData:
                trvVer = '/example.com@rpath:foo-%d-1-devel/123.4:1-%d-1' % (
                    i, i)
                image = imgmgr.createImage(
                    _image_type=imageType,
                    name = "image %02d" % i,
                    description = "image %02d description" % i,
                    project_branch_stage=stage,
                    trove_name='group-foo-%d-appliance' % i,
                    trove_version=trvVer,
                    trove_flavor=trvFlavor,
                )

                j = i + 2
                targetInternalImageId = targetImageIdTempl % j
                buildData = []

                imgmgr.createImageBuild(image, buildData=buildData)
                for fileExtension in fileExtensions:
                    if i == 4 and fileExtension == 'ova':
                        # Skip this one, to force an ovf 0.9 only image
                        continue
                    fileName = "filename-%02d-%02d.%s" % (imageType, i, fileExtension)
                    bf = imgmgr.createImageBuildFile(image,
                        url=fileName,
                        title="Image File Title %02d" % i,
                        size=100+i,
                        sha1="%040d" % i)
                    if i % 2 == 0:
                        imgbuild = imgmgr.recordTargetInternalId(
                            buildFile=bf, target=target,
                            targetInternalId=targetImageIdTempl % i)

                # Add a bunch of target images
                models.TargetImage.objects.create(
                    target = target,
                    name="target image name %02d" % j,
                    description="target image description %02d" % j,
                    target_internal_id=targetInternalImageId)

                # Create deferred images too
                self.createDeferredImage(image,
                    "Deferred image based on %s" % image.image_id,
                    projectBranchStage=stage)

        self._markAllImagesAsFinished()
        ret = [ target1, target2, target3 ]
        if withEc2:
            ret.append(targetEc2)
        return ret

    def createDeferredImage(self, baseImage, name, description=None,
            projectBranchStage=None):
        # Deferred images have no build files
        img = self.addImage(name=name, description=description,
            imageType=buildtypes.DEFERRED_IMAGE,
            stage=projectBranchStage, baseImage=baseImage,
            files=[])
        self._retagQuerySets()
        return img

    def testRecomputeTargetDeployableImages(self):
        targets = self._setupImages()
        self.mgr.targetsManager.recomputeTargetDeployableImages()

        target1 = targets[0]
        target3 = targets[2]
        targetX = models.Target.objects.get(name='Target without credentials')

        # Helper function, targetImage may be null
        def _g(targetImage):
            if targetImage is None:
                return None
            return targetImage.target_internal_id

        for imgName in [ "image 00", "image 01", "image 03" ]:
            img = imgmodels.Image.objects.get(name=imgName, _image_type=buildtypes.VMWARE_ESX_IMAGE)
            self.failUnlessEqual(
                [
                    [ tdi.target_image
                        for tdi in imgfile.target_deployable_images.all() ]
                    for imgfile in img.files.order_by('file_id') ],
                [[None, None, None], []]
            )

        imgName = "image 04"
        img = imgmodels.Image.objects.get(name=imgName, _image_type=buildtypes.VMWARE_ESX_IMAGE)
        self.failUnlessEqual(
            [
                [ (tdi.target.name, _g(tdi.target_image))
                    for tdi in imgfile.target_deployable_images.all() ]
                for imgfile in img.files.order_by('file_id') ],
            [[
                (targetX.name, None),
                ('Target Name vmware', 'target-internal-id-04'),
            ]]
        )

        imgName = "image 02"
        img = imgmodels.Image.objects.get(name=imgName, _image_type=buildtypes.VMWARE_ESX_IMAGE)
        imgfiles = img.files.order_by('file_id')

        self.failUnlessEqual(
                [
                    [ (tdi.target.name, _g(tdi.target_image))
                        for tdi in imgfile.target_deployable_images.order_by('target__target_id') ]
                    for imgfile in imgfiles ],
                [
                    [
                        ('Target Name vmware', 'target-internal-id-02'),
                        ('Target Name vcloud', None),
                        (targetX.name, None),
                    ],
                    []
                ])

        url = "images/%s" % img.image_id
        self._retagQuerySets()
        resp = self._get(url, username="ExampleDeveloper", password="password")
        self.failUnlessEqual(resp.status_code, 200)
        doc = xobj.parse(resp.content)
        actions = doc.image.actions.action
        self.failUnlessEqual([ x.name for x in actions ],
            ["Deploy image on 'Target Name vmware' (vmware)",
             "Deploy image on 'Target Name vcloud' (vcloud)",
             "Deploy image on '%s' (vmware)" % targetX.name,
             "Launch system on 'Target Name vmware' (vmware)",
             "Launch system on 'Target Name vcloud' (vcloud)",
             "Launch system on '%s' (vmware)" % targetX.name,
             "Cancel image build",
            ])
        self.failUnlessEqual([ x.enabled for x in actions ],
            ['true', 'false', 'false', 'true', 'false', 'false', 'false'])

        file1 = img.files.all()[0]
        self.failUnlessEqual([ x.descriptor.id for x in actions ],
            [
            'http://testserver/api/v1/targets/%s/descriptors/deploy/file/%s' %
                (target1.target_id, file1.file_id),
            'http://testserver/api/v1/targets/%s/descriptors/deploy/file/%s' %
                (target3.target_id, file1.file_id),
            'http://testserver/api/v1/targets/%s/descriptors/deploy/file/%s' %
                (targetX.target_id, file1.file_id),
            'http://testserver/api/v1/targets/%s/descriptors/launch/file/%s' %
                (target1.target_id, file1.file_id),
            'http://testserver/api/v1/targets/%s/descriptors/launch/file/%s' %
                (target3.target_id, file1.file_id),
            'http://testserver/api/v1/targets/%s/descriptors/launch/file/%s' %
                (targetX.target_id, file1.file_id),
            'http://testserver/api/v1/images/%s/descriptors/cancel_build' %
                (img.image_id, ),
            ])
        self.failUnlessEqual([ x.resources.target.id for x in actions[:-1] ],
            [
            'http://testserver/api/v1/targets/%s' %
                (target1.target_id, ),
            'http://testserver/api/v1/targets/%s' %
                (target3.target_id, ),
            'http://testserver/api/v1/targets/%s' %
                (targetX.target_id, ),
            'http://testserver/api/v1/targets/%s' %
                (target1.target_id, ),
            'http://testserver/api/v1/targets/%s' %
                (target3.target_id, ),
            'http://testserver/api/v1/targets/%s' %
                (targetX.target_id, ),
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
        resp = self._get(url, username="ExampleDeveloper", password="password")
        self.failUnlessEqual(resp.status_code, 200)
        doc = xobj.parse(resp.content)
        self.failUnlessEqual(doc.descriptor.metadata.displayName, "FooDescriptor")
        self.failUnlessEqual(doc.descriptor.metadata.rootElement, "descriptor_data")
        self.failUnlessEqual(doc.descriptor.dataFields.field.default, "7")

        baseImg = img

        # Check deferred image
        imgName = "image 02"
        img = imgmodels.Image.objects.get(
            name="Deferred image based on %s" % baseImg.image_id,
            _image_type=buildtypes.DEFERRED_IMAGE)

        url = "images/%s" % img.image_id
        resp = self._get(url, username="ExampleDeveloper", password="password")
        self.failUnlessEqual(resp.status_code, 200)
        doc = xobj.parse(resp.content)
        actions = doc.image.actions.action
        self.failUnlessEqual([ x.name for x in actions ],
            [
             "Deploy image on 'Target Name vmware' (vmware)",
             "Deploy image on 'Target Name vcloud' (vcloud)",
             "Deploy image on '%s' (vmware)" % targetX.name,
             "Launch system on 'Target Name vmware' (vmware)",
             "Launch system on 'Target Name vcloud' (vcloud)",
             "Launch system on '%s' (vmware)" % targetX.name,
             "Cancel image build",
            ])
        # We should be referring to the base image's files
        file1 = baseImg.files.all()[0]
        self.failUnlessEqual([ x.descriptor.id for x in actions ],
            [
            'http://testserver/api/v1/targets/%s/descriptors/deploy/file/%s' %
                (target1.target_id, file1.file_id),
            'http://testserver/api/v1/targets/%s/descriptors/deploy/file/%s' %
                (target3.target_id, file1.file_id),
            'http://testserver/api/v1/targets/%s/descriptors/deploy/file/%s' %
                (targetX.target_id, file1.file_id),
            'http://testserver/api/v1/targets/%s/descriptors/launch/file/%s' %
                (target1.target_id, file1.file_id),
            'http://testserver/api/v1/targets/%s/descriptors/launch/file/%s' %
                (target3.target_id, file1.file_id),
            'http://testserver/api/v1/targets/%s/descriptors/launch/file/%s' %
                (targetX.target_id, file1.file_id),
            'http://testserver/api/v1/images/%s/descriptors/cancel_build' %
                (img.image_id, ),
            ])
        self.failUnlessEqual(doc.image.jobs.id,
            'http://testserver/api/v1/images/%s/jobs' % img.image_id)

    def testRecomputeTargetDeployableImagesEC2(self):
        targets = self._setupImages(withEc2=True)
        self.mgr.targetsManager.recomputeTargetDeployableImages()

        targetEC2 = targets[-1]
        self.failUnlessEqual(targetEC2.target_type.name, 'ec2')

        for imgName in [ "image 00", "image 01", "image 03", ]:
            img = imgmodels.Image.objects.get(name=imgName, _image_type=buildtypes.AMI)
            self.failUnlessEqual(
                [
                    [ tdi.target_image
                        for tdi in imgfile.target_deployable_images.all() ]
                    for imgfile in img.files.order_by('file_id') ],
                [[None]]
            )

        missing = object()
        def _getTargetInternalId(tgtimg):
            if tgtimg is None:
                return missing
            return tgtimg.target_internal_id

        for imgName in [ "image 02", "image 04" ]:
            img = imgmodels.Image.objects.get(name=imgName, _image_type=buildtypes.AMI)
            self.failUnlessEqual(
                [
                    sorted(_getTargetInternalId(tdi.target_image)
                        for tdi in imgfile.target_deployable_images.all())
                    for imgfile in img.files.order_by('file_id') ],
                [[missing, "target-internal-id-%s" % imgName[-2:], ]]
            )


    def testDeployImage(self):
        targets = self._setupImages()
        imgName = "image 02"
        img = imgmodels.Image.objects.get(name=imgName, _image_type=buildtypes.VMWARE_ESX_IMAGE)
        imgmodels.ImageData.objects.create(image=img,
                name='filesystemSize', value='3141',
                data_type=mintdata.RDT_INT)
        self._testDeployImage(targets, img)

    def testDeployDeferredImage(self):
        targets = self._setupImages()
        imgName = "image 02"
        img = imgmodels.Image.objects.get(name=imgName, _image_type=buildtypes.VMWARE_ESX_IMAGE)
        imgmodels.ImageData.objects.create(image=img,
                name='filesystemSize', value='3141',
                data_type=mintdata.RDT_INT)
        deferredImg = imgmodels.Image.objects.get(base_image=img)
        self._testDeployImage(targets, deferredImg, img)

    def _testDeployImage(self, targets, img, baseImg=None):
        self.mgr.targetsManager.recomputeTargetDeployableImages()

        # Post a job
        jobXmlTmpl = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/targets/%(targetId)s/descriptors/deploy/file/%(buildFileId)s"/>
  <descriptor_data><imageId>%(buildFileId)s</imageId></descriptor_data>
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
        self._retagQuerySets()
        response = self._post(jobUrl, jobXml,
            username='ExampleDeveloper', password='password')
        self.failUnlessEqual(response.status_code, 200)
        obj = xobj.parse(response.content)

        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/targets/%s/descriptors/deploy/file/%s"
                % (targetId, buildFileId))

        dbjob = jmodels.Job.objects.get(job_uuid=unicode(job.job_uuid))
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
                'targets.configure', 'targets.deployImage',
            ])
        realCall = calls[-1]
        self.failUnlessEqual(self._mungeDict(realCall.args[0]),
          {
            'imageFileInfo': {
                'architecture' : 'x86',
                'fileId' : buildFileId,
                'name' : u'filename-09-02.ova',
                'sha1' : u'0000000000000000000000000000000000000002',
                'size' : 102,
                'baseFileName' : 'chater-foo-1-x86',
            },
            'descriptorData': "<?xml version='1.0' encoding='UTF-8'?>\n<descriptor_data><imageId>%s</imageId></descriptor_data>" % buildFileId,
            'imageDownloadUrl': 'https://bubba.com/downloadImage?fileId=%s' % buildFileId,
            'imageFileUpdateUrl': 'http://localhost/api/v1/images/%s/build_files/%s' % (baseImg.image_id, buildFileId),
            'targetImageXmlTemplate': '<file>\n  <target_images>\n    <target_image>\n      <target id="/api/v1/targets/1"/>\n      %(image)s\n    </target_image>\n  </target_images>\n</file>',
            'targetImageIdList': ['target-internal-id-02'],
            'imageData' : { 'filesystemSize' : 3141 },
          })
        self.failUnlessEqual(realCall.args[1:], ())
        self.failUnlessEqual(realCall.kwargs, dict(uuid=job.job_uuid))

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
        self.assertXMLEquals(response.content,
            testsxml.job_xml_with_artifacts % dict(jobUuid=job.job_uuid))

    def testLaunchSystem(self):
        targets = self._setupImages()
        imgName = "image 02"
        img = imgmodels.Image.objects.get(name=imgName, _image_type=buildtypes.VMWARE_ESX_IMAGE)
        self._testLaunchSystem(targets, img)

    def testLaunchSystemFromDeferredImage(self):
        targets = self._setupImages()
        imgName = "image 02"
        img = imgmodels.Image.objects.get(name=imgName, _image_type=buildtypes.VMWARE_ESX_IMAGE)
        deferredImg = imgmodels.Image.objects.get(base_image=img)
        self._testLaunchSystem(targets, deferredImg, img)


    def _testLaunchSystem(self, targets, img, baseImg=None, configData=None,
            expectedStatusCode=200):
        self.mgr.targetsManager.recomputeTargetDeployableImages()

        # Post a job
        jobXmlTmpl = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/targets/%(targetId)s/descriptors/launch/file/%(buildFileId)s"/>
  %(descriptorData)s
</job>
"""
        if baseImg is None:
            baseImg = img

        buildFileId = baseImg.files.all()[0].file_id
        imageId = img.image_id
        targetId = targets[0].target_id
        jobTypeId = self.mgr.sysMgr.eventType(jmodels.EventType.TARGET_LAUNCH_SYSTEM).job_type_id

        if configData:
            configDataXml = ('<system_configuration>%s</system_configuration>' %
                ''.join("<%s>%s</%s>" % (k, v, k)
                    for k, v in configData.items()))
            edata = '<withConfiguration>true</withConfiguration>' + configDataXml
        else:
            configDataXml = None
            edata = ''
        descriptorData = "<descriptor_data><imageId>%s</imageId>%s</descriptor_data>" % (buildFileId, edata)

        jobXml = jobXmlTmpl % dict(
                jobTypeId=jobTypeId,
                targetId=targetId,
                buildFileId = buildFileId,
                descriptorData=descriptorData)
        self._retagQuerySets()
        jobUrl = "images/%s/jobs" % imageId
        response = self._post(jobUrl, jobXml,
            username='ExampleDeveloper', password='password')
        self.failUnlessEqual(response.status_code, expectedStatusCode)
        if expectedStatusCode != 200:
            return response
        obj = xobj.parse(response.content)

        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/targets/%s/descriptors/launch/file/%s"
                % (targetId, buildFileId))

        dbjob = jmodels.Job.objects.get(job_uuid=unicode(job.job_uuid))
        jobToken = dbjob.job_token
        self.failUnlessEqual(dbjob.job_type.name, dbjob.job_type.TARGET_LAUNCH_SYSTEM)
        # The revolving job only links to the current image, unlike
        # deployment which links to both the base and the deferred image
        imageNames = [ img.name ]
        self.failUnlessEqual(
            [ x.image.name for x in dbjob.images.all() ],
            imageNames)

        calls = self.mgr.repeaterMgr.repeaterClient.getCallList()
        self.failUnlessEqual([ x.name for x in calls ],
            [
                'targets.configure', 'targets.launchSystem',
            ])
        realCall = calls[-1]
        descriptorData = etree.tostring(etree.fromstring(descriptorData),
            pretty_print=False, xml_declaration=True, encoding="UTF-8")
        self.failUnlessEqual(self._mungeDict(realCall.args[0]),
          {
            'imageFileInfo': {
                'architecture' : 'x86',
                'fileId' : buildFileId,
                'name' : u'filename-09-02.ova',
                'sha1' : u'0000000000000000000000000000000000000002',
                'size' : 102,
                'baseFileName' : 'chater-foo-1-x86',
            },
            'descriptorData': descriptorData,
            'imageDownloadUrl': 'https://bubba.com/downloadImage?fileId=%s' % buildFileId,
            'imageFileUpdateUrl': 'http://localhost/api/v1/images/%s/build_files/%s' % (baseImg.image_id, buildFileId),
            'targetImageXmlTemplate': '<file>\n  <target_images>\n    <target_image>\n      <target id="/api/v1/targets/1"/>\n      %(image)s\n    </target_image>\n  </target_images>\n</file>',
            'systemsCreateUrl': 'http://localhost/api/v1/jobs/%s/systems' %
                job.job_uuid,
            'targetImageIdList': ['target-internal-id-02'],
            'imageData' : {},
          })
        self.failUnlessEqual(realCall.args[1:], ())
        self.failUnlessEqual(realCall.kwargs, dict(uuid=job.job_uuid))


        systemsXml = """\
  <systems>
    <system>
      <targetType>xen-enterprise</targetType>
      <target_system_id>0c24c2d8-2fde-11d0-67ab-599b1d93616c</target_system_id>
      <description>misa-foobar-4</description>
      <target_system_state>Running</target_system_state>
      <ssl_client_certificate>foo</ssl_client_certificate>
      <target_system_description>misa-foobar-4</target_system_description>
      <ssl_client_key>foo</ssl_client_key>
      <target_system_name>misa-foobar-4</target_system_name>
      <dnsName>172.16.175.51</dnsName>
      <targetName>Target Name xen-enterprise</targetName>
      <name>misa-foobar-4</name>
    </system>
  </systems>"""

        # POST the system, that should create the artifacts
        url = 'jobs/%s/systems' % (job.job_uuid, )
        response = self._post(url, data=systemsXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)

        artifacts = jmodels.JobSystemArtifact.objects.all()
        self.failUnlessEqual(len(artifacts), 1)
        if configDataXml is None:
            self.assertEquals([j.system.configuration for j in artifacts],
                [configDataXml] * len(artifacts))
        else:
            # Munge config since the launch descriptor calls it
            # system_configuration
            tgt = configDataXml.replace('system_configuration>',
                'configuration>')
            for j in artifacts:
                self.assertXMLEquals(j.system.configuration, tgt)

        jobXml = """<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Some status here</status_text>
  <results encoding="identity">%(systems)s</results>
</job>
""" % dict(systems=systemsXml)

        jobUrl = "jobs/%s" % dbjob.job_uuid
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.failUnlessEqual(response.status_code, 200)

        response = self._get(jobUrl, username='admin', password='password')

        self.assertXMLEquals(response.content,
            testsxml.job_created_system % dict(jobUuid=job.job_uuid))
        return dbjob

    def testGetDescriptorLaunch(self):
        targets = self._setupImages()
        self.mgr.targetsManager.recomputeTargetDeployableImages()

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

        from smartform import descriptor
        def mockGetDescriptor(slf, trvTup):
            return descriptor.SystemConfigurationDescriptor(fromStream="""\
<descriptor>
  <metadata>
    <displayName>FooDescriptor</displayName>
    <rootElement>blah</rootElement>
    <descriptions><desc>Description</desc></descriptions>
  </metadata>
  <dataFields>
    <field>
      <name>blargh</name>
      <descriptions>
        <desc>Blargh</desc>
      </descriptions>
      <type>str</type>
      <required>true</required>
    </field>
  </dataFields>
</descriptor>
""")
        from rpath_tools.client.utils.config_descriptor_cache import ConfigDescriptorCache
        self.mock(ConfigDescriptorCache, 'getDescriptor', mockGetDescriptor)

        # Grab an image
        tgt = [ x for x in targets if x.target_type.name == 'vmware' ][0]
        imgName = "image 02"
        img = imgmodels.Image.objects.get(name=imgName, _image_type=buildtypes.VMWARE_ESX_IMAGE)
        buildFileId = img.files.all()[0].file_id
        response = self._get('targets/%d/descriptors/launch/file/%d' %
            (tgt.target_id, buildFileId),
            username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)

        doc = etree.fromstring(response.content)
        nsmap = dict(dsc='http://www.rpath.com/permanent/descriptor-1.1.xsd')
        fields = doc.xpath('/dsc:descriptor/dsc:dataFields/dsc:field/dsc:name/text()',
            namespaces=nsmap)
        self.assertEquals(fields,
            ['imageId', 'withConfiguration', 'system_configuration'])

        sfields = doc.xpath('/dsc:descriptor/dsc:dataFields/dsc:field'
            '[dsc:name="system_configuration"]/'
            'dsc:descriptor/dsc:dataFields/dsc:field/dsc:name/text()',
            namespaces=nsmap)
        self.assertEquals(sfields, ['blargh'])

        # Now test that we saved the config in the DB
        self.mgr.repeaterMgr.repeaterClient.reset()
        job = self._testLaunchSystem(targets, img,
            configData=dict(blargh='abc123'))
        system = jmodels.JobSystemArtifact.objects.filter(job=job)[0].system
        self.assertXMLEquals(system.configuration,
            "<configuration><blargh>abc123</blargh></configuration>")

        # Test errors
        response = self._testLaunchSystem(targets, img,
            configData=dict(johnny='is not here'), expectedStatusCode=400)
        self.assertXMLEquals(response.content, """\
<fault>
  <code>400</code>
  <message>Data validation error: [u"Missing field: 'blargh'"]</message>
  <traceback></traceback>
</fault>""")


    def testGetDescriptorDeploy(self):
        targets = self._setupImages()
        self.mgr.targetsManager.recomputeTargetDeployableImages()

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

        # Grab an image
        tgt = [ x for x in targets if x.target_type.name == 'vmware' ][0]
        imgName = "image 02"
        img = imgmodels.Image.objects.get(name=imgName, _image_type=buildtypes.VMWARE_ESX_IMAGE)
        buildFileId = img.files.all()[0].file_id
        response = self._get('targets/%d/descriptors/deploy/file/%d' %
            (tgt.target_id, buildFileId),
            username='ExampleDeveloper', password='password')
        self.assertEquals(response.status_code, 200)
