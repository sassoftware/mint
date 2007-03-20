#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#


import boto
from boto.exception import EC2ResponseError

from conary.dbstore.sqllib import toDatabaseTimestamp

from mint import database
from mint.mint_error import MintError

class TooManyAMIInstancesPerIP(MintError):
    def __str__(self):
        return "Too many AMI instances have been launched from this IP " \
               "address. Please try again later."

class FailedToLaunchAMIInstance(MintError):
    def __str__(self):
        return "Failed to launch AMI instance."

class BlessedAMIsTable(database.KeyedTable):
    name = 'BlessedAMIs'
    key = 'blessedAMIId'
    createSQL = """
        CREATE TABLE BlessedAMIs (
            blessedAMIId        %(PRIMARYKEY)s,
            ec2AMIId            CHAR(12) NOT NULL,
            buildId             INTEGER,
            shortDescription    VARCHAR(128),
            helptext            TEXT,
            instanceTTL         INTEGER NOT NULL,
            mayExtendTTLBy      INTEGER,
            isAvailable         INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ba_fk_b FOREIGN KEY (buildId)
                REFERENCES Builds(buildId) ON DELETE SET NULL
        )"""

    fields = ( 'blessedAMIId', 'ec2AMIId', 'buildId', 'shortDescription',
               'helptext', 'instanceTTL', 'mayExtendTTLBy',  'isAvailable' )

    indexes = { "BlessedAMIEc2AMIIdIdx":\
                    """CREATE INDEX BlessedAMIEc2AMIIdIdx
                            ON BlessedAMIs(ec2AMIId)""" }

    def getAvailable(self):
        cu = self.db.cursor()
        cu.execute("""SELECT blessedAMIId FROM BlessedAMIs
                      WHERE isAvailable = 1""")
        return [ x[0] for x in cu.fetchall() ]

class LaunchedAMIsTable(database.KeyedTable):
    name = 'LaunchedAMIs'
    key = 'launchedAMIId'
    createSQL = """
        CREATE Table LaunchedAMIs (
            launchedAMIId       %(PRIMARYKEY)s,
            blessedAMIId        INTEGER NOT NULL,
            launchedFromIP      CHAR(15) NOT NULL,
            ec2InstanceId       CHAR(10) NOT NULL,
            raaPassword         CHAR(8) NOT NULL,
            launchedAt          NUMERIC(14,0) NOT NULL,
            expiresAfter        NUMERIC(14,0) NOT NULL,
            isActive            INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT la_bai_fk FOREIGN KEY (blessedAMIId)
                REFERENCES BlessedAMIs(blessedAMIId) ON DELETE RESTRICT
        )"""

    fields = ( 'launchedAMIId', 'blessedAMIId', 'launchedFromIP',
               'ec2InstanceId', 'raaPassword', 'launchedAt', 'expiresAfter', 'isActive' )

    indexes = { 'LaunchedAMIsExpiresActive':
                    """CREATE INDEX LaunchedAMIsExpiresActive
                             ON LaunchedAMIs(isActive,expiresAfter)""",
                'LaunchedAMIsIPActive':
                    """CREATE INDEX LaunchedAMIsIPActive
                             ON LaunchedAMIs(isActive,launchedFromIP)"""}

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

    __slots__ = ( 'ec2conn', )

    def __init__(self, cfg):
        self.ec2conn = boto.connect_ec2(cfg.awsPublicKey, cfg.awsPrivateKey)

    def launchInstance(self, ec2AMIId, userData=None):
        try:
            ec2Reservation = self.ec2conn.run_instances(ec2AMIId,
                    user_data=userData)
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

