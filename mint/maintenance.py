#
# Copyright (c) 2005-2007, 2009 rPath, Inc.
#
# All Rights Reserved
#

import errno
import os

from mint import mint_error

# the length of the maintenanceLockPath file is used as the maintenance mode
# as defined below. no file equates to a length of zero.
# the reason for this is that an os.stat is far cheaper than opening a file
# descriptor, and this function will potentially be called thousands of times
# per second.

NORMAL_MODE  = 0
LOCKED_MODE  = 1
EXPIRED_MODE = 2

# client side
def getMaintenanceMode(cfg):
    # check the maintmode file. A missing file is the same as
    # normal mode.
    try:
        st_result = os.stat(cfg.maintenanceLockPath)
    except OSError, err:
        if err.args[0] == errno.ENOENT:
            return NORMAL_MODE
        raise

    return st_result.st_size


# call this thru xmlrpc only. must verify admin rights.
def setMaintenanceMode(cfg, maintMode):
    assert maintMode != EXPIRED_MODE # comes from the siteauth xml, not here
    if maintMode == NORMAL_MODE:
        try:
            os.unlink(cfg.maintenanceLockPath)
        except OSError, e:
            if e.errno != 2:
                raise
    else:
        f = open(cfg.maintenanceLockPath, 'w')
        f.write(chr(0) * maintMode)
        f.close()

def enforceMaintenanceMode(cfg, auth = None, msg = None, skipExpired=False):
    mode = getMaintenanceMode(cfg)
    if mode == NORMAL_MODE:
        return
    elif mode == EXPIRED_MODE:
        if skipExpired:
            return
        raise mint_error.MaintenanceMode("The rBuilder's entitlement has expired. "
                "Please navigate to the rBuilder homepage for more information.")

    if auth is None or not auth.admin:
        if msg:
            raise mint_error.MaintenanceMode(msg)
        else:
            raise mint_error.MaintenanceMode()
