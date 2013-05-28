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

import cgi
import logging
import os
import struct
import shutil
import tempfile
import time
import urllib2
from conary.lib import util
from mint.lib.fileupload import fileuploader
from webob import exc as web_exc
from webob import request

log = logging.getLogger(__name__)


def handle(context):
    if context.req.path_info == '/urldownloader.cgi':
        return URLDownloader(context).handle()
    elif context.req.path_info in ('/fileupload.cgi', '/fileupload-nginx'):
        return FileUpload(context).handle()
    else:
        return web_exc.HTTPNotFound()


class URLDownloader(object):
    CHUNKSIZE = 512 * 1024

    def __init__(self, context):
        self.req = context.req
        self.cfg = context.cfg
        self.start_response = context.start_response

    def handle(self):
        workDir = os.path.join(self.cfg.dataPath, 'tmp')
        url = self.req.GET['fileUrl']
        fileName = os.path.basename(url)
        self.start_response('200 OK', [
            ('Content-Type', 'text/html'),
            ('Status', 'Ok'),
            ])
        yield ''

        error = ''
        try:
            downloadedUrlPath = self.downloadUrl(url, workDir)
        except Exception, e:
            log.exception('download failed')
            downloadedUrlPath = None
            error = 'File download failed: %s' % str(e)

        yield self.uploadUrl(downloadedUrlPath, workDir, 'rb-pc-upload-',
                fileName, error=error)

    def writeManifest(self, manifest, fieldname, filename, tempfilename,
            error=None):
        ### We write this on our terms, not as a full representation of all the
        ### data submitted
        # Sample output is as follows:
        # fieldname = fieldname
        # filename = <filename provided by the browser>
        # tempfile = <temporary file>
        # content-type = <content-type>
        # content-disposition = <content-disposition>

        manifest.write('fieldname=%s\n' % fieldname)
        manifest.write('filename=%s\n' % filename)
        manifest.write('tempfile=%s\n' % tempfilename)
        manifest.write('content-type=%s\n' % 'application/octet-stream')
        manifest.write('content-disposition=%s\n' % 'form-data')
        manifest.write('error=%s\n' % error)
        manifest.flush()

    def uploadUrl(self, path, basedir, prefix, fileName, error=None):
        # Get the ID and fieldname from the query string
        id = self.req.GET['uploadId']

        # connect to the working directory
        basewkdir = os.path.join(basedir, prefix + id)

        # Create the dir if it doesn't exist
        if not os.path.exists(basewkdir):
            util.mkdirChain(basewkdir)

        filePath = ''
        if path and os.path.exists(path):
            filePath = os.path.join(basewkdir, os.path.basename(path))
            shutil.move(path, filePath)

        indexfile = open(os.path.join(basewkdir, 'uploadfile-index'), 'wt')
        self.writeManifest(indexfile, 'uploadfile', fileName,
            filePath, error=error)
        indexfile.close()

        return 'Ok'

    def downloadUrl(self, url, workDir):
        tempFilePath = tempfile.mktemp(suffix='.pcupload', dir=workDir)
        tempFile = open(tempFilePath, 'w+b')

        openUrl = urllib2.urlopen(url)

        while True:
            data = openUrl.read(self.CHUNKSIZE)
            if data:
                tempFile.write(data)
            else:
                break
        tempFile.close()

        return tempFilePath


