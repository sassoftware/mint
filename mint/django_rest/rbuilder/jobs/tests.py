#!/usr/bin/python
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
            [100, 299])
        self.failUnlessEqual([ x.status_text for x in jobs ],
            ["Initializing", "text 299"])

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

        dbjob = models.Job.objects.get(job_uuid=unicode(job.job_uuid))
        # Make sure the job is related to the target type
        self.failUnlessEqual(
            [ x.target_type.name for x in dbjob.jobtargettype_set.all() ],
            [ 'xen-enterprise' ],
        )
