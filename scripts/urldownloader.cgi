#!/usr/bin/env python
#
# Copyright (c) rPath, Inc.
# All rights reserved

import cgi
import cgitb
import os
import shutil
import signal
import sys
import tempfile
import urllib2
import logging

from conary.lib import util
from mint import config

log = logging.getLogger('urldownloader.cgi')

CHUNKSIZE = 512 * 1024

def cancel_signal(num, frame):
    print "Status: 200 Ok\n"
    print "Cancelled"
    sys.exit(0)

signal.signal(signal.SIGUSR1, cancel_signal)

def getUrl():
    url =  cgi.parse_qs(os.environ['QUERY_STRING'])['fileUrl'][0]
    return url

def writeManifest(manifest, fieldname, filename, tempfilename, error=None):
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

def uploadUrl(path, basedir, prefix, fileName, error=None):
    print >>sys.stdout, "Content-Type: text/html"

    # Get the ID and fieldname from the query string
    id = cgi.parse_qs(os.environ['QUERY_STRING'])['uploadId'][0]

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
    writeManifest(indexfile, 'uploadfile', fileName,
        filePath, error=error)
    indexfile.close()

    print >>sys.stdout, "Status: 200 Ok\n"
    print >>sys.stdout, "Ok"

def downloadUrl(url, workDir):
    tempFilePath = tempfile.mktemp(suffix='.pcupload', dir=workDir)
    tempFile = open(tempFilePath, 'w+b')

    openUrl = urllib2.urlopen(url)

    while True:
        data = openUrl.read(CHUNKSIZE)
        if data:
            tempFile.write(data)
        else:
            break
    tempFile.close()

    return tempFilePath

def main():
    cgitb.enable()

    mintCfg = config.MintConfig()
    docRoot = os.environ.get('DOCUMENT_ROOT', '')
    cfgPath = os.path.join(docRoot, 'rbuilder.conf')

    if docRoot and os.path.exists(cfgPath):
        mintCfg.read(cfgPath)
    else:
        mintCfg.read(config.RBUILDER_CONFIG)

    workDir = os.path.join(mintCfg.dataPath, 'tmp')

    url = getUrl()
    fileName = os.path.basename(url)

    error = ''
    try:
        downloadedUrlPath = downloadUrl(url, workDir)
    except Exception, e:
        log.exception('download failed')
        downloadedUrlPath = None
        error = 'File download failed: %s' % str(e)

    return uploadUrl(downloadedUrlPath, workDir, 'rb-pc-upload-', fileName,
        error=error)

if __name__ == '__main__':
    main()
