#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

import os

from mint import mint_error

# the length of the maintenanceLockPath file is used as the maintenance mode
# as defined below. no file equates to a length of zero.
# the reason for this is that an os.stat is far cheaper than opening a file
# descriptor, and this function will potentially be called thousands of times
# per second.

NORMAL_MODE  = 0
LOCKED_MODE  = 1

# client side
def getMaintenanceMode(cfg):
    if os.path.exists(cfg.maintenanceLockPath):
        return os.stat(cfg.maintenanceLockPath).st_size
    else:
        return NORMAL_MODE

# call this thru xmlrpc only. must verify admin rights.
def setMaintenanceMode(cfg, maintMode):
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

def enforceMaintenanceMode(cfg, auth = None, msg = None):
    e = msg and mint_error.MaintenanceMode(msg) or mint_error.MaintenanceMode
    mode = getMaintenanceMode(cfg)
    if mode == NORMAL_MODE:
        return
    if auth is None:
        raise e
    if not auth.admin:
        raise e
