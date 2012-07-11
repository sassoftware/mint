#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from lxml import etree

from mint.django_rest.test_utils import XMLTestCase, RepeaterMixIn

from mint.django_rest.rbuilder.jobs import models
from mint.django_rest.rbuilder.jobs import testsxml

from xobj import xobj

class BaseJobsTest(XMLTestCase):
    def _mock(self):
        pass

    def setUp(self):
        XMLTestCase.setUp(self)
        self._mock()

        eventUuid1 = 'eventuuid001'
        jobUuid1 = 'rmakeuuid001'
        eventUuid2 = 'eventuuid002'
        jobUuid2 = 'rmakeuuid002'
        eventUuid3 = 'eventuuid003'
        jobUuid3 = 'rmakeuuid003'
        system = self._saveSystem()

        user = self.getUser('testuser')
        self.job1 = self._newSystemJob(system, eventUuid1, jobUuid1,
            models.EventType.SYSTEM_REGISTRATION, createdBy=user)
        self.job2 = self._newSystemJob(system, eventUuid2, jobUuid2,
            models.EventType.SYSTEM_UPDATE, createdBy=user)

        self.system = system

class CacheTest(XMLTestCase):
    "Simple test for the caching module"
    def testInvalidateCache(self):
        Cache = models.modellib.Cache
        # Populate the cache
        jt1 = Cache.get(models.EventType, name=models.EventType.SYSTEM_REGISTRATION)
        # Add new job type
        jt2 = models.EventType.objects.create(name='fake',
            description='fakefake', priority=1)
        jt3 = Cache.get(models.EventType, name='fake')
        self.failUnlessEqual(jt2.job_type_id, jt3.job_type_id)

