#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import os
import urllib

import rpath_capsule_indexer

from mint import notices_store
from mint.rest.api import base
from mint.rest.middleware import auth, response

class ContentController(base.BaseController):
    modelName = 'capsuleKey'
    processSuburls = True

    @auth.internal
    @auth.public
    def get(self, req, capsuleType = None, capsuleKey = None):
        # To serve capsules, we expect capsuleKey/capsuleSha1
        # To serve files from capsules, # capsuleKey/capsuleSha1/filePath/fileSha1
        resp404 = response.response.Response(status=404)
        arr = req.unparsedPath.split('/')
        arrLen = len(arr)
        if arrLen in [0, 2]:
            return resp404
        capsuleKey = urllib.unquote(capsuleKey)
        capsuleSha1 = arr[0]
        indexer = self.db.capsuleMgr.getIndexer()
        if arrLen > 1:
            filePath = urllib.unquote(arr[1])
            fileSha1 = arr[2]
            try:
                stream = indexer.getFileFromPackage(capsuleKey, capsuleSha1,
                    filePath, fileSha1)
            except indexer.DownloadError:
                return resp404
            return response.SeekableStreamResponse(stream)
        pkg = indexer.getPackage(capsuleKey, capsuleSha1)
        if pkg is None:
            return resp404
        absPath = indexer.getFullFilePath(pkg)
        return response.SeekableStreamResponse(file(absPath))

    @auth.internal
    @auth.public
    def create(self, req, capsuleType, **kwargs):
        indexer = self.db.capsuleMgr.getIndexer()
        try:
            indexer.refresh()
        except rpath_capsule_indexer.errors.RPCError:
            return response.response.Response(status = 500)
        return response.response.Response(content_type = "text/plain",
            status = 204)

class CapsulesController(base.BaseController):
    modelName = "capsuleType"

    urls = dict(content = ContentController)
