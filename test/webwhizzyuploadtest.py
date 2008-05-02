import testsuite
testsuite.setup()
import unittest

import tempfile, os, signal
import struct
from StringIO import StringIO

import conary.lib.util
from mint.web import whizzyupload

multipart_headers_template = """POST /cgi-bin/fileupload.cgi HTTP/1.1
User-Agent: Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.8.1.13) Gecko/20080328 Foresight Firefox/2.0.0.13
Accept: text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5
Accept-Language: en-us,en;q=0.5
Accept-Encoding: gzip,deflate
Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7
Keep-Alive: 300
Connection: keep-alive
Content-Length: %d
Content-Type: multipart/form-data; boundary=-boundary

"""

multipart_template = """---boundary
Content-Disposition: form-data; name="project"

fakeproduct
---boundary
Content-Disposition: form-data; name="uploadfile"; filename="simplefile.txt"
Content-Type: text/plain

%s
---boundary
Content-Disposition: form-data; name="fieldname"

uploadfile
---boundary--
"""

multipart_environ = {
    'CONTENT_TYPE':     'multipart/form-data; boundary=-boundary',
    'REQUEST_METHOD':   'POST',
    'QUERY_STRING':     '',
}

class TestFileUploader(unittest.TestCase):
    def setUp(self):
        self.wkdir = tempfile.mkdtemp()
    def tearDown(self):
        conary.lib.util.rmtree(self.wkdir)

    def test_it(self):
        fup = whizzyupload.fileuploader(self.wkdir, 'field')

        self.assertEquals(fup.manifestfile, os.path.join(self.wkdir, 'field-index'))
        self.assertEquals(fup.statusfile, os.path.join(self.wkdir, 'field-status'))
        self.assertEquals(fup.metadatafile, os.path.join(self.wkdir, 'field-meta_data'))

    def test_parseManifest(self):
        #create a workdir
        fup = whizzyupload.fileuploader(self.wkdir, 'field')

        i = open(fup.manifestfile, 'wt')
        i.write("""fieldname=uploadfile
tempfile=garbage.txt
somethingnumeric=23939
""")
        i.close()

        self.assertEquals(fup.parseManifest(),
            {
                'fieldname': 'uploadfile',
                'tempfile': 'garbage.txt',
                'somethingnumeric': 23939,
            })

    def _baseCancelUpload(self):
        fup = whizzyupload.fileuploader(self.wkdir, 'field')

        i = open(fup.metadatafile, 'wt')
        i.write("""pid=23939""")
        i.close()

        fd, fn = tempfile.mkstemp(prefix='field-', dir=self.wkdir)
        os.close(fd)
        return fup, fn

    def test_cancelUpload(self):
        oldkill = os.kill
        self.killed = []
        def fake_kill(x, y):
            self.killed.append((x,y))
        os.kill = fake_kill
        try:
            fup, fn = self._baseCancelUpload()
            fup.cancelUpload()
            #Check that everything got done
            self.assertEquals(self.killed, [(23939, signal.SIGUSR1)])
            assert not os.path.isfile(fn)
            assert not os.path.isfile(fup.manifestfile)

            #now do it again with a manifest
            self.killed = []
            fup, fn = self._baseCancelUpload()
            i = open(fup.manifestfile, 'wt')
            i.write('garbage=garbage')
            i.close()
            fup.cancelUpload()
            #Check that everything got done
            self.assertEquals(self.killed, [])
            assert not os.path.isfile(fn)
            assert not os.path.isfile(fup.manifestfile)

            #make sure there's nothing in wkdir
            self.assertEquals(os.listdir(self.wkdir), [], "error, wkdir is not empty")
        finally:
            os.kill = oldkill

