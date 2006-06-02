#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#
from mint import database

class InboundLabelsTable(database.KeyedTable):
    name = 'InboundLabels'
    key = 'labelId'
    createSQL= """CREATE TABLE InboundLabels (
        projectId       INT NOT NULL,
        labelId         INT NOT NULL,
        url             VARCHAR(255),
        username        VARCHAR(255),
        password        VARCHAR(255),
        CONSTRAINT InboundLabels_projectId_fk
            FOREIGN KEY (projectId) REFERENCES Projects(projectId)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        CONSTRAINT InboundLabels_labelId_fk
            FOREIGN KEY (labelId) REFERENCES Labels(labelId)
            ON DELETE RESTRICT ON UPDATE CASCADE
    ) %(TABLEOPTS)s"""

    fields = ['projectId', 'labelId', 'url', 'username', 'password']


class OutboundLabelsTable(database.KeyedTable):
    name = 'OutboundLabels'
    key = 'labelId'
    createSQL= """CREATE TABLE OutboundLabels (
        projectId       INT NOT NULL,
        labelId         INT NOT NULL,
        url             VARCHAR(255),
        username        VARCHAR(255),
        password        VARCHAR(255),
        allLabels       INT DEFAULT 0,
        recurse         INT DEFAULT 0,
        CONSTRAINT OutboundLabels_projectId_fk
            FOREIGN KEY (projectId) REFERENCES Projects(projectId)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        CONSTRAINT OutboundLabels_labelId_fk
            FOREIGN KEY (labelId) REFERENCES Labels(labelId)
            ON DELETE RESTRICT ON UPDATE CASCADE
    ) %(TABLEOPTS)s"""

    fields = ['projectId', 'labelId', 'url', 'username', 'password',
              'allLabels', 'recurse']

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            cu = self.db.cursor()
            if dbversion == 17 and not self.initialCreation:
                cu.execute("ALTER TABLE OutboundLabels ADD COLUMN allLabels INT DEFAULT 0")
            if dbversion == 18 and not self.initialCreation:
                cu.execute("ALTER TABLE OutboundLabels ADD COLUMN recurse INT DEFAULT 0")
            return dbversion >= 18
        return True

    def get(self, *args, **kwargs):
        res = database.KeyedTable.get(self, *args, **kwargs)
        res['allLabels'] = bool(res['allLabels'])
        res['recurse'] = bool(res['recurse'])
        return res

    def delete(self, labelId, url):
        cu = self.db.cursor()

        cu.execute("DELETE FROM OutboundLabels WHERE labelId=? AND url=?",
                   labelId, url)
        cu.execute("DELETE FROM OutboundMatchTroves WHERE labelId=?", labelId)
        self.db.commit()


class OutboundMatchTrovesTable(database.KeyedTable):
    name = 'OutboundMatchTroves'
    key = 'labelId'
    createSQL= """CREATE TABLE OutboundMatchTroves (
        projectId       INT NOT NULL,
        labelId         INT NOT NULL,
        idx             INT NOT NULL,
        matchStr         VARCHAR(255),
        CONSTRAINT OutboundMatchTroves_projectId_fk
            FOREIGN KEY (projectId) REFERENCES Projects(projectId)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        CONSTRAINT OutboundMatchTroves_labelId_fk
            FOREIGN KEY (labelId) REFERENCES Labels(labelId)
            ON DELETE RESTRICT ON UPDATE CASCADE
    ) %(TABLEOPTS)s"""

    fields = ['projectId', 'labelId', 'matchStr']

    def set(self, projectId, labelId, matchList):
        cu = self.db.cursor()
        cu.execute("""DELETE FROM OutboundMatchTroves
                          WHERE projectId=? AND labelId=?""",
                   projectId, labelId)
        for idx, matchStr in enumerate(matchList):
            cu.execute("""INSERT INTO OutboundMatchTroves
                              (projectId, labelId, idx, matchStr)
                              VALUES(?, ?, ?, ?)""",
                       projectId, labelId, idx, matchStr)
        self.db.commit()

    def listMatches(self, labelId):
        cu = self.db.cursor()
        cu.execute("""SELECT matchStr
                          FROM OutboundMatchTroves
                          WHERE labelId=?
                          ORDER BY idx""",
                   labelId)
        return [x[0] for x in cu.fetchall()]

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
