#
# Copyright (c) 2005-2007 rPath, Inc.
# All Rights Reserved
#
# copytree utility functions with callback reporting support.
#
from conary.lib import util, log

import os
import shutil


def _copytree(src, dst, symlinks=False, callback = None):
    names = os.listdir(src)
    os.mkdir(dst)
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                _copytree(srcname, dstname, symlinks, callback = callback)
            else:
                shutil.copy2(srcname, dstname)
                if callback:
                    callback(1)
        except (IOError, os.error), why:
            errors.append((srcname, dstname, why))
    if errors:
        raise shutil.Error, errors


def _copyVisit(arg, dirname, names):
    sourcelist = arg[0]
    sourcelen = arg[1]
    dest = arg[2]
    filemode = arg[3]
    dirmode = arg[4]
    if dirmode:
        os.chmod(dirname, dirmode)
    for name in names:
        if filemode:
            os.chmod(dirname+os.sep+name, filemode)
        sourcelist.append(os.path.normpath(
            dest + os.sep + dirname[sourcelen:] + os.sep + name))

def copytree(sources, dest, symlinks=False, filemode=None, dirmode=None, callback = None):
    """
    Copies tree(s) from sources to dest, returning a list of
    the filenames that it has written.
    """
    sourcelist = []
    totalFiles = 0
    for source in util.braceGlob(sources):
        if os.path.isdir(source):
            if source[-1] == '/':
                source = source[:-1]
            thisdest = '%s%s%s' %(dest, os.sep, os.path.basename(source))
            log.debug('copying [tree] %s to %s', source, thisdest)
            _copytree(source, thisdest, symlinks, callback = callback)
            if dirmode:
                os.chmod(thisdest, dirmode)
            os.path.walk(source, _copyVisit,
                         (sourcelist, len(source), thisdest, filemode, dirmode))
        else:
            log.debug('copying [file] %s to %s', source, dest)
            shutil.copy2(source, dest)
            totalFiles += 1
            if callback:
                callback(totalFiles)

            if dest.endswith(os.sep):
                thisdest = dest + os.sep + os.path.basename(source)
            else:
                thisdest = dest
            if filemode:
                os.chmod(thisdest, filemode)
            sourcelist.append(thisdest)
    return sourcelist