class TestWhizzyUpload(unittest.TestCase):
    def setUp(self):
        #Need a workdir
        self.wkdir = tempfile.mkdtemp()

    def tearDown(self):
        conary.lib.util.rmtree(self.wkdir)

    def testReadline(self):
        #Set up a writer
        f = StringIO('''line1
line2
%s''' % ('A'*56))
        ofn = os.path.join(self.wkdir, 'status')
        o = open(ofn, 'wb')

        fwrap =whizzyupload.ProgressFileObject(f, o, 2)

        l = fwrap.buffered_readline()
        self.assertEquals('line1\n', l)
        self.assertEquals(whizzyupload.readStatus(ofn), 0)
        fwrap.buffer_reset()
        
        #The next read should be the same as the buffered
        self.assertEquals(fwrap.readline(), 'line1\n')
        self.assertEquals(whizzyupload.readStatus(ofn), 6)
        self.assertEquals(fwrap.readline(3), 'lin')
        self.assertEquals(whizzyupload.readStatus(ofn), 9)
        self.assertEquals(fwrap.readline(), 'e2\n')
        self.assertEquals(whizzyupload.readStatus(ofn), 12)
        self.assertEquals(fwrap.readline(), 'A'*56)
        self.assertEquals(whizzyupload.readStatus(ofn), 68)

    def testStdinWrapper(self):
        #Set up a writer
        f = open('/dev/zero', 'rb')
        ofn = os.path.join(self.wkdir, 'status')
        o = open(ofn, 'wb')

        fwrap = whizzyupload.ProgressFileObject(f, o, 2)
        self.assertEquals(fwrap.read(6), '\x00\x00\x00\x00\x00\x00')

        read = whizzyupload.readStatus(ofn)
        self.assertEquals(read, 6, "Status file reports a different size than expected")

        statusfileconts = open(ofn, 'rb').read()
        self.assertEquals(statusfileconts, '\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x06')

        fwrap.close()
        assert f.closed, 'fwrap.close() should have closed the wrapped fileobj'

    def testPollStatus(self):
        fup = whizzyupload.fileuploader(self.wkdir, 'file')
        info = fup.pollStatus()
        assert info['currenttime']
        del info['currenttime']
        self.assertEquals(info, {'read': 0, 'finished': {}})

        input = StringIO("a" * 200)
        o = open(fup.statusfile, 'wb')
        fwrap = whizzyupload.ProgressFileObject(input, o, 2)

        m = open(fup.metadatafile, 'wt')
        whizzyupload.writeMetadata(m, 200)

        #Get initial status
        info = fup.pollStatus()
        assert info['currenttime']
        assert info['starttime']
        starttime = info['starttime']
        del info['starttime']
        del info['currenttime']
        self.assertEquals(info, {'read': 0, 'finished': {}, 'pid': os.getpid(), 'totalsize': 200})

        #Read some, and recheck the status
        self.assertEquals('a'*100, fwrap.read(100))
        info = fup.pollStatus()
        assert info['currenttime']
        del info['currenttime']
        self.assertEquals(info, {'read': 100, 'finished': {}, 'pid': os.getpid(), 'totalsize': 200, 'starttime': starttime})

        #read to the end
        self.assertEquals('a'*100, fwrap.read(100))
        info = fup.pollStatus()
        assert info['currenttime']
        del info['currenttime']
        self.assertEquals(info, {'read': 200, 'finished': {}, 'pid': os.getpid(), 'totalsize': 200, 'starttime': starttime})

        #Now write the manifest
        i = open(fup.manifestfile, 'wt')
        i.write("""fieldname=uploadfile
tempfile=garbage.txt
somethingnumeric=23939
""")
        i.close()
        info = fup.pollStatus()
        assert info['currenttime']
        del info['currenttime']
        self.assertEquals(info, {'read': 200, 'finished': {'fieldname': 'uploadfile', 'tempfile': 'garbage.txt', 'somethingnumeric': 23939}, 'pid': os.getpid(), 'totalsize': 200, 'starttime': starttime})

    def get_fieldstorage(self, data):
        sin = multipart_template % data
        env = dict(multipart_environ)
        env['CONTENT_LENGTH'] = str(len(sin))
        headers = multipart_headers_template % len(sin)

        stdin = StringIO(headers + sin)
        stdin.seek(0)

        ufs = whizzyupload.genUploadFieldStorage(self.wkdir)
        fs = ufs(fp=stdin, environ=env)
        return fs

    def testFieldStorage(self):
        fs = self.get_fieldstorage('abc' * 50)
        uploadfs = fs['uploadfile']
        #We don't expect to have a file for data this small
        self.assertEquals(uploadfs.filen, None, "Did not expect a file to have been created")

        self.assertEquals('abc' * 50, uploadfs.value)
        uploadfs.flush_to_file()
        assert uploadfs.filen.startswith(self.wkdir), "Flushed file %s not in %s" % (uploadfs.filen, self.wkdir)

        self.assertEquals('abc' * 50, open(uploadfs.filen, 'rb').read())

        self.assertEquals('abc' * 50, uploadfs.value)

    def testLargeFieldStorage(self):
        refdata = 'abc' * 1024
        fs = self.get_fieldstorage(refdata)

        uploadfs = fs['uploadfile']
        assert uploadfs.filen, "Expected that a file would have been created"

