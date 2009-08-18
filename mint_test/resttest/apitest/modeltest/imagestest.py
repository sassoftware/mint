#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import testsetup
from mint_test import mint_rephelp


from mint.rest.api import models
from mint.rest.modellib import converter

class ReleaseModelTest(mint_rephelp.MintDatabaseHelper):
    def testReleaseModel(self):
        release = converter.fromText('xml', data, models.UpdateRelease, None, None)
        assert(release.imageIds[0].imageId == 1)

    def testImageListModel(self):
        images = converter.fromText('xml', imageList, models.ImageList, None, 
                                    None)
        assert(images.images[0].imageId == 1)

data = """<?xml version='1.0' encoding='UTF-8'?>
<release id="http://%(server)s:%(port)s/api/products/testproject/releases/1">
<hostname>testproject</hostname>
<name>Release Name</name>
<imageIds>
<imageId>1</imageId>
</imageIds>
</release>
"""

imageList = """<?xml version='1.0' encoding='UTF-8'?>
<images>
<image>
<imageId>1</imageId>
</image>
</images>
"""

if __name__ == "__main__":
        testsetup.main()
