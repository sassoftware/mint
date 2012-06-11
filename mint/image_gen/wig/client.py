#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

from rmake3 import client as rmk_client
from rmake3.core import types as rmk_types
from rmake3.lib import uuid

from mint.image_gen import constants as iconst


class WigClient(rmk_client.RmakeClient):
    """Client for creating WIG jobs on rMake."""

    def createJob(self, jobData, subscribe=False):
        job = rmk_types.RmakeJob(
                job_uuid=uuid.uuid4(),
                job_type=iconst.WIG_JOB,
                owner='nobody',
                data=jobData,
                )
        job = self.proxy.createJob(job.freeze())
        return job.job_uuid, job
