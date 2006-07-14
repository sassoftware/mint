#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

from mint import buildtypes
from mint.distro import raw_hd_image

class RawFsImage(raw_hd_image.RawHdImage):
    fileType = buildtypes.typeNames[buildtypes.RAW_FS_IMAGE]

    def __init__(self, *args, **kwargs):
        res = raw_hd_image.RawHdImage.__init__(self, *args, **kwargs)
        self.makeBootable = False
        return res
