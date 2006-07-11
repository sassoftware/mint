#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

from mint import database

(RDT_STRING,
 RDT_BOOL,
 RDT_INT,
 RDT_ENUM)= range(4)

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
        self.indexes = {self.name + "Idx" : "CREATE INDEX %s ON %s(%sId)" \
                                % (self.name + "Idx", self.name, self.front)}

        return database.DatabaseTable.__init__(self, db)

    def setDataValue(self, id, name, value, dataType):
        # do any data conversions necessary to safely store value as a string
        if dataType == RDT_BOOL:
            value=str(int(value))
        elif dataType == RDT_INT:
            value=str(value)

        cu = self.db.cursor()

        # audited for SQL injection
        cu.execute("DELETE FROM %s WHERE %sId=? AND name=?" % (self.name, self.front), id, name)
        # audited for SQL injection
        cu.execute("INSERT INTO %s (%sId, name, value, dataType) VALUES(?, ?, ?, ?)" % (self.name, self.front),
                   (id, name, value, dataType))
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


class JobDataTable(GenericDataTable):
    name = "JobData"

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            if dbversion == 7 and not self.initialCreation:
                cu = self.db.cursor()
                #Need to drop the JobData Table.  It's not compatible
                #with the new genericdatatable
                cu.execute('DROP TABLE JobData')
                cu.execute(self.createSQL)
            if dbversion == 13:
                cu = self.db.cursor()
                # replace all skipMediaCheck calls with showMediaCheck
                # use modular math since sqlite does not support XOR.
                cu.execute("""INSERT INTO ReleaseData
                                  SELECT releaseId, 'showMediaCheck',
                                          (value + 1) % 2, datatype
                                   FROM ReleaseData
                                   WHERE name='skipMediaCheck'""")
                cu.execute("""DELETE FROM ReleaseData
                                  WHERE name='skipMediaCheck'""")
            return dbversion >= 13
        return True

class UserDataTable(GenericDataTable):
    name = "UserData"

# XXX This table is deprecated in favor of BuildDataTable
class ReleaseDataTable(GenericDataTable):
    name = "ReleaseData"

class BuildDataTable(GenericDataTable):
    name = "BuildData"

