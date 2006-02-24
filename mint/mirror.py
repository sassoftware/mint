#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#
from mint import database

class MirrorLabelsTable(database.KeyedTable):
    name = 'MirrorLabels'
    key = 'targetLabelId'
    createSQL= """CREATE TABLE MirrorLabels (
        projectId       INT NOT NULL,
        targetLabelId   INT NOT NULL,
        url             VARCHAR(255),
        username        VARCHAR(255),
        password        VARCHAR(255),
        CONSTRAINT MirrorLabels_projectId_fk
            FOREIGN KEY (projectId) REFERENCES Projects(projectId)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        CONSTRAINT MirrorLabels_targetLabelId_fk
            FOREIGN KEY (targetLabelId) REFERENCES Labels(labelId)
            ON DELETE RESTRICT ON UPDATE CASCADE
    ) %(TABLEOPTS)s"""

    fields = ['projectId', 'targetLabelId', 'url', 'username', 'password']

class RepNameMapTable(database.DatabaseTable):
    name = "RepNameMap"
    createSQL = """CREATE TABLE RepNameMap (
        fromName    VARCHAR(255),
        toName      VARCHAR(255),
        PRIMARY KEY(fromName, toName)
    ) %(TABLEOPTS)s"""

    fields = ['fromName', 'toName']
    indexes = {'RepNameMap_fromName_idx': 'CREATE INDEX RepNameMap_fromName_idx ON RepNameMap(fromName)'}

    def new(self, fromName, toName):
        cu = self.db.cursor()

        cu.execute("INSERT INTO RepNameMap VALUES (?, ?)", fromName, toName)
        self.db.commit()
