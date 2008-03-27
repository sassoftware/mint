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

from mint.mint_error import UpdateServiceNotFound

EXCLUDE_SOURCE_MATCH_TROVES = ["-.*:source", "-.*:debuginfo"]
INCLUDE_ALL_MATCH_TROVES = ["+.*"]

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

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.KeyedTable.__init__(self, db)

    def get(self, *args, **kwargs):
        res = database.KeyedTable.get(self, *args, **kwargs)
        if 'allLabels' in res:
            res['allLabels'] = bool(res['allLabels'])
        if 'recurse' in res:
            res['recurse'] = bool(res['recurse'])
        return res

    def delete(self, id):
        cu = self.db.transaction()
        try:
            cu.execute("""DELETE FROM OutboundMirrors WHERE
                              outboundMirrorId = ?""", id)

            # Cleanup mapping table ourselves if we are using SQLite,
            # as it doesn't know about contraints.
            if self.cfg.dbDriver == 'sqlite':
                cu.execute("""DELETE FROM OutboundMirrorsUpdateServices WHERE
                              outboundMirrorId = ?""", id)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
            return True

    def getOutboundMirrors(self):
        cu = self.db.cursor()
        cu.execute("""SELECT outboundMirrorId, sourceProjectId,
                        targetLabels, allLabels, recurse,
                        matchStrings, mirrorOrder, fullSync
                        FROM OutboundMirrors
                        ORDER by mirrorOrder""")
        return [list(x[:3]) + [bool(x[3]), bool(x[4]), x[5].split(), \
                x[6], bool(x[7])] \
                for x in cu.fetchall()]

class OutboundMirrorsUpdateServicesTable(database.DatabaseTable):
    name = "OutboundMirrorsUpdateServices"
    fields = [ 'updateServiceId', 'outboundMirrorId' ]

    def getOutboundMirrorTargets(self, outboundMirrorId):
        cu = self.db.cursor()
        cu.execute("""SELECT obus.updateServiceId, us.hostname,
                             us.mirrorUser, us.mirrorPassword, us.description
                      FROM OutboundMirrorsUpdateServices obus
                           JOIN
                           UpdateServices us
                           USING(updateServiceId)
                      WHERE outboundMirrorId = ?""", outboundMirrorId)
        return [ list(x) for x in cu.fetchall() ]

    def setTargets(self, outboundMirrorId, updateServiceIds):
        cu = self.db.transaction()
        updates = [ (outboundMirrorId, x) for x in updateServiceIds ]
        try:
            cu.execute("""DELETE FROM OutboundMirrorsUpdateServices
                          WHERE outboundMirrorId = ?""", outboundMirrorId)
        except:
            pass # don't worry if there is nothing to do here

        try:
            cu.executemany("INSERT INTO OutboundMirrorsUpdateServices VALUES(?,?)",
                updates)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
            return updateServiceIds

class RepNameMapTable(database.DatabaseTable):
    name = "RepNameMap"

    fields = ['fromName', 'toName']

    def new(self, fromName, toName):
        cu = self.db.cursor()

        cu.execute("INSERT INTO RepNameMap VALUES (?, ?)", fromName, toName)
        self.db.commit()
        return cu._cursor.lastrowid

class UpdateServicesTable(database.KeyedTable):
    name = 'UpdateServices'
    key = 'updateServiceId'
    fields = [ 'updateServiceId', 'hostname',
               'mirrorUser', 'mirrorPassword', 'description' ]

    def __init__(self, db, cfg):
        self.cfg = cfg
        database.KeyedTable.__init__(self, db)

    def getUpdateServiceList(self):
        cu = self.db.cursor()
        cu.execute("""SELECT %s FROM UpdateServices""" % ', '.join(self.fields))
        return [ list(x) for x in cu.fetchall() ]

    def delete(self, id):
        cu = self.db.transaction()
        try:
            cu.execute("""DELETE FROM UpdateServices WHERE
                              updateServiceId = ?""", id)

            # Cleanup mapping table ourselves if we are using SQLite,
            # as it doesn't know about contraints.
            if self.cfg.dbDriver == 'sqlite':
                cu.execute("""DELETE FROM OutboundMirrorsUpdateServices WHERE
                              updateServiceId = ?""", id)
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()
            return True


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

    def logTraceback(self):
        tb = traceback.format_exc()
        [self.log.error(x) for x in tb.split("\n") if x.strip()]

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
