#
# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#

import raw_hd_image

class RawFsImage(raw_hd_image.RawHdImage):
    fileType = 'Raw Filesystem Image'

    def __init__(self, *args, **kwargs):
        res = raw_hd_image.RawHdImage.__init__(self, *args, **kwargs)
        self.makeBootable = False
        return res
