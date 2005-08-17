#
# Copyright (c) 2004-2005 rPath, Inc.
#
# All Rights Reserved
#
from imagegen import ImageGenerator

class LiveCFImage(ImageGenerator):
    def write(self):
        raise NotImplementedError
