import sys
from mod_python import apache

class AdminHandler:
    def handle(self, cmd):
        print >> sys.stderr, cmd
        sys.stderr.flush()
        return apache.OK
