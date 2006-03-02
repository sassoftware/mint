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
        CONSTRAINT OutboundLabels_projectId_fk
            FOREIGN KEY (projectId) REFERENCES Projects(projectId)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        CONSTRAINT OutboundLabels_labelId_fk
            FOREIGN KEY (labelId) REFERENCES Labels(labelId)
            ON DELETE RESTRICT ON UPDATE CASCADE
    ) %(TABLEOPTS)s"""

    fields = ['projectId', 'labelId', 'url', 'username', 'password']

    def delete(self, labelId, url):
        cu = self.db.cursor()

        cu.execute("DELETE FROM OutboundLabels WHERE labelId=? AND url=?", labelId, url)
        self.db.commit()


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
