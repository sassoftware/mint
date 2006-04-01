#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

# python standard library imports
import os, sys
import tempfile
import subprocess
import re

# mint imports
from imagegen import ImageGenerator, MSG_INTERVAL
import bootable_image

from conary.lib import util
from mint import releasetypes


class Tarball(bootable_image.BootableImage):
    fileType = releasetypes.typeNames[releasetypes.TARBALL]

    def write(self):
        try:
            # instantiate the contents that need to go into the image
            self.createFileTree()
            # and instantiate the image itself
            self.createImage('tarball')
            self.status('Compressing taball')
            newExt = self.outfile.replace('.img', '.tgz')
            os.rename(self.outfile, newExt)
            imagesList = [(newExt, self.fileType)]
        finally:
            if self.fakeroot:
                util.rmtree(self.fakeroot)

        return self.moveToFinal(imagesList,
                                os.path.join(self.cfg.finishedPath,
                                             self.project.getHostname(),
                                             str(self.release.getId())))

    def __init__(self, *args, **kwargs):
        res = bootable_image.BootableImage.__init__(self, *args, **kwargs)
        self.freespace = 0
        self.addJournal = False
        self.makeBootable = False
        return res
