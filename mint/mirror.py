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
    createSQL= """CREATE TABLE InboundMirrors (
        inboundMirrorId %(PRIMARYKEY)s,
        targetProjectId INT NOT NULL,
        sourceLabels    VARCHAR(767) NOT NULL,
        sourceUrl       VARCHAR(767) NOT NULL,
        sourceUsername  VARCHAR(254),
        sourcePassword  VARCHAR(254),
        mirrorOrder     INT DEFAULT 0,
        allLabels       INT DEFAULT 0,
        CONSTRAINT InboundMirrors_targetProjectId_fk
            FOREIGN KEY (targetProjectId) REFERENCES Projects(projectId)
            ON DELETE CASCADE ON UPDATE CASCADE
    ) %(TABLEOPTS)s"""

    fields = ['inboundMirrorId', 'targetProjectId', 'sourceLabels',
              'sourceUrls', 'sourceUsername', 'sourcePassword',
              'mirrorOrder', 'allLabels']

    indexes = {'InboundMirrorsProjectIdIdx': """CREATE INDEX InboundMirrorsProjectIdIdx ON InboundMirrors(targetProjectId)"""}

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            cu = self.db.cursor()
            if dbversion == 24:
                cu.execute("""INSERT INTO InboundMirrors (targetProjectId,
                    sourceLabels, sourceUrl, sourceUsername, sourcePassword)
                   SELECT il.projectId AS targetProjectId,
                          l.label AS sourceLabels,
                          il.url AS sourceUrl,
                          il.username AS sourceUsername,
                          il.password AS sourcePassword
                   FROM InboundLabels il JOIN labels l USING (labelId)""")
                cu.execute("""DROP TABLE InboundLabels""")
            if dbversion == 30 and not self.initialCreation:
                cu.execute("ALTER TABLE InboundMirrors ADD COLUMN mirrorOrder INT DEFAULT 0")
            if dbversion == 31 and not self.initialCreation:
                cu.execute("ALTER TABLE InboundMirrors ADD COLUMN allLabels INT DEFAULT 0")
            return dbversion >= 31

        return True