class FileUpload(object):

    def __init__(self, context):
        self.req = context.req
        self.cfg = context.cfg
        self.responseFactory = context.responseFactory

    def handle(self):
        basedir = os.path.join(self.cfg.dataPath, 'tmp')
        #Get the ID and fieldname from the query string
        id = self.req.GET['uploadId']
        fieldname = self.req.GET['fieldname']
        #connect to the working directory
        basewkdir = os.path.join(basedir, 'rb-pc-upload-' + id)
        fileup = fileuploader(basewkdir, fieldname)
        #Create the status file, and write out the metadata
        statusfile = open(os.path.join(basewkdir, fileup.statusfile), 'wb')
        metafile = open(os.path.join(basewkdir, fileup.metadatafile), 'wt')
        self.writeMetadata(metafile)
        metafile.close()
        # Copy data. This is done by instantiating a custom FieldStorage class
        # which will spool the uploaded file to the workdir while writing out
        # progress information.
        fsClass = makeFieldStorageClass(basewkdir, fieldname, statusfile)
        try:
            fs = fsClass(fp=self.req.body_file, environ=self.req.environ)
            #Now what do we do with it?  Write the final set of data?
            indexfile = open(os.path.join(basewkdir, fileup.manifestfile), 'wt')
            self.writeManifest(indexfile, fs, fieldname)
            indexfile.close()
            return self.responseFactory("Ok\n", headerlist=[
                ('Content-Type', 'text/html'),
                ('Status', 'Ok'),
                ])
        except request.DisconnectionError:
            log.error("Client disconnected during upload at %s", self.req.url)
            return web_exc.HTTPBadRequest()


    def writeMetadata(self, metafile):
        metafile.write('starttime=%f\n' % time.time())
        metafile.write('pid=%d\n' % os.getpid())
        metafile.flush()

    def writeManifest(self, manifest, fs, fieldname):
        ### We write this on our terms, not as a full representation of all the
        ### data submitted
        # Sample output is as follows:
        # fieldname = fieldname
        # filename = <filename provided by the browser>
        # tempfile = <temporary file>
        # content-type = <content-type>
        # content-disposition = <content-disposition>
        if fieldname + '_path' in fs:
            # nginx upload
            filename = fs[fieldname + '_name'].value
            temppath = fs[fieldname + '_path'].value
        else:
            # direct upload
            f = fs[fieldname]
            if f.file is not None:
                f.flush_to_file()
            filename = f.filename
            temppath = f.filen
        manifest.write('fieldname=%s\n' % fieldname)
        manifest.write('filename=%s\n' % filename)
        manifest.write('tempfile=%s\n' % temppath)
        manifest.flush()


class _UploadFieldStorage(cgi.FieldStorage):
    """
    Override the default temporary file handling behavior of the FieldStorage
    class.

    First, place the file in the desired directory instead of /tmp. Second,
    record upload progress to the status file.

    Note that the class attributes here must be class attributes because
    FieldStorage will recursively instantiate itself for each field.
    """
    # These settings propagate to children
    callback = None
    fieldname = None
    statusfile = None
    workdir = None

    # These values are bound to the instance
    filen = None
    written = 0

    def flush_to_file(self):
        if self.filen is None:
            f = self.make_file('b')
            f.write(self.value)
            f.flush()
            self.file = f

    def make_file(self, binary=None):
        fobj = tempfile.NamedTemporaryFile(prefix='%s-' % self.name,
                dir=self.workdir, delete=False)
        self.filen = fobj.name
        if self.name == self.fieldname:
            # This is the upload file field, so track its progress
            fobj = StatusWritingWrapper(fobj, self.statusfile)
        return fobj


def makeFieldStorageClass(workdir_, fieldname_, statusfile_):
    """
    Make a new class with the specified settings. This ugliness is necessary
    because of how FieldStorage recursively instantiates itself.
    """
    class UploadFieldStorage(_UploadFieldStorage):
        workdir = workdir_
        fieldname = fieldname_
        statusfile = statusfile_
    return UploadFieldStorage


class StatusWritingWrapper(object):
    FLUSH_INTERVAL = 0.25

    def __init__(self, fobj, statusfile):
        self.fobj = fobj
        self.statusfile = statusfile
        self.written = 0
        self.lastFlush = time.time()

    def write(self, data):
        self.fobj.write(data)
        self.written += len(data)
        if time.time() - self.lastFlush > self.FLUSH_INTERVAL:
            self.lastFlush = time.time()
            self.statusfile.write(struct.pack("!Q", self.written))
            self.statusfile.flush()

    def __getattr__(self, key):
        return getattr(self.fobj, key)
