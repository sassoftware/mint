#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

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
            models.EventType.SYSTEM_POLL, createdBy=user)
        self.job3 = self._newSystemJob(system, eventUuid3, jobUuid3,
            models.EventType.SYSTEM_POLL_IMMEDIATE, createdBy=user)

        self.system = system

class JobsTestCase(BaseJobsTest):

    def _mock(self):
        models.Job.getRmakeJob = self.mockGetRmakeJob

    def mockGetRmakeJob(self):
        self.mockGetRmakeJob_called = True

    def testGetJobs(self):
        response = self._get('jobs/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.jobs_xml)

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
            [models.JobState.RUNNING, models.JobState.COMPLETED,
            models.JobState.FAILED ])

        self.failUnlessEqual([ int(x.status_code) for x in jobs ],
            [101, 299, 404])
        self.failUnlessEqual([ x.status_text for x in jobs ],
            ["text 101", "text 299", "text 404"])

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


