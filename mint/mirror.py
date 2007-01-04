#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#
from mint import config
from mint import database
from mint import scriptlibrary

import os
import sys
import traceback

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
        CONSTRAINT InboundMirrors_targetProjectId_fk
            FOREIGN KEY (targetProjectId) REFERENCES Projects(projectId)
            ON DELETE CASCADE ON UPDATE CASCADE
    ) %(TABLEOPTS)s"""

    fields = ['inboundMirrorId', 'targetProjectId', 'sourceLabels',
              'sourceUrls', 'sourceUsername', 'sourcePassword']

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
            return dbversion >= 25
        return True

class OutboundMirrorsTable(database.KeyedTable):
    name = 'OutboundMirrors'
    key = 'outboundMirrorId'
    createSQL= """CREATE TABLE OutboundMirrors (
        outboundMirrorId %(PRIMARYKEY)s,
        sourceProjectId  INT NOT NULL,
        targetLabels     VARCHAR(767) NOT NULL,
        targetUrl        VARCHAR(767) NOT NULL,
        targetUsername   VARCHAR(254),
        targetPassword   VARCHAR(254),
        allLabels        INT NOT NULL DEFAULT 0,
        recurse          INT NOT NULL DEFAULT 0,
        matchStrings     VARCHAR(767) NOT NULL DEFAULT '',
        CONSTRAINT OutboundMirrors_sourceProjectId_fk
            FOREIGN KEY (sourceProjectId) REFERENCES Projects(projectId)
            ON DELETE CASCADE ON UPDATE CASCADE
    ) %(TABLEOPTS)s"""

    fields = ['outboundMirrorId', 'sourceProjectId', 'targetLabels',
              'targetUrl', 'targetUsername', 'targetPassword', 'allLabels',
              'recurse', 'matchStrings']

    indexes = {'OutboundMirrorsProjectIdIdx': """CREATE INDEX OutboundMirrorsProjectIdIdx ON OutboundMirrors(sourceProjectId)"""}

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
            return dbversion >= 25
        return True

    def get(self, *args, **kwargs):
        res = database.KeyedTable.get(self, *args, **kwargs)
        if 'allLabels' in res:
            res['allLabels'] = bool(res['allLabels'])
        if 'recurse' in res:
            res['recurse'] = bool(res['recurse'])
        return res

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

    def __init__(self, aLockPath = scriptlibrary.DEFAULT_LOCKPATH):
        self.cfg = config.MintConfig()
        self.cfg.read(self.cfgPath)
        if self.logFileName:
            self.logPath = os.path.join(self.cfg.dataPath, 'logs', self.logFileName)
        scriptlibrary.SingletonScript.__init__(self, aLockPath)

    def handle_args(self):
        if len(sys.argv) < 2:
            return False
        return True

    def usage(self):
        print "usage: %s <url to rBuilder server>" % self.name
        return 1

    def logTraceback(self):
        tb = traceback.format_exc()
        [self.log.error(x) for x in tb.split("\n") if x.strip()]
