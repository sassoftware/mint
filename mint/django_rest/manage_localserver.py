#!/usr/bin/env python

import os
import sys
testutilsPath = os.environ.get('TESTUTILS_PATH', None)
if testutilsPath:
    sys.path.insert(0, testutilsPath)
sys.path.insert(0, '../../../include')

from django.core.management import execute_manager
try:
    import settings_localserver # Assumed to be in the same directory.
except ImportError, e:
    sys.stderr.write("Error: Can't find the file 'settings_local.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings_local module.\n(If the file settings_local.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.stderr.write(str(e))
    sys.stderr.write('\n')
    sys.exit(1)
    
def run():
    execute_manager(settings_localserver)

if __name__ == "__main__":
    run()
