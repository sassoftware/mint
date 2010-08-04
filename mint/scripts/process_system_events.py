#!/usr/bin/python
#
# Copyright (c) 2010 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
"""
This script can be used to check for and handle current system inventory events
"""

import sys

from mint import config
from mint.lib import scriptlibrary

class ProcessSystemEvents(scriptlibrary.SingletonScript):
    cfgPath = config.RBUILDER_CONFIG
    logFileName = 'scripts.log'
    newLogger = True
    
    def run(self):        
        if sys.argv[0].startswith('--xyzzy='):
            self.cfgPath = sys.argv.pop(0).split('=')[1]
            print "Test mode using configuration from %s" % self.cfgPath
        #elif os.getuid():
        #    sys.exit("This script must be run as root")
    
#        if len(sys.argv) > 1 and sys.argv[1] == 'useLocalSettings':
#            try:
#                from mint.django_rest import settings_local
#                execute_manager(settings_local)
#            except ImportError:
#                sys.exit("Error: Can't find the file 'settings_local.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
#        else:
#            try:
#                from mint.django_rest import settings
#                execute_manager(settings)
#            except ImportError:
#                sys.exit("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
                
        from mint.django_rest.rbuilder.inventory import systemdbmgr
        system_manager = systemdbmgr.SystemDBManager()
        system_manager.processSystemEvents()
        
    def usage(self):
        print >> sys.stderr, "Usage: %s [useLocalSettings]" % \
            sys.argv[0]
        sys.stderr.flush()
        sys.exit(1)
    
