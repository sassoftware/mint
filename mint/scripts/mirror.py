#
# Copyright (c) 2005-2007, 2009 rPath, Inc.
#
# All Rights Reserved
#

import logging
import optparse
import os
import sys

from mint import config
from mint.lib import scriptlibrary

log = logging.getLogger(__name__)

EXCLUDE_SOURCE_MATCH_TROVES = ["-.*:source", "-.*:debuginfo"]
INCLUDE_ALL_MATCH_TROVES = ["+.*"]

class MirrorScript(scriptlibrary.SingletonScript):
    cfgPath = config.RBUILDER_CONFIG
    logFileName = None
    newLogger = True

    options = None
    args = None

    def handle_args(self):
        usage = "%prog [options]"
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
        # read the configuration
        cfg = config.MintConfig()
        if self.options.cfgPath:
            cfg.read(self.options.cfgPath)
        else:
            cfg.read(self.cfgPath)
        self.setConfig(cfg)
        if self.args:
            self.mintUrl = self.args[0]
        else:
            self.mintUrl = 'http://%s:%s@localhost/xmlrpc-private/' % (
                    cfg.authUser, cfg.authPass)
        return True

    def _doMirror(self, mirrorCfg, sourceRepos, targetRepos, fullSync = False):

        from conary.conaryclient import mirror
        from conary.lib import util

        # set the correct tmpdir to use
        tmpDir = os.path.join(self.cfg.dataPath, 'tmp')
        if os.access(tmpDir, os.W_OK):
            util.settempdir(tmpDir)
            log.info("Using %s as tmpDir", tmpDir)
        else:
            log.warning("Using system temporary directory")

        fullSync = self.options.sync or fullSync
        if fullSync:
            log.info("Full sync requested on this mirror")
        if self.options.syncSigs:
            log.info("Full signature sync requested on this mirror")

        # first time through, we should pass in sync options;
        # subsequent passes should use the mirror marks
        passNumber = 1

        if self.options.test:
            # If we are testing, print the configuration
            if not self.options.showConfig:
                log.info("--test implies --show-config")
                self.options.showConfig = True

        if self.options.showConfig:
            print >> sys.stdout, "-- Start Mirror Configuration File --"
            mirrorCfg.display()
            print >> sys.stdout, "-- End Mirror Configuration File --"
            sys.stdout.flush()

        if self.options.test:
            log.info("Testing mode, not actually mirroring")
            return

        log.info("Beginning pass %d", passNumber)
        callAgain = mirror.mirrorRepository(sourceRepos, targetRepos,
            mirrorCfg, sync = self.options.sync or fullSync,
            syncSigs = self.options.syncSigs)
        log.info("Completed pass %d", passNumber)

        while callAgain:
            passNumber += 1
            log.info("Beginning pass %d", passNumber)
            callAgain = mirror.mirrorRepository(sourceRepos,
                targetRepos, mirrorCfg)
            log.info("Completed pass %d", passNumber)
