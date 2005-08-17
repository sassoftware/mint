#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import os.path

from imagegen import ImageGenerator

class StubImage(ImageGenerator):
    def write(self):
        f = os.path.join(self.cfg.imagesPath, "stub.iso")

        stub = file(f, "w")
        print >> stub, "Hello World!"

        return [f]
