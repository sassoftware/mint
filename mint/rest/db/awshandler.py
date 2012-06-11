#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
from mint import buildtypes
from mint import amiperms
from mint import ec2
from mint import mint_error

from mint.rest.db import manager

class AWSHandler(manager.Manager):
    def __init__(self, cfg, db, auth, publisher = None):
	manager.Manager.__init__(self, cfg, db, auth, publisher)
        self.amiPerms = amiperms.AMIPermissionsManager(cfg, db.db)

    def notify_UserProductRemoved(self, event, userId, projectId, oldLevel=None,
                                  userlevel = None):
        self.amiPerms.deleteMemberFromProject(userId, projectId)

    def notify_UserProductAdded(self, event, userId, projectId, oldLevel=None,
                                userlevel = None):
        self.amiPerms.addMemberToProject(userId, projectId)

    def notify_UserProductChanged(self, event, userId, projectId, oldLevel,
                                  newLevel):
        self.amiPerms.setMemberLevel(userId, projectId, oldLevel, newLevel)

    def notify_UserCancelled(self, event, userId):
        # yuck.
        awsFound, oldAwsAccountNumber = self.db.userData.getDataValue(
                                                userId, 'awsAccountNumber')
        self.amiPerms.setUserKey(userId, oldAwsAccountNumber, None)

    def notify_ReleasePublished(self, event, releaseId):
        self.amiPerms.publishRelease(releaseId)

    def notify_ReleaseUnpublished(self, event, releaseId):
        self.amiPerms.unpublishRelease(releaseId)

    def notify_ImageRemoved(self, event, imageId, imageName, imageType):
        if imageType != buildtypes.AMI or imageName is None:
            return
        s3 = self.amiPerms._getS3Client()
        try:
            s3.deleteAMI(imageName)
        except (ec2.mint_error.EC2Exception,
                mint_error.AMIInstanceDoesNotExist):
            pass

    def notify_ProductUnhidden(self, event, projectId):
        self.amiPerms.unhideProject(projectId)