class JobsTestCase(BaseJobsTest):

    def _mock(self):
        models.Job.getRmakeJob = self.mockGetRmakeJob

    def mockGetRmakeJob(self):
        self.mockGetRmakeJob_called = True

    def testGetJobs(self):
        response = self._get('jobs/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.jobs_xml)

    def testGetJobsSortBySyntheticFields(self):
        response = self._get('jobs/?order_by=job_description')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            testsxml.jobs_xml.replace('order_by=""',
                'order_by="job_description"'))

    def testGetJobStates(self):
        response = self._get('job_states/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.job_states_xml)

    def testGetJob(self):
        response = self._get('jobs/rmakeuuid001/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.job_xml)

    def testGetJobState(self):
        response = self._get('job_states/1/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.job_state_xml)

    def testGetSystemJobs(self):
        response = self._get('inventory/systems/%s/jobs/' % \
            self.system.pk, username="admin", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.systems_jobs_xml)

    def testUpdateJob(self):
        jobUuid = 'jobUuid1'
        jobToken = 'jobToken1'
        job = self._newJob(jobUuid, jobToken=jobToken,
            jobType=models.EventType.TARGET_REFRESH_IMAGES)

        jobXml = """
<job>
  <job_status>Completed</job_status>
  <status_code>200</status_code>
  <status_text>Some status here</status_text>
  <results encoding="identity">
    <images>
      <image id="id1">
        <imageId>id1</imageId>
      </image>
      <image id="id2">
        <imageId>id2</imageId>
      </image>
    </images>
  </results>
</job>
"""
        response = self._put('jobs/%s' % jobUuid, jobXml,
            jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        self.failUnlessEqual(obj.job.id, "http://testserver/api/v1/jobs/%s" % job.job_uuid)

class Jobs2TestCase(BaseJobsTest):
    def _mock(self):
        class DummyStatus(object):
            def __init__(slf, **kwargs):
                slf.__dict__.update(kwargs)
        class DummyJob(object):
            def __init__(slf, job_uuid, code, text, detail, final, completed, failed):
                slf.job_uuid = job_uuid
                slf.status = DummyStatus(code=code, text=text, detail=detail,
                    final=final, completed=completed, failed=failed)
        class Dummy(object):
            data = dict(
                rmakeuuid001 = (101, "text 101", "detail 101", False,
                    False, False),
                rmakeuuid002 = (202, "text 202", "detail 202", True,
                    True, False),
                rmakeuuid003 = (404, "text 404", "detail 404", True,
                    False, True),
            )
            @staticmethod
            def mockGetRmakeJob(slf):
                jobUuid = slf.job_uuid
                code, text, detail, final, completed, failed = Dummy.data[jobUuid]
                j = DummyJob(jobUuid, code, text, detail, final, completed, failed)
                return j
        self.mock(models.Job, 'getRmakeJob', Dummy.mockGetRmakeJob)

    def testGetJobs(self):
        # Mark job2 as succeeded, to make sure the status doesn't get updated
        # from the rmake job again (this is a stretch)
        completedState = models.JobState.objects.get(name=models.JobState.COMPLETED)
        self.job2.job_state = completedState
        self.job2.status_code = 299
        self.job2.status_text = "text 299"
        self.job2.status_detail = "no such luck"
        self.job2.save()

        response = self._get('jobs/')
        self.assertEquals(response.status_code, 200)

        obj = xobj.parse(response.content)
        jobs = obj.jobs.job

        self.failUnlessEqual([ str(x.job_state) for x in jobs ],
            [models.JobState.RUNNING, models.JobState.COMPLETED])

        self.failUnlessEqual([ int(x.status_code) for x in jobs ],
            [101, 299])
        self.failUnlessEqual([ x.status_text for x in jobs ],
            ["text 101", "text 299"])

class JobCreationTest(BaseJobsTest, RepeaterMixIn):
    def _mock(self):
        RepeaterMixIn.setUpRepeaterClient(self)
        from mint.django_rest.rbuilder.inventory.manager import repeatermgr
        self.mock(repeatermgr.RepeaterManager, 'repeaterClient',
            self.mgr.repeaterMgr.repeaterClient)

    def testCreateJob(self):
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
        response = self._post('jobs', jobXml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id, "http://testserver/api/v1/target_types/6/descriptor_create_target")

        dbjob = models.Job.objects.get(job_uuid=job.job_uuid)
        # Make sure the job is related to the target type
        self.failUnlessEqual(
            [ x.target_type.name for x in dbjob.jobtargettype_set.all() ],
            [ 'xen-enterprise' ],
        )

    def testCreateJobSystemScan(self):
        jobType = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_SCAN)
        system = self._saveSystem()
        system.save()
        jobXml = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/inventory/systems/%(systemId)s/descriptors/survey_scan"/>
  <descriptor_data>
    <top_level_group>group-foo=/a@b:c/1-2-3</top_level_group>
  </descriptor_data>
</job>
""" % dict(jobTypeId=jobType.job_type_id, systemId=system.system_id)

        response = self._post('jobs', jobXml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/inventory/systems/%s/descriptors/survey_scan" % system.system_id)

        repClient = self.mgr.repeaterMgr.repeaterClient
        cimParams = repClient.CimParams
        resLoc = repClient.ResultsLocation

        callList = repClient.getCallList()

        eventUuids = [ x.args[0].pop('eventUuid') for x in callList ]

        dbjob = models.Job.objects.get(job_uuid=job.job_uuid)
        # Make sure the job is related to the system
        self.failUnlessEqual(
            [ (x.system_id, x.event_uuid) for x in dbjob.systems.all() ],
            [ (system.system_id, eventUuids[0]) ],
        )



        self.failUnlessEqual(callList,
            [
                ('survey_scan_cim',
                    (
                        cimParams(**{'targetType': None, 'instanceId': None, 'targetName': None, 'port': 5989, 'host': u'1.1.1.1', 'launchWaitTime': 1200, 'clientKey': u'testsystemsslclientkey', 'requiredNetwork': None, 'clientCert': u'testsystemsslclientcertificate'}),

                    ),
                    dict(
                        desiredTopLevelItems = [u'group-foo=/a@b:c/1-2-3'],
                        zone=system.managing_zone.name,
                    ),
                ),
            ])

        # same deal with wmi

        system.management_interface = self.mgr.wmiManagementInterface()
        system.save()

        response = self._post('jobs', jobXml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/inventory/systems/%s/descriptors/survey_scan" % system.system_id)

        callList = repClient.getCallList()
        eventUuids = [ x.args[0].pop('eventUuid') for x in callList[1:] ]

        dbjob = models.Job.objects.get(job_uuid=job.job_uuid)

        # Make sure the job is related to the system
        self.failUnlessEqual(
            [ (x.system_id, x.event_uuid) for x in dbjob.systems.all() ],
            [ (system.system_id, eventUuids[0]) ]
        )

        repClient = self.mgr.repeaterMgr.repeaterClient
        cimParams = repClient.CimParams
        resLoc = repClient.ResultsLocation

        # Ignore cim one
        self.failUnlessEqual(len(callList), 2)

        wmiParams = repClient.WmiParams

        self.failUnlessEqual(callList[1:],
            [
                ('survey_scan_wmi',
                    (
                        wmiParams(**{'port': 5989, 'host': u'1.1.1.1', 'requiredNetwork': None,}),

                    ),
                    dict(
                        desiredTopLevelItems = [u'group-foo=/a@b:c/1-2-3'],
                        zone=system.managing_zone.name,
                    ),
                ),
            ])

        # ssh interface should fail

        system.management_interface = self.mgr.sshManagementInterface()
        system.save()

        response = self._post('jobs', jobXml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 400)
        self.assertXMLEquals(response.content, """
<fault><code>400</code><message>Unsupported management interface</message><traceback></traceback></fault>""")

    def testJobSystemScanResults(self):
        jobType = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_SCAN)
        system = self._saveSystem()
        system.save()
        jobXml = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/inventory/systems/%(systemId)s/descriptors/survey_scan"/>
  <descriptor_data/>
</job>
""" % dict(jobTypeId=jobType.job_type_id, systemId=system.system_id)

        response = self._post('jobs', jobXml,
            username='testuser', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/inventory/systems/%s/descriptors/survey_scan" % system.system_id)

        dbjob = models.Job.objects.get(job_uuid=job.job_uuid)

        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Done</status_text>
  <results>
    <surveys>
      <survey>
        <uuid>aa-bb-cc-dd</uuid>
        <config_properties/>
        <desired_properties/>
        <observed_properties/>
        <discovered_properties/>
        <validation_report/>
        <rpm_packages/>
        <conary_packages/>
        <services/>
      </survey>
    </surveys>
  </results>
</job>
"""

        # Grab token
        jobToken = dbjob.job_token
        jobUrl = "jobs/%s" % dbjob.job_uuid
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        # print response.content
        job = obj.job
        self.failUnlessEqual(job.job_uuid, dbjob.job_uuid)

        # Make sure the job is related to the survey
        self.failUnlessEqual(
            [ x.survey.uuid for x in dbjob.created_surveys.all() ],
            [ 'aa-bb-cc-dd' ]
        )

        # #2337 - make sure active flags are not set
        dbsystem = system.__class__.objects.get(system_id=system.system_id)
        self.assertEquals(bool(dbsystem.has_active_jobs), False)
        self.assertEquals(bool(dbsystem.has_running_jobs), False)

    def testJobSystemSoftwareUpdate(self):
        jobType = self.mgr.sysMgr.eventType(models.EventType.SYSTEM_UPDATE)
        system = self._saveSystem()
        system.save()
        url = "inventory/systems/%(systemId)s/descriptors/update" % dict(
            systemId=system.system_id)
        response = self._get(url,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)

        tree = etree.fromstring(response.content)
        nsmap = dict(dsc='http://www.rpath.com/permanent/descriptor-1.1.xsd')
        fieldNames = tree.xpath('/dsc:descriptor/dsc:dataFields/dsc:field/dsc:name/text()',
            namespaces=nsmap)
        self.assertEquals(fieldNames, ['trove_label', 'dry_run', ])

        jobXml = """
<job>
  <job_type id="http://localhost/api/v1/inventory/event_types/%(jobTypeId)s"/>
  <descriptor id="http://testserver/api/v1/inventory/systems/%(systemId)s/descriptors/update"/>
  <descriptor_data>
    <trove_label>group-foo=example.com@rpath:42/1-2-3</trove_label>
    <dry_run>true</dry_run>
  </descriptor_data>
</job>
""" % dict(jobTypeId=jobType.job_type_id, systemId=system.system_id)

        url = "inventory/systems/%(systemId)s/jobs" % dict(
            systemId=system.system_id)
        response = self._post(url, jobXml,
            username='admin', password='password')
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.descriptor.id,
            "http://testserver/api/v1/inventory/systems/%s/descriptors/update" % system.system_id)

        dbjob = models.Job.objects.get(job_uuid=job.job_uuid)

        jobXml = """
<job>
  <job_state>Completed</job_state>
  <status_code>200</status_code>
  <status_text>Done</status_text>
  <results>
    <preview>
      <ignore-me-1/>
      <ignore-me-2/>
    </preview>
  </results>
</job>
"""

        # Grab token, pretend to be rMake putting CIM job results back to mint.
        jobToken = dbjob.job_token
        jobUrl = "jobs/%s" % dbjob.job_uuid
        response = self._put(jobUrl, jobXml, jobToken=jobToken)
        self.assertEquals(response.status_code, 200)
        obj = xobj.parse(response.content)
        job = obj.job
        self.failUnlessEqual(job.job_uuid, dbjob.job_uuid)

        # Make sure the job is related to the survey
        self.failUnlessEqual(
            [ x.preview for x in dbjob.created_previews.all() ],
            [ "<?xml version='1.0' encoding='UTF-8'?>\n<preview>\n  <ignore-me-1/>\n  <ignore-me-2/>\n</preview>\n" ]
        )

        # Fetch the job
        response = self._get(jobUrl)
        self.assertEquals(response.status_code, 200)

        tree = etree.fromstring(response.content)
        resources = tree.xpath('/job/created_resources')
        self.assertXMLEquals(etree.tostring(resources[0]),
            '<created_resources><preview id="http://testserver/api/v1/inventory/previews/1"/>\n</created_resources>')

        # Make sure we can fetch the preview
        url = "inventory/previews/1"
        response = self._get(url, username="testuser", password="password")
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content,
            '<preview><ignore-me-1/><ignore-me-2/><system id="http://testserver/api/v1/inventory/systems/4"/></preview>')
