#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import os
import sys
import time

from conary.lib import util
from restlib import response

from mint import builds
from mint import buildtypes
from mint import helperfuncs
from mint import mint_error
from mint.lib import data
from mint.rest import errors
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
