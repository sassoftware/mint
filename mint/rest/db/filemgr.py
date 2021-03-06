#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import errno
import os
from conary.lib import util
from restlib import response

from mint.rest.db import manager


class FileManager(manager.Manager):
    def _getImagePath(self, hostname, imageId, fileName=None, create=False):
        path = os.path.join(self.cfg.imagesPath, hostname, str(imageId))
        if create and not os.path.isdir(path):
            util.mkdirChain(path)
        if fileName:
            path = os.path.join(path, fileName)
        return path

    def imageHasFile(self, hostname, imageId, fileName):
        return os.path.isfile(self._getImagePath(hostname, imageId, fileName))

    def getImageFile(self, hostname, imageId, fileName, asResponse=False):
        path = self._getImagePath(hostname, imageId, fileName)
        if os.path.exists(path):
            if asResponse:
                return response.FileResponse(path, 'text/plain')
            else:
                return open(path).read()

        else:
            if asResponse:
                return response.Response('', 'text/plain')
            else:
                return ''

    def appendImageFile(self, hostname, imageId, fileName, data):
        path = self._getImagePath(hostname, imageId, fileName, create=True)
        fObj = open(path, 'a')
        fObj.write(data)
        fObj.close()

    def deleteImageFile(self, hostname, imageId, fileName):
        path = self._getImagePath(hostname, imageId, fileName)
        try:
            os.unlink(path)
        except OSError, err:
            if err.args[0] != errno.ENOENT:
                raise
        # Try to delete the parent directory
        try:
            os.rmdir(os.path.dirname(path))
        except OSError, err:
            if err.args[0] not in (errno.ENOENT, errno.ENOTEMPTY):
                raise

    def openImageFile(self, hostname, imageId, fileName, mode):
        create = mode[0] in 'aw'
        path = self._getImagePath(hostname, imageId, fileName, create)
        return open(path, mode)
