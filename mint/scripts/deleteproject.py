#!/usr/bin/python
import os
import sys
import traceback

from conary import conarycfg

from mint import config
from mint import mint_error
from mint import helperfuncs
from mint.lib import scriptlibrary
from mint import shimclient

class DeleteProject(scriptlibrary.SingletonScript):
    cfgPath = config.RBUILDER_CONFIG
    logFileName = 'scripts.log'
    newLogger = True
    
    def run(self):
        args = sys.argv[1:]
        if not args:
            self.usage()
        
        if args[0].startswith('--xyzzy='):
            self.cfgPath = args.pop(0).split('=')[1]
            print "Test mode using configuration from %s" % self.cfgPath
        elif os.getuid():
            sys.exit("This script must be run as root")

        # make sure they want to do it
        if '--force' in args:
            args.remove('--force')
        else:
            self.confirm(args)
        
        mintConfig = config.getConfig(self.cfgPath)
        self.setConfig(mintConfig)

        mintClient = shimclient.ShimMintClient(mintConfig,
                (mintConfig.authUser, mintConfig.authPass))

        for projectName in args:
            print "Deleting '" + projectName + "'..."
            mintClient.deleteProjectByName(projectName)
        
    def usage(self):
        print >> sys.stderr, "Usage: %s project [project] [project] ..." % \
            sys.argv[0]
        print >> sys.stderr, "Each project is referred to by short name only"
        print >> sys.stderr, '(i.e. use "rpath" instead of "rPath Linux").'
        sys.stderr.flush()
        sys.exit(1)
        
    def confirm(self, args):
        print "Executing this script will completely eradicate the following Projects:"
        print '\n'.join(args)
        print "If you do not have backups, it will be impossible to recover from this."
        print "are you ABSOLUTELY SURE you want to do this? [yes/N]"
        answer = sys.stdin.readline()[:-1]
        if answer.upper() != 'YES':
            if answer.upper() not in ('', 'N', 'NO'):
                print >> sys.stderr, "you must type 'yes' if you truly want to delete",
                print >> sys.stderr, "these projects."
            sys.exit("Aborting.")
