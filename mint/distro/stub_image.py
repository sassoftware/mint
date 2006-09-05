#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import os.path

from mint.distro.imagegen import ImageGenerator

class StubImage(ImageGenerator):
    def write(self):
        f = os.path.join(self.cfg.finishedPath, "stub.iso")

        buildId = self.job.getBuildId()
        build = self.client.getBuild(buildId)
        stubContent = build.getDataValue('stringArg')

        stub = file(f, "w")
        print >> stub, stubContent

        return [(f, "Disk 1")]
