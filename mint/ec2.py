#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

global _boto_present

try:
    import boto
    from boto.exception import EC2ResponseError
    _boto_present = True
except ImportError:
    _boto_present = False


from mint import database
from mint.mint_error import *
from mint.helperfuncs import toDatabaseTimestamp

class BlessedAMIsTable(database.KeyedTable):
    name = 'BlessedAMIs'
    key = 'blessedAMIId'

    fields = ( 'blessedAMIId', 'ec2AMIId', 'buildId', 'shortDescription',
               'helptext', 'instanceTTL', 'mayExtendTTLBy',
               'isAvailable', 'userDataTemplate' )

    def getAvailable(self):
        cu = self.db.cursor()
        cu.execute("""SELECT blessedAMIId FROM BlessedAMIs
                      WHERE isAvailable = 1""")
        return [ x[0] for x in cu.fetchall() ]

class LaunchedAMIsTable(database.KeyedTable):
    name = 'LaunchedAMIs'
    key = 'launchedAMIId'

    fields = ( 'launchedAMIId', 'blessedAMIId', 'launchedFromIP',
               'ec2InstanceId', 'raaPassword', 'launchedAt',
               'expiresAfter', 'isActive', 'userData' )

    def getActive(self):
        cu = self.db.cursor()
        cu.execute("""SELECT launchedAMIId FROM LaunchedAMIs
                      WHERE isActive = 1""")
        return [ x[0] for x in cu.fetchall() ]

    def getCountForIP(self, ipaddr):
        cu = self.db.cursor()
        cu.execute("""SELECT COUNT(launchedAMIId) FROM LaunchedAMIs
                      WHERE isActive = 1 AND launchedFromIP = ?""",
                      ipaddr)
        return cu.fetchone()[0]

    def getCandidatesForTermination(self):
        cu = self.db.cursor()
        cu.execute("""SELECT launchedAMIId, ec2InstanceId FROM LaunchedAMIs
                      WHERE isActive = 1 AND expiresAfter < ?""",
                      toDatabaseTimestamp())
        return [ x for x in cu.fetchall() ]

class LaunchedAMI(database.TableObject):

    __slots__ = LaunchedAMIsTable.fields

    def getItem(self, id):
        return self.server.getLaunchedAMI(id)

    def save(self):
        return self.server.updateLaunchedAMI(self.launchedAMIId,
                self.getDataAsDict())

class BlessedAMI(database.TableObject):

    __slots__ = BlessedAMIsTable.fields

    def getItem(self, id):
        return self.server.getBlessedAMI(id)

    def save(self):
        return self.server.updateBlessedAMI(self.blessedAMIId,
                self.getDataAsDict())

class EC2Wrapper(object):

    __slots__ = ( 'ec2conn', 'accountId', 'accessKey', 'secretKey')

    def __init__(self, (accountId, accessKey, secretKey)):
        self.accountId = accountId
        self.accessKey = accessKey
        self.secretKey = secretKey
        self.ec2conn = boto.connect_ec2(self.accessKey, self.secretKey)

    def launchInstance(self, ec2AMIId, userData=None, useNATAddressing=False):

        # Get the appropriate addressing type to pass into the
        # Amazon API; 'public' uses NAT, 'direct' is bridged.
        # The latter method is deprecated and may go away in the
        # future.
        addressingType = useNATAddressing and 'public' or 'direct'
        try:
            ec2Reservation = self.ec2conn.run_instances(ec2AMIId,
                    user_data=userData, addressing_type=addressingType)
            ec2Instance = ec2Reservation.instances[0]
            return str(ec2Instance.id)
        except EC2ResponseError:
            return None

    def getInstanceStatus(self, ec2InstanceId):
        try:
            rs = self.ec2conn.get_all_instances(instance_ids=[ec2InstanceId])
            instance = rs[0].instances[0]
            return str(instance.state), str(instance.dns_name)
        except EC2ResponseError:
            return "unknown", ""

    def terminateInstance(self, ec2InstanceId):
        try:
            self.ec2conn.terminate_instances(instance_ids=[ec2InstanceId])
            return True
        except EC2ResponseError:
            return False
        
    def getAllKeyPairs(self, keyNames=None):
        keyPairs = []
        rs = self.ec2conn.get_all_key_pairs(keynames=keyNames)
        for pair in rs:
            keyPairs.append((str(pair.name), str(pair.fingerprint),
                            str(pair.material)))            
        return keyPairs
    
    @staticmethod
    def validateCredentials(authToken):
        try:
            wrapper = EC2Wrapper(authToken)
            wrapper.getAllKeyPairs()
            rc = True, None
        except EC2ResponseError, e:
            rc = False, e.status
            
        return rc
            
