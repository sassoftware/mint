#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

import database

(RDT_STRING,
     RDT_BOOL,
     RDT_INT)= range(3)

class GenericDataTable(database.DatabaseTable):
    '''
        This class crates a simple database table allowing for arbitrary data storage associated
        with a primary key of another table.
    '''
    name = None
    '''
        Note that this should contain the name of the "other" table followed by the word "Data"
    '''

    def __init__(self, db):
        if self.name is None:
            raise NotImplementedError
        self.lowered = self.name[0].lower() + self.name[1:]
        self.front = self.lowered.replace('Data', '')
        self.createSQL = """
            CREATE TABLE %s (
                                 %sId INTEGER,
                                 name CHAR(32),
                                 value TEXT,
                                 dataType INTEGER,
                                 PRIMARY KEY(%sId, name)
                                 );
        """ % (self.name, self.front, self.front)
        self.fields = ['%sId' % self.front, 'name', 'value', 'dataType']
        return database.DatabaseTable.__init__(self, db)
    

    def setDataValue(self, id, name, value, dataType):
        # do any data conversions necessary to safely store value as a string
        if dataType == RDT_BOOL:
            value=str(int(value))
        elif dataType == RDT_INT:
            value=str(value)

        cu = self.db.cursor()

        cu.execute("DELETE FROM %s WHERE %sId=? AND name=?" % (self.name, self.front), id, name)
        cu.execute("INSERT INTO %s (%sId, name, value, dataType) VALUES(?, ?, ?, ?)" % (self.name, self.front),
                   (id, name, value, dataType))
        return True

    def getDataValue(self, id, name):
        # this function returns a tuple: isPresent, value to avoid
        # passing None to indicate that no value is set, since we don't
        # allow our XMLRPC server to pass None values.
        cu = self.db.cursor()
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
        cu.execute("SELECT name, value, dataType FROM %s WHERE %sId=?" % (self.name, self.front), id)
        dataDict = {}
        for name, value, dataType in cu.fetchall():
            if dataType == RDT_BOOL:
                value=bool(int(value))
            elif dataType == RDT_INT:
                value=int(value)
            dataDict[name] = value
        return dataDict


class JobDataTable(GenericDataTable):
    name = "JobData"

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            falling = False
            if dbversion == 7:
                cu = self.db.cursor()
                #Need to drop the JobData Table.  It's not compatible
                #with the new genericdatatable
                cu.execute('DROP TABLE JobData')
                cu.execute(self.createSQL)
                return (dbversion + 1) == self.schemaVersion
        return True

class UserDataTable(GenericDataTable):
    name = "UserData"

class ReleaseDataTable(GenericDataTable):
    name = "ReleaseData"
