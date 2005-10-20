#
# Copyright (c) 2004-2005 rPath, Inc.
#
# All Rights Reserved
#
import os
import sys

from lib import util
from imagegen import ImageGenerator

class Cleanup(ImageGenerator):
    def write(self):
        releaseId = self.job.getReleaseId()
        release = self.client.getRelease(releaseId)
        version = release.getTroveVersion()
        revision = version.trailingRevision().asString()
        project = self.client.getProject(release.getProjectId())
        
        topdir = os.path.join(self.cfg.imagesPath,
                              project.getHostname(),
                              release.getArch(),
                              revision,
                              "unified")

        print >> sys.stderr, "cleaning %s" % topdir
        # util.rmtree(topdir)
        return [] 
