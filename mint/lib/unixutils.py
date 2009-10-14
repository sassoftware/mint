#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

import errno
import os
import tempfile


class AtomicFile(object):
    """
    Open a temporary file adjacent to C{path} for writing. When
    C{f.commit()} is called, the temporary file will be flushed and
    renamed on top of C{path}, constituting an atomic file write.
    """

    fObj = None

    def __init__(self, path, mode='w+b', chmod=0644, **kwargs):
        self.finalPath = os.path.realpath(path)
        self.finalMode = chmod

        kwargs.setdefault('dir', os.path.dirname(self.finalPath))
        fDesc, self.name = tempfile.mkstemp(**kwargs)
        self.fObj = os.fdopen(fDesc, mode)

    def __getattr__(self, name):
        return getattr(self.fObj, name)

    def commit(self, sync=True):
        """
        C{flush()}, C{chmod()}, and C{rename()} to the target path.
        C{close()} afterwards.
        """
        if self.fObj.closed:
            raise RuntimeError("Can't commit a closed file")

        # Flush and change permissions before renaming so the contents
        # are immediately present and accessible.
        self.fObj.flush()
        os.chmod(self.name, self.finalMode)
        if sync:
            os.fsync(self.fObj)

        # Rename to the new location. Since both are on the same
        # filesystem, this will atomically replace the old with the new.
        os.rename(self.name, self.finalPath)

        # Hash file
        hash = hashFile(self.fObj)

        # Now close the file.
        self.fObj.close()

        return hash

    def close(self):
        if self.fObj and not self.fObj.closed:
            os.unlink(self.name)
            self.fObj.close()
    __del__ = close

atomicOpen = AtomicFile


def hashFile(path, missingOk=False, inodeOnly=False):
    """
    Return a hash of the metadata for C{path}, sufficient to distinguish
    whether a file has been modified or replaced.

    Hashes these items:
     * device number
     * inode number
     * file size
     * mtime (time of modification)
     * ctime (time of last metadata change e.g. creation or renaming)

    C{path} may also be a file descriptor or file-like object supporting
    C{fileno()}, in which case a C{fstat()} call is used to determine
    the metadata of the given open file. This is especially useful in
    combination with C{missingOk} and C{inodeOnly} to enable automatic
    log rotation -- if the hash of the file descriptor differs from
    the hash of the file on disk, then the log has been rotated and the
    file handle should be re-opened to begin writing to the new file.

    @param path: Path of the file to hash
    @type  path: C{basestring} or file-like object or file descriptor
    @param missingOk: If C{True}, return C{None} if the file is missing.
    @type  missingOk: C{bool}
    @param inodeOnly: If C{True}, hash only C{st_dev} and C{st_inode}. The
                        hash will distinguish whether the file has been
                        replaced, but not if it has been modified in-place.
    @type  inodeOnly: C{bool}
    @returns: Hash of C{path}'s metadata
    @rtype: C{int}
    """
    try:
        if isinstance(path, basestring):
            # Path
            stat = os.stat(path)
        else:
            # File descriptor or file-like object
            if hasattr(path, 'fileno'):
                path = path.fileno()
            elif not isinstance(path, (int, long)):
                raise RuntimeError("Expected a path, file descriptor, or "
                        "fileno()-capable object")
            stat = os.fstat(path)
    except OSError, err:
        if err.args[0] == errno.ENOENT:
            # No such file or directory
            if missingOk:
                return None
        raise

    items = (stat.st_dev, stat.st_ino)
    if not inodeOnly:
        items += (stat.st_size, stat.st_mtime, stat.st_ctime)
    return hash(items)