class TestWhizzyCGI(unittest.TestCase):
    def setUp(self):
        #Need a workdir
        self.prefix='tmp-testWhizzy-CGI-'
        self.wkdir = tempfile.mkdtemp(prefix=self.prefix)
        self.basedir = os.path.dirname(self.wkdir)
        self.id = os.path.basename(self.wkdir).replace(self.prefix, '')
        #TODO Use a fileuploader here
        self.status,self.metadata,self.manifest = [os.path.join(self.wkdir, 'uploadfile-%s' % x) for x in ['status', 'meta_data', 'index']]

    def tearDown(self):
        conary.lib.util.rmtree(self.wkdir)

    def get_cgi_context(self, data):
        sin = multipart_template % data
        env = dict(multipart_environ)
        env['CONTENT_LENGTH'] = str(len(sin))
        env['QUERY_STRING'] = 'id=%s;fieldname=uploadfile' % self.id
        headers = multipart_headers_template % len(sin)

        stdin = StringIO(headers + sin)
        stdin.seek(0)

        stdout = StringIO('')
        stdout.seek(0)

        return stdin, stdout, env

    def testCgiHandler_badRequest(self):
        filedata = "line\n" * 40
        stdin, stdout, env = self.get_cgi_context(filedata)
        env['QUERY_STRING'] = ''

        whizzyupload.handle_cgi_request(stdin, stdout, self.basedir, self.prefix, env)
        self.assertEquals(stdout.getvalue(), 'Content-Type: text/html\nStatus: 400 Bad request\n\nInvalid request, id and fieldname must be specified in the query string\n')

        env['QUERY_STRING'] = 'id=%s' % self.id
        stdin.seek(0)
        stdout.seek(0)
        whizzyupload.handle_cgi_request(stdin, stdout, self.basedir, self.prefix, env)
        self.assertEquals(stdout.getvalue(), 'Content-Type: text/html\nStatus: 400 Bad request\n\nInvalid request, id and fieldname must be specified in the query string\n')

    def testCgiHandler(self):
        filedata = "line\n" * 40
        stdin, stdout, env = self.get_cgi_context(filedata)

        whizzyupload.handle_cgi_request(stdin, stdout, self.basedir, self.prefix, env)

        r = whizzyupload.pollStatus(self.metadata, self.status, self.manifest)
        self.assertEquals(r['read'], int(r['totalsize']))
        self.assertEquals(r['read'], len(stdin.getvalue()))
        assert r['pid'], "Should have had a pid in the status"
        assert r['currenttime'], "Should have had the current time in the status"
        assert r['starttime'], "Should have had the start time in the status"
        assert r['finished']['tempfile'], "No tempfile created"
        self.assertEquals(r['finished']['filename'], 'simplefile.txt')
        self.assertEquals(r['finished']['fieldname'], 'uploadfile')
        self.assertEquals(r['finished']['content-type'], 'text/plain')

        #Check to ensure that the status file is always increasing
        f = open(self.status, 'rb')
        lastread = -1
        while True:
            d = f.read(8)
            if not d:
                break
            p = struct.unpack("!Q", d)
            assert p > lastread, 'The status file is malformed'
            lastread = p
