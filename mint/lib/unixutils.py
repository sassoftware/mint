#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

import os
import tempfile


def atomicOpen(path, mode='w+b', chmod=0644):
    """
    Open a temporary file adjacent to C{path} for writing. When
    C{f.commit()} is called, the temporary file will be flushed and
    renamed on top of C{path}, constituting an atomic file write.
    """
    path = os.path.realpath(path)
    fObj = tempfile.NamedTemporaryFile(mode=mode,
            dir=os.path.dirname(path))
    fObj.finalPath = path
    fObj.finalMode = chmod

    def commit():
        """
        C{flush()}, C{chmod()}, and C{rename()} to the target path.
        C{close()} afterwards.
        """
        if fObj.closed:
            raise RuntimeError("Can't commit a closed file")

        # Flush and change permissions before renaming so the contents
        # are immediately present and accessible.
        fObj.flush()
        os.chmod(fObj.name, fObj.finalMode)
        os.fsync(fObj)

        # Rename to the new location. Since both are on the same
        # filesystem, this will atomically replace the old with the new.
        os.rename(fObj.name, fObj.finalPath)

        # Now close the file, but prevent it from being deleted.
        fObj.delete = False
        fObj.close()
    fObj.commit = commit

    return fObj
