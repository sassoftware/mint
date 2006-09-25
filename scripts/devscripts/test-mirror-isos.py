#!/usr/bin/python

from conary.lib import util
from conary import dbstore
import os, sys
import struct
import tempfile

def checkFiles(reposPath):
    db = dbstore.connect(os.path.join(reposPath, 'sqldb'), 'sqlite')
    contentsPath = os.path.join(reposPath, 'contents')
    cu = db.cursor()
    cu.execute('select distinct hex(sha1) from filestreams')
    missing = []
    for (sha,) in cu.fetchall():
        if not sha:
            continue
        splitSha = struct.unpack('2s2s36s', sha)
        if not os.path.exists(os.path.join(contentsPath, *splitSha)):
            missing.append(sha)
    db.close()
    return missing

def concatImages(images):
    tmpDir = tempfile.mkdtemp()
    mountPoint = tempfile.mkdtemp()
    try:
        p = os.popen('tar -x -C %s' % tmpDir, 'w')
        for image in images:
            os.system('sudo mount -o loop %s %s' % (image, mountPoint))
            for chunk in [x for x in os.listdir(mountPoint) if 'tar' in x and not x.endswith('sha1')]:
                print "chunk: %s" % chunk, chr(13),
                sys.stdout.flush()
                f = open(os.path.join(mountPoint, chunk))
                done = False
                while not done:
                    data = f.read(512)
                    done = not data
                    if not done:
                        p.write(data)
                f.close()
            os.system('sudo umount %s' % mountPoint)
        print checkFiles(tmpDir)
    finally:
        try:
            os.system('sudo umount %s' % mountPoint)
        except:
            pass
        for dir in (tmpDir, mountPoint):
            try:
                util.rmtree(dir)
            except:
                print >> sys.stderr, "warning, couldn't delete %s" % dir

if __name__ == '__main__':
    #print [(x, checkFiles(x)) for x in sys.argv[1:]]
    concatImages(sys.argv[1:])

