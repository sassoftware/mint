#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.http import HttpResponse

from mint.django_rest.rbuilder.jobs import models
from mint.django_rest.rbuilder import service
from mint.django_rest.deco import requires, return_xml, access, Flags

class JobsBaseService(service.BaseAuthService):
    def _check_uuid_auth(self, request, kwargs):
        headerName = 'X-rBuilder-Job-Token'
        jobToken = self.getHeaderValue(request, headerName)
        if not jobToken:
            return None
        jobUuid = kwargs['job_uuid']
        # Check for existance
        jobs = models.Job.objects.filter(
            job_uuid=jobUuid, job_token=jobToken)
        if not jobs:
            return False
        self._setMintAuth(jobs[0].created_by)
        return True

class JobsService(JobsBaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.get()

    def get(self):
        return self.mgr.getJobs()

    @requires("job", flags=Flags(save=False))
    @return_xml
    def rest_POST(self, request, job):
        return self.mgr.addJob(job)

class JobService(JobsBaseService):
    @access.anonymous
    @return_xml
    def rest_GET(self, request, job_uuid):
        return self.get(job_uuid)

    def get(self, job_uuid):
        return self.mgr.getJob(job_uuid=job_uuid)

    @access.auth_token
    @requires("job")
    @return_xml
    def rest_PUT(self, request, job_uuid, job):
        return self.mgr.updateJob(job_uuid, job)

    def rest_DELETE(self, job_uuid):
        self.mgr.deleteJob(job_uuid)
        response = HttpResponse(status=204)
        return response

class JobStatesService(service.BaseService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.get()

    def get(self):
        return self.mgr.getJobStates()

class JobStateService(service.BaseService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, job_state_id):
        return self.get(job_state_id)

    def get(self, job_state_id):
        return self.mgr.getJobState(job_state_id)

class JobStatesJobsService(service.BaseService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, job_state_id):
        return self.get(job_state_id)

    def get(self, job_state_id):
        return self.mgr.getJobsByJobState(job_state_id)

class JobSystemsService(JobsBaseService):
    @access.auth_token
    @requires("systems", flags=Flags(save=False))
    @return_xml
    def rest_POST(self, request, job_uuid, systems):
        job = self.mgr.getJob(job_uuid=job_uuid)
        return self.mgr.addLaunchedSystems(systems, job=job, forUser=self.mgr.user)
