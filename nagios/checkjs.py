#
# Copyright (c) 2006 rPath, Inc.
#

import os
import re
from nagpy.plugin import NagiosPlugin
from nagpy.util.exceptionHooks import stdout_hook

class CheckJS(NagiosPlugin):
    def __init__(self):
        NagiosPlugin.__init__(self)
        self.statusCmd = '/sbin/service multi-jobserver status'

    def getStatusMessage(self):
        fd = os.popen(self.statusCmd)
        res = fd.read()
        fd.close()
        return res
    
    @stdout_hook
    def check(self):
        res = self.getStatusMessage()
	status = self.nagios_ok
        for x in res.strip().split('\n'):
            if not re.search('is running\.$', x):
                status = self.nagios_critical
        return status
