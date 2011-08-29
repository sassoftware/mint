#
# Copyright (c) 2011 rPath, Inc.
#

import hashlib
from jobslave.response import FilePutter
from restlib import client as rl_client
from rmake3.worker import plug_worker
from xml.etree import ElementTree as ET

from mint.image_gen import constants as iconst
from mint.image_gen.util import FileWithProgress


class ImageUploadTask(plug_worker.TaskHandler):

    taskType = iconst.IUP_TASK

    def run(self):
        self.params = self.getData()
        image = self.params.image

        for imageFile in image.files:
            self._uploadFile(imageFile)

        self._commitImage()
        self.sendStatus(iconst.IUP_JOB_DONE, "Image uploaded")

    def _uploadFile(self, imageFile):
        progStr = "Uploading file %s" % (imageFile.fileName,)
        self.sendStatus(iconst.IUP_JOB_UPLOADING, progStr)

        srcUrl = imageFile.url
        srcClient = rl_client.Client(srcUrl.asString(), srcUrl.headers)
        srcClient.connect()
        response = srcClient.request('GET', srcUrl.unparsedPath)

        digest = hashlib.sha1()
        size = int(response.getheader('Content-Length') or 0)
        def callback(transferred):
            if size:
                percent = int(100.0 * transferred / size)
                progress = ': %d%%' % percent
            else:
                mebibytes = transferred / 1048576.0
                progress = ': %.1fMiB' % mebibytes
            self.sendStatus(iconst.IUP_JOB_UPLOADING, progStr + progress)
        wrapper = FileWithProgress(response, callback)

        destUrl = imageFile.destination
        destClient = FilePutter(destUrl.asString(), destUrl.headers)
        destClient.connect()
        destClient.putFileObject('PUT', wrapper, digest,
                fileSize=(size or None))

        imageFile.size = wrapper.total
        imageFile.sha1 = digest.hexdigest()

    def _commitImage(self):
        self.sendStatus(iconst.IUP_JOB_PACKAGING,
                "Committing image to repository")
        url = self.params.imageURL.asString() + 'files'
        # This is awkward. Thanks, modellib.
        root = ET.Element('files')
        for imageFile in self.params.image.files:
            fx = ET.SubElement(root, 'file')
            ET.SubElement(fx, 'title').text = imageFile.title
            ET.SubElement(fx, 'size').text = str(imageFile.size)
            ET.SubElement(fx, 'sha1').text = imageFile.sha1
            ET.SubElement(fx, 'fileName').text = imageFile.fileName
        mx = ET.SubElement(root, 'metadata')
        for key, value in self.params.image.metadata.items():
            ET.SubElement(mx, key).text = str(value)

        client = rl_client.Client(url, self.params.imageURL.headers)
        client.connect()
        client.request('PUT', ET.tostring(root))
