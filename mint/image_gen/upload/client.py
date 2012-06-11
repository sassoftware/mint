#
# Copyright (c) 2011 rPath, Inc.
#

from rmake3 import client as rmk_client
from rmake3.core import types as rmk_types
from rmake3.lib import uuid

from mint.image_gen import constants as iconst
from mint.image_gen.upload import handler


class UploadClient(rmk_client.RmakeClient):

    def downloadImages(self, image, imageURL):
        params = handler.ImageUploadParams(image=image, imageURL=imageURL)
        job = rmk_types.RmakeJob(
                job_uuid=uuid.uuid4(),
                job_type=iconst.IUP_JOB,
                owner='nobody',
                data=params,
                )
        job = self.proxy.createJob(job.freeze())
        return job.job_uuid, job
