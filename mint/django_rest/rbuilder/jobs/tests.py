#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.rbuilder.inventory.tests import XMLTestCase

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

        self.job1 = self._newJob(system, eventUuid1, jobUuid1,
            models.EventType.SYSTEM_REGISTRATION)
        self.job2 = self._newJob(system, eventUuid2, jobUuid2,
            models.EventType.SYSTEM_POLL)
        self.job3 = self._newJob(system, eventUuid3, jobUuid3,
            models.EventType.SYSTEM_POLL_IMMEDIATE)

        self.system = system

class JobsTestCase(BaseJobsTest):

    def _mock(self):
        models.Job.getRmakeJob = self.mockGetRmakeJob

    def mockGetRmakeJob(self):
        self.mockGetRmakeJob_called = True

    def testGetJobs(self):
        response = self._get('/api/jobs/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.jobs_xml)

    def testGetJobStates(self):
        response = self._get('/api/job_states/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.job_states_xml)

    def testGetJob(self):
        response = self._get('/api/jobs/1/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.job_xml)

    def testGetJobState(self):
        response = self._get('/api/job_states/1/')
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.job_state_xml)

    def testGetSystemJobs(self):
        response = self._get('/api/inventory/systems/%s/jobs/' % \
            self.system.pk)
        self.assertEquals(response.status_code, 200)
        self.assertXMLEquals(response.content, testsxml.systems_jobs_xml)

class Jobs2TestCase(BaseJobsTest):
    def _mock(self):
        class DummyStatus(object):
            def __init__(slf, **kwargs):
                slf.__dict__.update(kwargs)
        class DummyJob(object):
            def __init__(slf, code, text, detail, final, completed, failed):
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
                j = DummyJob(code, text, detail, final, completed, failed)
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

        response = self._get('/api/jobs/')
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

