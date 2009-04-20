#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import testsetup
import mint_rephelp


from mint.rest.api import models
from mint.rest.modellib import converter

class ReleaseModelTest(mint_rephelp.MintDatabaseHelper):
    def testImageListModel(self):
        release = converter.fromText('xml', data, models.Release, None,
                                    None)
        assert(release.imageIds is None)

data = """<?xml version='1.0' encoding='UTF-8'?>
<release id="http://%(server)s:%(port)s/api/products/testproject/releases/1">
<hostname>testproject</hostname>
<name>Release Name</name>
</release>
"""

if __name__ == "__main__":
        testsetup.main()
