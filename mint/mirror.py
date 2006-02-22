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
        targetLabelId   INT NOT NULL,
        url             CHAR(255),
        username        CHAR(255),
        password        CHAR(255)
    ) %(TABLEOPTS)s"""

    fields = ['targetLabelId', 'url', 'username', 'password']