class OutboundMirrorsTable(database.KeyedTable):
    name = 'OutboundMirrors'
    key = 'outboundMirrorId'
    createSQL= """CREATE TABLE OutboundMirrors (
        outboundMirrorId %(PRIMARYKEY)s,
        sourceProjectId  INT NOT NULL,
        targetLabels     VARCHAR(767) NOT NULL,
        allLabels        INT NOT NULL DEFAULT 0,
        recurse          INT NOT NULL DEFAULT 0,
        matchStrings     VARCHAR(767) NOT NULL DEFAULT '',
        mirrorOrder      INT DEFAULT 0,
        CONSTRAINT OutboundMirrors_sourceProjectId_fk
            FOREIGN KEY (sourceProjectId) REFERENCES Projects(projectId)
            ON DELETE CASCADE ON UPDATE CASCADE
    ) %(TABLEOPTS)s"""

    fields = ['outboundMirrorId', 'sourceProjectId', 'targetLabels',
              'allLabels', 'recurse', 'matchStrings', 'mirrorOrder']

    indexes = {'OutboundMirrorsProjectIdIdx': \
            """CREATE INDEX OutboundMirrorsProjectIdIdx
               ON OutboundMirrors(sourceProjectId)"""}

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            cu = self.db.cursor()
            if dbversion == 17:
                cu.execute("ALTER TABLE OutboundLabels ADD COLUMN allLabels INT DEFAULT 0")
            if dbversion == 18:
                cu.execute("ALTER TABLE OutboundLabels ADD COLUMN recurse INT DEFAULT 0")
            if dbversion == 24:
                cu.execute("""SELECT ol.labelId, ol.projectId, l.label, ol.url, ol.username, ol.password, ol.allLabels, ol.recurse FROM OutboundLabels ol JOIN Labels l USING (labelId)""")
                outboundLabels = cu.fetchall()
                cu.execute("""DROP TABLE OutboundLabels""")
                for ol in outboundLabels:
                    cu.execute("""INSERT INTO OutboundMirrors (sourceProjectId, targetLabels, targetUrl, targetUsername, targetPassword, allLabels, recurse) VALUES(?,?,?,?,?,?,?)""", *ol[1:])
                    outboundMirrorId = cu.lastrowid
                    cu.execute("""SELECT matchStr FROM OutboundMatchTroves WHERE projectId = ? AND labelId = ? ORDER BY idx ASC""", ol[1], ol[0])
                    matchStrings = ' '.join([x[0] for x in cu.fetchall()])
                    cu.execute("""UPDATE OutboundMirrors SET matchStrings = ? WHERE outboundMirrorId = ?""", matchStrings, outboundMirrorId)

                cu.execute("""DROP TABLE OutboundMatchTroves""")
            if dbversion == 30 and not self.initialCreation:
                cu.execute("ALTER TABLE OutboundMirrors ADD COLUMN mirrorOrder INT DEFAULT 0")
            if dbversion == 34 and not self.initialCreation:
                cu.execute("""SELECT outboundMirrorId, sourceProjectId,
                                     targetLabels, allLabels, recurse,
                                     matchStrings, mirrorOrder, targetUrl,
                                     targetUsername, targetPassword
                              FROM OutboundMirrors ORDER BY mirrorOrder ASC""")
                outboundMirrors = cu.fetchall()
                cu.execute("""DROP TABLE OutboundMirrors""")

                # Create the OutboundMirrors and OutboundMirrorTargets tables
                cu.execute(self.createSQL % self.db.keywords)
                omtTable = OutboundMirrorTargetsTable(self.db)
                del omtTable

                for om in outboundMirrors:
                    cu.execute("""INSERT INTO OutboundMirrors
                        (outboundMirrorId, sourceProjectId, targetLabels,
                         allLabels, recurse, matchStrings, mirrorOrder)
                         VALUES(?,?,?,?,?,?,?)""", *om[0:7])
                    cu.execute("""INSERT INTO OutboundMirrorTargets
                        (outboundMirrorId, url, username, password)
                        VALUES(?,?,?,?)""", om[0], *om[7:])
            return dbversion >= 34
        return True

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
    createSQL = """CREATE TABLE OutboundMirrorTargets (
        outboundMirrorTargetsId %(PRIMARYKEY)s,
        outboundMirrorId        INT NOT NULL,
        url                     VARCHAR(767) NOT NULL,
        username                VARCHAR(254) NOT NULL,
        password                VARCHAR(254) NOT NULL,
        CONSTRAINT OutboundMirrorTargets_omi_fk
            FOREIGN KEY (outboundMirrorId)
                REFERENCES OutboundMirrors(outboundMirrorId)
            ON DELETE CASCADE ON UPDATE CASCADE
    ) %(TABLEOPTS)s"""

    fields = [ 'outboundMirrorTargetsId', 'outboundMirrorId',
               'url', 'username', 'password' ]

    indexes = { 'outboundMirrorTargets_outboundMirrorIdIdx':
            """CREATE INDEX outboundMirrorTargets_outboundMirrorIdIdx
               ON OutboundMirrorTargets(outboundMirrorId)"""}


class RepNameMapTable(database.DatabaseTable):
    name = "RepNameMap"
    createSQL = """CREATE TABLE RepNameMap (
        fromName    VARCHAR(255),
        toName      VARCHAR(255),
        PRIMARY KEY(fromName, toName)
    ) %(TABLEOPTS)s"""

    fields = ['fromName', 'toName']
    indexes = {'RepNameMap_fromName_idx': \
               'CREATE INDEX RepNameMap_fromName_idx ON RepNameMap(fromName)'}

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
        self.cfg = config.MintConfig()
        self.cfg.read(self.cfgPath)
        if self.logFileName:
            self.logPath = os.path.join(self.cfg.dataPath, 'logs', self.logFileName)
        scriptlibrary.SingletonScript.__init__(self, aLockPath)

    def handle_args(self):
        usage = "%prog [options] rbuilder-xml-rpc-url"
        op = optparse.OptionParser(usage=usage)
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
