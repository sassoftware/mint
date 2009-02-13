from mint.lib import database
from mint.helperfuncs import toDatabaseTimestamp, urlSplit

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

