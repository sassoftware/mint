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
    def rest_GET(self, request, job_id=None):
        return self.get(job_id)

    def get(self, job_id):
        if job_id:
            return self.mgr.getJob(job_id)
        else:
            return self.mgr.getJobs()

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
