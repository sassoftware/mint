#
# Copyright (c) 2006 rPath, Inc.
#

import os
import re
from nagpy.plugin import NagiosPlugin
from nagpy.util.exceptionHooks import stdout_hook
from mint_nagpy.config import CheckJobsConfig

class CheckJS(NagiosPlugin):
    def __init__(self):
        NagiosPlugin.__init__(self)
        self.cfg = CheckJobsConfig()

    @stdout_hook
    def check(self):
        status = self.nagios_ok
        jsdirs = [x for x in os.listdir(self.cfg.jsPath) if os.path.isdir(os.path.join(self.cfg.jsPath, x))]
        for x in jsdirs:
            f = open(os.path.join(self.cfg.jsPath, x, self.cfg.jsConfig))
            conf = f.read()
            f.close()
            match = re.search('lockFile\s+(.+)\s*\n', conf)
            lockFile = match.groups()[0].lstrip('/')
            try:
                f = open(os.path.join(self.cfg.jsPath, x, lockFile))
            except IOError:
                if status == self.nagios_ok:
                    status = self.nagios_warning
            else:
                pid = f.read()
                f.close()
                fd = os.popen('ps -p %s -o comm=' % pid)	
                res = fd.read().strip()
                fd.close()
                if (res != 'job-server'):
                    status = self.nagios_critical
        return status
