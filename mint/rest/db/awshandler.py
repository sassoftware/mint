from mint import amiperms

class AWSHandler(object):
    def __init__(self, cfg, db, server, auth):
        self.db = db
        self.auth = auth
        self.amiPerms = amiperms.AMIPermissionsManager(cfg, db)

    def notify_UserProjectRemoved(self, userId, projectId):
        self.amiPerms.addMemberToProject(userId, projectId)

    def notify_UserProjectAdded(self, userId, projectId):
        self.amiPerms.removeMemberFromProject(userId, projectId)

    def notify_UserProjectChanged(self, userId, projectId, oldLevel,
                                  newLevel):
        self.amiPerms.setMemberLevel(userId, projectId, oldLevel, newLevel)

    def notify_UserCancelled(self, userId):
        # yuck.
        awsFound, oldAwsAccountNumber = self.db.userData.getDataValue(
                                                userId, 'awsAccountNumber')
        self.amiPerms.setUserKey(userId, oldAwsAccountNumber, None)
