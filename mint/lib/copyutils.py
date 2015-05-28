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

"""
copytree utility functions with callback reporting support.
"""


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
    fileowner = arg[5]
    dirowner = arg[6]
    if dirmode:
        os.chmod(dirname, dirmode)
    if dirowner:
        os.chown(dirname, *dirowner)
    for name in names:
        if filemode:
            os.chmod(dirname+os.sep+name, filemode)
        if fileowner:
            os.chown(dirname+os.sep+name, *fileowner)
        sourcelist.append(os.path.normpath(
            dest + os.sep + dirname[sourcelen:] + os.sep + name))

def copytree(sources, dest, symlinks=False,
        filemode=None, dirmode=None,
        fileowner=None, dirowner=None,
        callback = None):
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
            if dirowner:
                os.chown(thisdest, *dirowner)
            os.path.walk(source, _copyVisit,
                         (sourcelist, len(source), thisdest, filemode, dirmode, fileowner, dirowner))
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
            if fileowner:
                os.chown(thisdest, *fileowner)
            sourcelist.append(thisdest)
    return sourcelist
