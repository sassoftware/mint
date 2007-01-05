#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#

from conary.conarycfg import ConfigFile
from conary.lib import cfgtypes

class CheckJobsConfig(ConfigFile):
    # Stores the timestamp of the last check
    timeStampFile             = (cfgtypes.CfgString, '/srv/rbuilder/nagios/check-jobs.timestamp')
    iterationFile	      = (cfgtypes.CfgString, '/srv/rbuilder/nagios/check-jobs.iteration')
    # Maximum time a job is allowed to run, in seconds
    maxJobTime                = (cfgtypes.CfgInt, 21600)
    jsPath                    = (cfgtypes.CfgString, '/srv/rbuilder/jobserver/')
    jsConfig                  = (cfgtypes.CfgList(cfgtypes.CfgString))
    filterExp                 = (cfgtypes.CfgList(cfgtypes.CfgString))
    retries                   = (cfgtypes.CfgInt, 5)
    disabled                  = (cfgtypes.CfgBool, False)
