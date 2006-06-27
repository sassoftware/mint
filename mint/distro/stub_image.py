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

        productId = self.job.getProductId()
        product = self.client.getProduct(productId)
        stubContent = product.getDataValue('stringArg')
        
        stub = file(f, "w")
        print >> stub, stubContent

        return [(f, "Disk 1")]
