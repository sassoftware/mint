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


import base64
from mint.lib import cred_client
from mint.lib import database

(RDT_STRING,
 RDT_BOOL,
 RDT_INT,
 RDT_ENUM,
 RDT_TROVE)= range(5)

class Data(object):

    @classmethod
    def thaw(cls, data, dataType):
        if data is None:
            return None
        if dataType == RDT_BOOL:
            return bool(int(data))
        if dataType == RDT_INT:
            return int(data)
        return data

    @classmethod
    def freeze(cls, data, dataType):
        if data is None:
            return None
        if dataType == RDT_BOOL:
            return str(int(data))
        if dataType == RDT_INT:
            return str(data)
        return data

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
        value = Data.freeze(value, dataType)

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
        value = Data.thaw(value, dataType)
        return True, value

    def getDataDict(self, id):
        cu = self.db.cursor()
        # audited for SQL injection
        cu.execute("SELECT name, value, dataType FROM %s WHERE %sId=?" % (self.name, self.front), id)
        dataDict = {}
        for name, value, dataType in cu.fetchall():
            value = Data.thaw(value, dataType)
            dataDict[name] = value
        return dataDict

    def removeDataValue(self, id, name, commit=True):
        cu = self.db.cursor()

        cu.execute("DELETE FROM %s WHERE %sId=? AND name=?" % (self.name, self.front), id, name)
        if commit:
            self.db.commit()

        return True
    
def marshalGenericData(genericDataDict):
    if not genericDataDict:
        return ""
    # Newline-separated fields
    data = '\n'.join(["%s:%s" % (k, base64.b64encode(v))
        for (k, v) in sorted(genericDataDict.iteritems())
        if v is not None])
    return data

def unmarshalGenericData(genericData):
    ret = {}
    for nameval in genericData.split('\n'):
        arr = nameval.split(':', 1)
        if len(arr) != 2:
            continue
        ret[arr[0]] = base64.b64decode(arr[1])
    return ret


def _getCredClient():
    return cred_client.CredentialsClient()


def marshalCredentials(cfg, creds):
    value = marshalGenericData(creds)
    if cfg and cfg.encryptCredentials:
        value = _getCredClient().wrap(value)
    return value
marshalTargetUserCredentials = marshalCredentials


def unmarshalCredentials(cfg, creds):
    if creds.startswith('{'):
        creds = _getCredClient().unwrap(creds)
    return unmarshalGenericData(creds)
unmarshalTargetUserCredentials = unmarshalCredentials
