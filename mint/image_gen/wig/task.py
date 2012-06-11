#
# Copyright (c) 2011 rPath, Inc.
#

import logging
import json
from rmake3.worker import plug_worker

from jobslave import job_data
from mint import buildtypes
from mint.image_gen import constants as iconst
from mint.image_gen.wig import generator as genmod
from mint.image_gen.wig import isogen

log = logging.getLogger('wig')


class WigTask(plug_worker.TaskHandler):

    taskType = iconst.WIG_TASK

    def run(self):
        data = job_data.JobData(json.loads(self.getData()))
        imageType = data['buildType']
        if imageType == buildtypes.WINDOWS_ISO:
            genClass = isogen.IsoGenerator
        elif imageType == buildtypes.WINDOWS_WIM:
            genClass = genmod.WimGenerator
        elif imageType in (buildtypes.VMWARE_IMAGE,
                buildtypes.VMWARE_ESX_IMAGE):
            genClass = genmod.ConvertedImageGenerator
        else:
            raise TypeError("Invalid Windows image type %s" % imageType)
        generator = genClass(self, data)
        try:
            generator.run()
        finally:
            generator.destroy()


