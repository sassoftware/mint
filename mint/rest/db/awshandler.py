
class AWSHandler(object):
    def __init__(self, cfg, db, server):
        self.cfg = cfg
        self.db = db
        self.server = server

    def notify_UserProjectRemoved(self, performer, userId, projectId):
        # Set any EC2 launch permissions if the user has aws credentials set.
        awsFound, awsAccountNumber = self.userData.getDataValue(userId,
                                         'awsAccountNumber')
        if awsFound:
            # Remove all old launch permissions.
            amiIds = self.server._getProductAMIIdsForPermChange(userId, projectId)
            self.server.removeEC2LaunchPermissions(userId, awsAccountNumber, 
                                                   amiIds)


    def notify_UserProjectAdded(self, performer, userId, projectId):
        # Set any EC2 launch permissions if the user has aws 
        # credentials set.
        awsFound, awsAccountNumber = self.userData.getDataValue(userId,
                                         'awsAccountNumber')
        if awsFound:
            self.addProductEC2LaunchPermissions(userId, awsAccountNumber,
                                                projectId)


    def notify_UserProjectChanged(self, performer, userId, projectId, level):
        # Get any EC2 launch permissions if the user has aws credentials set.
        awsFound, awsAccountNumber = self.userData.getDataValue(userId,
                                         'awsAccountNumber')
        if not awsFound:
            return 

        currentAMIIds = self._getProductAMIIdsForPermChange(userId,
                                                           projectId)
        newAMIIds = self._getProductAMIIdsForPermChange(
                             userId, projectId)
        if level == userlevels.USER:
            self.removeEC2LaunchPermissions(userId, awsAccountNumber,
                   [id for id in currentAMIIds if id not in newAMIIds])
        else:
            self.addEC2LaunchPermissions(userId, awsAccountNumber,
                   [id for id in newAMIIds if id not in currentAMIIds])


    def notify_UserCancelled(self, performer, userId):
        # remove EC2 launch permissions
        ec2cred = self.getEC2CredentialsForUser(userId)
        if ec2cred and ec2cred.has_key('awsAccountNumber'):
            if ec2cred['awsAccountNumber']:
                # revoke launch permissions
                self.server.removeAllEC2LaunchPermissions(userId, 
                                                ec2cred['awsAccountNumber'])
                
        # remove EC2 credentials
        self.server.removeEC2CredentialsForUser(userId)
