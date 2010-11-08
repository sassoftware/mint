#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

from rmake3 import client as rmk_client
from rmake3.core import types as rmk_types
from rmake3.lib import uuid

from mint.image_gen import constants as iconst
from mint.image_gen.wig import data as wig_data


class WigClient(rmk_client.RmakeClient):
    """Client for creating WIG jobs on rMake."""

    def createJob(self, jobData, subscribe=False):
        jobData = wig_data.ImageJobData.fromDict(jobData)
        job = rmk_types.RmakeJob(
                job_uuid=uuid.uuid4(),
                job_type=iconst.WIG_JOB,
                owner='nobody',
                data=jobData,
                )
        job = self.proxy.createJob(job.freeze())
        return job.job_uuid, job
