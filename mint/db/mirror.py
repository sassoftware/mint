#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from mint.lib import database

class InboundMirrorsTable(database.KeyedTable):
    name = 'InboundMirrors'
    key = 'inboundMirrorId'

    fields = ['inboundMirrorId', 'targetProjectId', 'sourceLabels',
              'sourceUrl', 'sourceAuthType', 'sourceUsername',
              'sourcePassword', 'sourceEntitlement',
              'mirrorOrder', 'allLabels']

    def getIdByHostname(self, hostname):
        cu = self.db.cursor()
        cu.execute("""
        SELECT MIN(inboundMirrorId) FROM InboundMirrors
        JOIN Projects ON Projects.projectId = InboundMirrors.targetProjectId
        WHERE Projects.fqdn = ?
        """, hostname)
        return cu.fetchone()[0]


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
