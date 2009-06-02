#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
from mint import config
from mint.lib import scriptlibrary

import os
import sys
import optparse
import traceback

EXCLUDE_SOURCE_MATCH_TROVES = ["-.*:source", "-.*:debuginfo"]
INCLUDE_ALL_MATCH_TROVES = ["+.*"]

class MirrorScript(scriptlibrary.SingletonScript):
    cfgPath = config.RBUILDER_CONFIG
    logFileName = None
    options = None
    args = None

    def __init__(self, aLockPath = scriptlibrary.DEFAULT_LOCKPATH):
        scriptlibrary.SingletonScript.__init__(self, aLockPath)

    def handle_args(self):
        usage = "%prog [options] rbuilder-xml-rpc-url"
        op = optparse.OptionParser(usage=usage)
        op.add_option("-c", "--rbuilder-config",
                dest = "cfgPath", default = None,
                help = "use a different configuration file")
        op.add_option("-v", "--verbose", action = "store_true",
                dest = "verbose", default = False,
                help = "show detailed mirroring output")
        op.add_option("--full-sig-sync", action = "store_true",
                dest = "syncSigs", default = False,
                help = "replace all of the trove signatures on the "
                       "target repository")
        op.add_option("--full-trove-sync", action = "store_true",
                dest = "sync", default = False,
                help = "ignore the last-mirrored timestamp in the "
                       "target repository")
        op.add_option("--show-mirror-cfg", action = "store_true",
                dest = "showConfig", default = False,
                help = "print generated mirror configs to stdout")
        op.add_option("--test", action = "store_true",
                dest = "test", default = False,
                help = "show how mirrorRepository would be called "
                       "(don't actually mirror)")
        (self.options, self.args) = op.parse_args()
        if len(self.args) < 1:
            op.error("missing URL to rBuilder XML-RPC interface")
            return False
        # read the configuration
        self.cfg = config.MintConfig()
        if self.options.cfgPath:
            self.cfg.read(self.options.cfgPath)
        else:
            self.cfg.read(self.cfgPath)
        if self.logFileName:
            self.logPath = os.path.join(self.cfg.logPath, self.logFileName)
        return True

    def _doMirror(self, mirrorCfg, sourceRepos, targetRepos, fullSync = False):

        from conary.conaryclient import mirror
        from conary.lib import util

        # set the correct tmpdir to use
        tmpDir = os.path.join(self.cfg.dataPath, 'tmp')
        if os.access(tmpDir, os.W_OK):
            util.settempdir(tmpDir)
            self.log.info("Using %s as tmpDir" % tmpDir)
        else:
            self.log.warning("Using system temporary directory")

        fullSync = self.options.sync or fullSync
        if fullSync:
            self.log.info("Full sync requested on this mirror")
        if self.options.syncSigs:
            self.log.info("Full signature sync requested on this mirror")

        # first time through, we should pass in sync options;
        # subsequent passes should use the mirror marks
        passNumber = 1

        if self.options.test:
            # If we are testing, print the configuration
            if not self.options.showConfig:
                self.log.info("--test implies --show-config")
                self.options.showConfig = True

        if self.options.showConfig:
            print >> sys.stdout, "-- Start Mirror Configuration File --"
            mirrorCfg.display()
            print >> sys.stdout, "-- End Mirror Configuration File --"
            sys.stdout.flush()

        if self.options.test:
            self.log.info("Testing mode, not actually mirroring")
            return

        self.log.info("Beginning pass %d" % passNumber)
        callAgain = mirror.mirrorRepository(sourceRepos, targetRepos,
            mirrorCfg, sync = self.options.sync or fullSync,
            syncSigs = self.options.syncSigs)
        self.log.info("Completed pass %d" % passNumber)

        while callAgain:
            passNumber += 1
            self.log.info("Beginning pass %d" % passNumber)
            callAgain = mirror.mirrorRepository(sourceRepos,
                targetRepos, mirrorCfg)
            self.log.info("Completed pass %d" % passNumber)
