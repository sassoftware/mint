#
# Copyright (c) 2011 rPath, Inc.
#

import hashlib
from restlib import client as rl_client
from rmake3.worker import plug_worker
from xml.etree import ElementTree as ET

from mint.django_rest import timeutils
from mint.image_gen import constants as iconst
from mint.image_gen.response import FilePutter
from mint.image_gen.util import FileWithProgress


class ImageUploadTask(plug_worker.TaskHandler):

    taskType = iconst.IUP_TASK

    def run(self):
        self.params = self.getData()
        image = self.params.image

        for imageFile in image.files:
            try:
                self._uploadFile(imageFile)
            except rl_client.ConnectionError, e:
                self.sendStatus(iconst.IUP_JOB_FAILED,
                    "Failed to import image URL %s %s" %
                        (imageFile.url.asString(), str(e)))
                return

        self._commitImage()
        self.sendStatus(iconst.IUP_JOB_DONE, "Image uploaded")

    def _uploadFile(self, imageFile):
        progStr = "Uploading file %s" % (imageFile.file_name,)
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
        url = self.urlJoin(self.params.imageURL.asString(), 'files')
        # This is awkward. Thanks, modellib.
        root = ET.Element('files')
        for imageFile in self.params.image.files:
            fx = ET.SubElement(root, 'file')
            ET.SubElement(fx, 'title').text = imageFile.title
            ET.SubElement(fx, 'size').text = str(imageFile.size)
            ET.SubElement(fx, 'sha1').text = imageFile.sha1
            ET.SubElement(fx, 'fileName').text = imageFile.file_name
        mx = ET.SubElement(root, 'metadata')
        for key, value in self.params.image.metadata.items():
            ET.SubElement(mx, key).text = str(value)

        headers = self.params.imageURL.headers.copy()
        headers['Content-Type'] = 'application/xml'
        client = rl_client.Client(url, headers)
        client.connect()
        client.request('PUT', ET.tostring(root))
        self.logMessage('Image built')

    def logMessage(self, msg, *args):
        """
        jobslave/response.py has a smart log handler that runs in a different
        thread. We don't need that, we should send state changes as logs
        but we're not there. This is hopefully just a short-term fix
        (but isn't that what we always say?) -- misa 2012-03-13
        """
        tstamp = timeutils.now()
        if not args:
            msgString = "%s %s\n" % (tstamp, msg)
        else:
            msgString = "%s %s\n" % (tstamp, msg % args)

        url = self.urlJoin(self.params.imageURL.asString(), 'buildLog')

        headers = self.params.imageURL.headers.copy()
        headers['Content-Type'] = 'text/plain'
        client = rl_client.Client(url, headers)
        client.connect()
        try:
            client.request("POST", body=msgString)
        except rl_client.ResponseError, e:
            if e.status != 204:
                raise

    @classmethod
    def urlJoin(cls, *args):
        """
        Join arguments by / after stripping leading and trailing /, to avoid
        duplicating it
        """
        return '/'.join(x.strip('/') for x in args)
