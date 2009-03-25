#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

from mint.lib import database

(RDT_STRING,
 RDT_BOOL,
 RDT_INT,
 RDT_ENUM,
 RDT_TROVE)= range(5)

class GenericDataTable(database.DatabaseTable):
    name = None

    def __init__(self, db):
        if not self.name:
            return NotImplementedError
        self.lowered = self.name[0].lower() + self.name[1:]
        self.front = self.lowered.replace('Data', '')
        self.fields = ['%sId' % self.front, 'name', 'value', 'dataType']
        return database.DatabaseTable.__init__(self, db)

    def setDataValue(self, id, name, value, dataType, commit=True):
        # do any data conversions necessary to safely store value as a string
        if dataType == RDT_BOOL:
            value=str(int(value))
        elif dataType == RDT_INT:
            value=str(value)

        cu = self.db.cursor()

        self.removeDataValue(id, name, commit=False)

        # audited for SQL injection
        cu.execute("INSERT INTO %s (%sId, name, value, dataType) VALUES(?, ?, ?, ?)" % (self.name, self.front),
                   (id, name, value, dataType))
        if commit:
            self.db.commit()
        return True

    def getDataValue(self, id, name):
        # this function returns a tuple: isPresent, value to avoid
        # passing None to indicate that no value is set, since we don't
        # allow our XMLRPC server to pass None values.
        cu = self.db.cursor()
        # audited for SQL injection
        cu.execute("SELECT value, dataType FROM %s WHERE %sId=? AND name=?" % (self.name, self.front), (id, name))
        res = cu.fetchall()
        if len(res) != 1:
            return False, 0
        value, dataType = res[0]
        if dataType == RDT_BOOL:
            value=bool(int(value))
        elif dataType == RDT_INT:
            value=int(value)
        return True, value

    def getDataDict(self, id):
        cu = self.db.cursor()
        # audited for SQL injection
        cu.execute("SELECT name, value, dataType FROM %s WHERE %sId=?" % (self.name, self.front), id)
        dataDict = {}
        for name, value, dataType in cu.fetchall():
            if dataType == RDT_BOOL:
                value=bool(int(value))
            elif dataType == RDT_INT:
                value=int(value)
            dataDict[name] = value
        return dataDict

    def removeDataValue(self, id, name, commit=True):
        cu = self.db.cursor()

        cu.execute("DELETE FROM %s WHERE %sId=? AND name=?" % (self.name, self.front), id, name)
        if commit:
            self.db.commit()

        return True