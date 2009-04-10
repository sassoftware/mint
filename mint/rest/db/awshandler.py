#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
from mint import amiperms

class AWSHandler(object):
    def __init__(self, cfg, db):
        self.db = db
        self.amiPerms = amiperms.AMIPermissionsManager(cfg, db)

    def notify_UserProductRemoved(self, event, userId, projectId, userlevel = None):
        self.amiPerms.deleteMemberFromProject(userId, projectId)

    def notify_UserProductAdded(self, event, userId, projectId, userlevel = None):
        self.amiPerms.addMemberToProject(userId, projectId)

    def notify_UserProductChanged(self, event, userId, projectId, oldLevel,
                                  newLevel):
        self.amiPerms.setMemberLevel(userId, projectId, oldLevel, newLevel)

    def notify_UserCancelled(self, userId):
        # yuck.
        awsFound, oldAwsAccountNumber = self.db.userData.getDataValue(
                                                userId, 'awsAccountNumber')
        self.amiPerms.setUserKey(userId, oldAwsAccountNumber, None)

    def notify_ReleasePublished(self, releaseId):
        self.amiPerms.publishRelease(releaseId)

    def notify_ReleaseUnpublished(self, releaseId):
        self.amiPerms.unpublishRelease(releaseId)
