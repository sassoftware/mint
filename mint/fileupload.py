#
# Copyright (C) 2008, rPath, Inc.
# All rights reserved
#

import os, signal, time, struct
import conary.lib.util

def _get_filename(templatename):
    def _wrapped_get_filename(self):
        return os.path.join(self.wkdir, getattr(self, templatename) % self.fieldname)
    return _wrapped_get_filename

def pollStatus(metafile, statusfile, manifestfile):
    info = dict()
    if os.path.isfile(metafile):
        info.update(parseMetadata(metafile))
    info['read'] = readStatus(statusfile)
    ctime = time.time()
    info['currenttime'] = ctime
    #The upload is finished when the manifest is written
    if os.path.isfile(manifestfile):
        manifest = parseManifest(manifestfile)
        info['finished'] = manifest
    else:
        info['finished'] = {}
    return info


class fileuploader(object):
    def __init__(self, wkdir, fieldname):
        self.wkdir = wkdir
        self.fieldname = fieldname

    manifest_template = '%s-index'
    status_template   = '%s-status'
    metadata_template = '%s-meta_data'

    manifestfile = property(fget = _get_filename('manifest_template'))
    statusfile = property(fget = _get_filename('status_template'))
    metadatafile = property(fget = _get_filename('metadata_template'))

    ### Poller section
    def parseManifest(self):
        return parseManifest(self.manifestfile)

    def pollStatus(self):
        return pollStatus(self.metadatafile, self.statusfile, self.manifestfile) 

    def cancelUpload(self):
        info = {}
        if os.path.isfile(self.metadatafile):
            info.update(parseMetadata(self.metadatafile))
        if not os.path.isfile(self.manifestfile):
            # kill the upload
            if info.get('pid', None) is not None:
                os.kill(int(info['pid']), signal.SIGUSR1)

        #Remove all the relevant files
        conary.lib.util.rmtree(os.path.join(self.wkdir, '%s-*' % self.fieldname))

def parseManifest(manifestfile):
    return _slurpFile(manifestfile)

def parseMetadata(metafile):
    return _slurpFile(metafile)

def readStatus(statusfile):
    ret = 0
    try:
        st = os.stat(statusfile)
        if st.st_size < 8:
            return 0
    except OSError:
        return 0
    f = open(statusfile, 'rb')
    f.seek(-8, 2) # seek to the last short in the file
    assert (f.tell() % 8) == 0

    b = f.read(8) # Read those last 8 bytes
    (ret, ) = struct.unpack("!Q", b)

    return ret

def _slurpFile(fn):
    #open the file, and read line by line, splitting on '='.  Create a dictionary of key-value pairs.
    ret = dict()
    f = open(fn, 'rt')
    for l in f.readlines():
        k, v = l.split('=')
        v = v.strip()
        try:
            v = int(v)
        except ValueError:
            pass
        ret[k] = v
    return ret


