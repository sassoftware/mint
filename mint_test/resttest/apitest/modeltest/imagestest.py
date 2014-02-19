#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint_test import mint_rephelp


from mint.rest.api import models
from mint.rest.modellib import converter

class ImageModelTest(mint_rephelp.MintDatabaseHelper):

    def testImageListModel(self):
        images = converter.fromText('xml', imageList, models.ImageList, None, 
                                    None)
        assert(images.images[0].imageId == 1)

    def testImageFileURL(self):
        xml = """\
<image>
  <name>my image</name>
  <files>
    <file>
      <title>image title</title>
      <size>1234</size>
      <sha1>abc</sha1>
      <fileName>file name</fileName>
      <url urlType="0">http://localhost:1234</url>
      <url>http://localhost:12345</url>
      <url urlType="1"/>
    </file>
  </files>
  <imageId>1</imageId>
</image>
"""
        image = converter.fromText("xml", xml, models.Image, None, None)
        self.failUnlessEqual(image.name, "my image")
        self.failUnlessEqual([ x.title for x in image.files.files ],
            ['image title'])
        self.failUnlessEqual([ x.size for x in image.files.files ],
            [1234])
        self.failUnlessEqual([ x.sha1 for x in image.files.files ],
            ['abc'])
        self.failUnlessEqual([ x.fileName for x in image.files.files ],
            ['file name'])
        self.failUnlessEqual(
            [ [ (y.url, y.urlType) for y in x.urls ] for x in image.files.files ],
            [ [
                ('http://localhost:1234', 0),
                ('http://localhost:12345', None),
                (None, 1),
            ] ],
            )

        class Controller(object):
            def url(slf, request, *args, **kwargs):
                return args[0]
        class Request(object):
            def __init__(slf, baseUrl):
                slf.baseUrl = baseUrl

        # Need to set the file ID
        counter = 42
        for f in image.files.files:
            for url in f.urls:
                url.urlType = 0
                url.fileId = counter
                counter += 1
        # Now make sure we can dump the data back in xml, and the url
        # attribute/text field doesn't cause problems.
        newxml = converter.toText("xml", image, Controller(),
            Request("irc://goo/"))

        tmpl = '<url urlType="0">irc://goo/downloadImage?fileId=%s&amp;urlType=0</url>'
        for fileId in [42, 43, 44]:
            self.assertIn(tmpl % fileId, newxml)

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

