#!/usr/bin/env python
# Copyright (c) 2010 rPath, Inc.
# All rights reserved

import cgi
import cgitb
import os
import shutil
import signal
import sys
import tempfile
import urllib2

from mint import config

def cancel_signal(num, frame):
    print "Status: 200 Ok\n"
    print "Cancelled"
    sys.exit(0)

signal.signal(signal.SIGUSR1, cancel_signal)

class UrlForm(cgi.FieldStorage):
    pass

def getUrl():
    url =  cgi.parse_qs(os.environ['QUERY_STRING'])['fileUrl'][0]
    # urlForm = UrlForm()
    # if 'url' in urlForm:
        # return urlForm['url'].value
    # else:
        # raise Exception("Url not found in form input")
    return url

def writeManifest(manifest, fieldname, filename, tempfilename):
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
    manifest.flush()

def uploadUrl(path, basedir, prefix, fileName):
    print >>sys.stdout, "Content-Type: text/html"

    #Get the ID and fieldname from the query string
    id = cgi.parse_qs(os.environ['QUERY_STRING'])['uploadId'][0]

    #connect to the working directory
    basewkdir = os.path.join(basedir, prefix + id)

    filePath = os.path.join(basewkdir, os.path.basename(path))
    shutil.copyfile(path, filePath)
    indexfile = open(os.path.join(basewkdir, 'uploadfile-index'), 'wt')
    writeManifest(indexfile, 'uploadfile', fileName,
        filePath)
    indexfile.close()

    print >>sys.stdout, "Status: 200 Ok\n"
    print >>sys.stdout, "Ok"


def downloadUrl(url, workDir):

    tempFilePath = tempfile.mktemp(suffix='.ccs', dir=workDir)
    tempFile = open(tempFilePath, 'w+b')
    tempFile.write(urllib2.urlopen(url).read())
    tempFile.close()

    return tempFilePath

def main():
    cgitb.enable()

    mintCfg = config.MintConfig()
    workDir = os.path.join(mintCfg.dataPath, 'tmp')
    
    url = getUrl()
    fileName = os.path.basename(url)

    downloadedUrlPath = downloadUrl(url, workDir)
    # html = getFormHtml(downloadedUrlPath)

    return uploadUrl(downloadedUrlPath, workDir, 'rb-pc-upload-', fileName)

if __name__ == '__main__':
    main()
