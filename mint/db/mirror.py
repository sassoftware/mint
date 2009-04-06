#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
from mint.lib import database

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
              'allLabels', 'recurse', 'matchStrings', 'mirrorOrder',
              'useReleases',
              ]

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
                        matchStrings, mirrorOrder, fullSync,
                        useReleases
                        FROM OutboundMirrors
                        ORDER by mirrorOrder""")
        return [list(x[:3]) + [bool(x[3]), bool(x[4]), x[5].split(), \
                x[6], bool(x[7]), bool(x[8])] \
                for x in cu.fetchall()]
        
    def getOutboundMirrorByProject(self, projectId):
        cu = self.db.cursor()
        cu.execute("SELECT * FROM OutboundMirrors WHERE sourceProjectId=?", projectId)
        x = cu.fetchone_dict()
        if x:
            return x
        else:
            return {}

    def isProjectMirroredByRelease(self, projectId):
        cu = self.db.cursor()
        cu.execute("""SELECT COUNT(*) FROM OutboundMirrors
            WHERE sourceProjectId = ? AND useReleases = 1""", projectId)
        count = cu.fetchone()[0]
        return bool(count)

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
        return [ list(x[:4]) + [x[4] and x[4] or ''] \
                for x in cu.fetchall() ]

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

    @database.dbWriter
    def new(self, cu, fromName, toName):
        cu.execute("INSERT INTO RepNameMap VALUES (?, ?)", fromName, toName)
        return cu.lastid()
    
    def getCountByFromName(self, fromName):
        cu = self.db.cursor()
        cu.execute("SELECT COUNT(*) FROM RepNameMap WHERE fromName = ?", fromName)
        count = cu.fetchone()[0]
        return bool(count)

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

