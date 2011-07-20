#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.http import HttpResponse

from mint.django_rest.rbuilder import service
from mint.django_rest.deco import requires, return_xml, access

class JobsService(service.BaseService):
    
    @access.anonymous
    @return_xml
    def rest_GET(self, request, job_uuid=None):
        return self.get(job_uuid=job_uuid)

    def get(self, job_uuid):
        if job_uuid:
            return self.mgr.getJob(job_uuid=job_uuid)
        else:
            return self.mgr.getJobs()

    @requires("job")
    @return_xml
    def rest_POST(self, job):
        return self.mgr.addJob(job)

    @requires("job")
    @return_xml
    def rest_PUT(self, job_uuid, job):
        return self.mgr.updateJob(job_uuid, job)

    def rest_DELETE(self, job_uuid):
        self.mgr.deleteJob(job_uuid)
        response = HttpResponse(status=204)
        return response

class JobStatesService(service.BaseService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, job_state_id=None):
        return self.get(job_state_id)

    def get(self, job_state_id):
        if job_state_id:
            return self.mgr.getJobState(job_state_id)
        else:
            return self.mgr.getJobStates()

class JobStatesJobsService(service.BaseService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request, job_state_id):
        return self.get(job_state_id)

    def get(self, job_state_id):
        return self.mgr.getJobsByJobState(job_state_id)
