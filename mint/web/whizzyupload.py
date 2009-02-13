#
# Copyright (C) 2008, rPath, Inc.
# All rights reserved
#

from StringIO import StringIO
import os, struct, tempfile, time
from mint.lib.fileupload import fileuploader

### Writer section
def writeMetadata(metafile, size):
    metafile.write('starttime=%f\n' % time.time())
    metafile.write('totalsize=%d\n' % size)
    metafile.write('pid=%d\n' % os.getpid())
    metafile.flush()

def writeManifest(manifest, fs, fieldname):
    ### We write this on our terms, not as a full representation of all the
    ### data submitted
    # Sample output is as follows:
    # fieldname = fieldname
    # filename = <filename provided by the browser>
    # tempfile = <temporary file>
    # content-type = <content-type>
    # content-disposition = <content-disposition>

    f = fs[fieldname]
    manifest.write('fieldname=%s\n' % fieldname)
    #Make sure that we have a file
    if f.file is not None:
        f.flush_to_file()
    manifest.write('filename=%s\n' % f.filename)
    manifest.write('tempfile=%s\n' % f.filen)
    manifest.write('content-type=%s\n' % f.type)
    manifest.write('content-disposition=%s\n' % f.disposition)
    manifest.flush()

class ProgressFileObject(object):
    """ Wrapper intended to produce upload status by wrapping file.read() for stdin.
    """
    def __init__(self, fileobj, statusfile, chunksize=8*1024):
        self.fp = fileobj
        self.sp = statusfile
        self.chunksize = chunksize
        self.readcount = 0
        self.buffer = StringIO()

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            return getattr(self.fp, attr)

    def _writeStatus(self, bytecount):
        self.readcount += bytecount
        b = struct.pack("!Q", self.readcount)
        self.sp.write(b)
        self.sp.flush()

    def buffered_readline(self):
        l = self.fp.readline()
        self.buffer.write(l)
        return l

    def buffer_reset(self):
        self.buffer.seek(0)

    def readline(self, max=None):
        #Try to do it from the buffer first
        # max for a StringIO is treated differently than for a regular file(),
        # so have to do this hackery
        l = self.buffer.readline(*(max and [max] or []))
        if not l:
            l = self.fp.readline(*(max and [max] or []))
        self._writeStatus(len(l))
        return l

    def read(self, datasize=None):
        """ Write how many bytes have been read to the status file.

            This still returns all the requested data as a string, so memory usage could be high if datasize is left at None, just like file.read()
        """
        dataary=[]
        left = datasize
        if datasize is None or left > 0:
            #Read to datasize or to EOF writing out progress every
            #"chunksize" bytes
            while(True):
                thischunksize = self.chunksize < left and self.chunksize or left
                #Read from the internal buffer first
                #d = None
                d = self.buffer.read(thischunksize)
                if len(d) < thischunksize:
                    d += self.fp.read(thischunksize - len(d))
                r = len(d)
                if d:
                    self._writeStatus(r)
                    left -= r
                    dataary.append(d)
                else:
                    break
            return "".join(dataary)

import cgi
class _UploadFieldStorage(cgi.FieldStorage):
    workdir = None
    filen = None

    def flush_to_file(self):
        if self.filen is None:
            f = self.make_file('b')
            f.write(self.value)
            f.flush()
            self.file = f

    def make_file(self, binary=None):
        fd, self.filen = tempfile.mkstemp(prefix='%s-' % self.name, dir=self.workdir)
        f = os.fdopen(fd, 'w+b')
        return f

def genUploadFieldStorage(wkdir):
    class UploadFieldStorage(_UploadFieldStorage):
        workdir = wkdir

    return UploadFieldStorage

### base poller methods
### The cgi handler method
def handle_cgi_request(stdin, stdout, basedir, prefix, env=os.environ):
    # send a content type header so that the browser doesn't close the connection
    print >>stdout, "Content-Type: text/html"

    #Get the ID and fieldname from the query string
    try:
        id = cgi.parse_qs(env['QUERY_STRING'])['uploadId'][0]
        fieldname = cgi.parse_qs(env['QUERY_STRING'])['fieldname'][0]
    except:
        print >>stdout, "Status: 400 Bad request\n"
        print >>stdout, "Invalid request, uploadId and fieldname must be specified in the query string"
        stdout.flush()
        return

    #connect to the working directory
    basewkdir = os.path.join(basedir, prefix + id)

    fileup = fileuploader(basewkdir, fieldname)
    klass = genUploadFieldStorage(basewkdir)

    #Create the status file, and write out the metadata
    statusfile = open(os.path.join(basewkdir, fileup.statusfile), 'wb')
    metafile = open(os.path.join(basewkdir, fileup.metadatafile), 'wt')

    #Wrap stdin
    stdinwrap = ProgressFileObject(stdin, statusfile)

    headsize = 0
    while True:
        l = stdinwrap.buffered_readline()
        headsize += len(l)
        if l == '\n' or l == '\r\n':
            break
    stdinwrap.buffer_reset()

    #We only show progress for the CONTENT_LENGTH assuming that the headers are
    #negligible
    writeMetadata(metafile, headsize + int(env['CONTENT_LENGTH']))
    metafile.close()

    #Create the FieldStorage object with the wrapped stdin
    fs = klass(stdinwrap, environ=env)
    #stdinwrap.close()

    #Now what do we do with it?  Write the final set of data?
    indexfile = open(os.path.join(basewkdir, fileup.manifestfile), 'wt')
    writeManifest(indexfile, fs, fieldname)
    indexfile.close()

    print >>stdout, "Status: 200 Ok\n"
    print >>stdout, "Ok"

    stdout.flush()

