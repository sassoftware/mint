#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
from mint import config
from mint import database
from mint import scriptlibrary

import os
import sys
import optparse
import traceback

EXCLUDE_SOURCE_MATCH_TROVES = ["-.*:source", "-.*:debuginfo", "+.*"]

class InboundMirrorsTable(database.KeyedTable):
    name = 'InboundMirrors'
    key = 'inboundMirrorId'

    fields = ['inboundMirrorId', 'targetProjectId', 'sourceLabels',
              'sourceUrls', 'sourceAuthType', 'sourceUsername',
              'sourcePassword', 'sourceEntitlement',
              'mirrorOrder', 'allLabels']

class OutboundMirrorsTable(database.KeyedTable):
    name = 'OutboundMirrors'
    key = 'outboundMirrorId'

    fields = ['outboundMirrorId', 'sourceProjectId', 'targetLabels',
              'allLabels', 'recurse', 'matchStrings', 'mirrorOrder']

    def get(self, *args, **kwargs):
        res = database.KeyedTable.get(self, *args, **kwargs)
        if 'allLabels' in res:
            res['allLabels'] = bool(res['allLabels'])
        if 'recurse' in res:
            res['recurse'] = bool(res['recurse'])
        return res


class OutboundMirrorTargetsTable(database.KeyedTable):
    name = "OutboundMirrorTargets"
    key = 'outboundMirrorTargetsId'

    fields = [ 'outboundMirrorTargetsId', 'outboundMirrorId',
               'url', 'username', 'password' ]


class RepNameMapTable(database.DatabaseTable):
    name = "RepNameMap"

    fields = ['fromName', 'toName']

    def new(self, fromName, toName):
        cu = self.db.cursor()

        cu.execute("INSERT INTO RepNameMap VALUES (?, ?)", fromName, toName)
        self.db.commit()
        return cu._cursor.lastrowid


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

    def logTraceback(self):
        tb = traceback.format_exc()
        [self.log.error(x) for x in tb.split("\n") if x.strip()]

    def _doMirror(self, mirrorCfg, sourceRepos, targetRepos):

        from conary.conaryclient import mirror
        from conary.lib import util

        if self.options.showConfig:
            print >> sys.stdout, "-- Start Mirror Configuration File --"
            mirrorCfg.display()
            print >> sys.stdout, "-- End Mirror Configuration File --"
            sys.stdout.flush()

        # set the correct tmpdir to use
        tmpDir = os.path.join(self.cfg.dataPath, 'tmp')
        if os.access(tmpDir, os.W_OK):
            util.settempdir(tmpDir)
            self.log.info("Using %s as tmpDir" % tmpDir)
        else:
            self.log.warning("Using system temporary directory")

        # first time through, we should pass in sync options;
        # subsequent passes should use the mirror marks
        passNumber = 1
        self.log.info("Beginning pass %d" % passNumber)
        callAgain = mirror.mirrorRepository(sourceRepos, targetRepos,
            mirrorCfg, sync = self.options.sync,
            syncSigs = self.options.syncSigs)
        self.log.info("Completed pass %d" % passNumber)

        while callAgain:
            passNumber += 1
            self.log.info("Beginning pass %d" % passNumber)
            callAgain = mirror.mirrorRepository(sourceRepos,
                targetRepos, mirrorCfg)
            self.log.info("Completed pass %d" % passNumber)
