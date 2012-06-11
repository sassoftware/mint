#!/usr/bin/env python

import sys

from django.core.management import execute_manager

def run():
    print 'using settings.py...'
    try:
        import settings # Assumed to be in the same directory.
        execute_manager(settings)
    except ImportError:
        sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
        sys.exit(1)

if __name__ == "__main__":
    sys.path.insert(0, '../../../include')
    if len(sys.argv) > 1 and sys.argv[1] == 'useLocalSettings':
        import manage_local
        sys.argv.pop(0) # strip off useLocalSettings param
        manage_local.run()
    else:
        run()
    
