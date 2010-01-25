import tarfile

from mint import config
from mint import ec2
from mint import mint_error
from mint import userlevels

class AMIPermissionsManager(object):
    def __init__(self, cfg, db):
        self.cfg = cfg
        self.db = db

    def setUserKey(self, userId, oldAccountNumber, newAccountNumber):
        amiIds = self._getAMIsForPermChange(userId)
        if oldAccountNumber:
            self._removeAMIPermissionsForAccount(oldAccountNumber, amiIds)
        if newAccountNumber:
            self._addAMIPermissionsForAccount(newAccountNumber, amiIds)
    
    def addMemberToProject(self, userId, projectId):
        if not self._hasAWSAccount(userId):
            return
        amiIds = self._getAMIsForPermChange(userId, projectId)
        self._addAMIPermissionsForUser(userId, amiIds)

    def deleteMemberFromProject(self, userId, projectId):
        if not self._hasAWSAccount(userId):
            return
        amiIds = self._getAMIsForPermChange(userId, projectId)
        self._removeAMIPermissionsForUser(userId, amiIds)

    def setMemberLevel(self, userId, projectId, oldLevel, newLevel):
        if not self._hasAWSAccount(userId):
            return
        oldIds = self._getAMIsForPermChange(userId, projectId, oldLevel)
        oldIds = set(oldIds)
        newIds = self._getAMIsForPermChange(userId, projectId, newLevel)
        newIds = set(newIds)
        unchangedIds = oldIds & newIds
        self._removeAMIPermissionsForUser(userId, oldIds - unchangedIds)
        self._addAMIPermissionsForUser(userId, newIds - unchangedIds)

    def publishRelease(self, releaseId):
        amiIds, isPrivate, projectId = self._getAMIsForRelease(releaseId)
        if isPrivate:
            users = self.db.projectUsers.getMembersByProjectId(projectId)
            userIds = [ x[0] for x in users if x[2] == userlevels.USER ]
            self._addAMIPermissionsForUsers(userIds, amiIds)
        else:
            self._addAMIPermissionsForAll(amiIds)

    def unpublishRelease(self, releaseId):
        amiIds, isPrivate, projectId = self._getAMIsForRelease(releaseId)
        users = self.db.projectUsers.getMembersByProjectId(projectId)
        userIds = [ x[0] for x in users if x[2] in userlevels.WRITERS ]
        self._removeAMIPermissionsForAll(amiIds)
        self._addAMIPermissionsForUsers(userIds, amiIds)

    def hideProject(self, projectId):
        # Get a list of published and unpublished AMIs for this project
        published, unpublished = self.db.builds.getAMIBuildsForProject(
                                                                projectId)

        if not (published or unpublished):
            return

        writers, readers = self.db.projectUsers.\
                                getEC2AccountNumbersForProjectUsers(projectId)
        self._removeAMIPermissionsForAll(published + unpublished)
        # all project members, including users, can see published builds
        self._addAMIPermissionsForAccounts(writers + readers, published)
        # only project developers and owners can see unpublished builds
        self._addAMIPermissionsForAccounts(writers, unpublished)

    def unhideProject(self, projectId):
        writers, readers = self.db.projectUsers.\
                                getEC2AccountNumbersForProjectUsers(projectId)
        published, unpublished = self.db.builds.getAMIBuildsForProject(
                                                                projectId)
        self._removeAMIPermissionsForAll(published + unpublished)
        # everyone can view published releases
        self._addAMIPermissionsForAll(published)
        # writers can view unpublished releases
        self._addAMIPermissionsForAccounts(writers, unpublished)

    def getTargetData(self):
        targetId = self.db.targets.getTargetId('ec2', 'aws', None)
        if targetId is None:
            raise mint_error.EC2NotConfigured()
        amiData = self.db.targetData.getTargetData(targetId)
        return amiData

    def uploadBundle(self, filePath, callback = None):
        targetData = self.getTargetData()
        s3Bucket = targetData.get('ec2S3Bucket')
        if s3Bucket is None:
            raise mint_error.EC2NotConfigured()
        client = self._getS3Client()
        tarObject = tarfile.TarFile.open(filePath, "r:gz")
        return client.uploadBundle(tarObject, s3Bucket, callback = callback)

    def registerAMI(self, bucketName, manifestName, readers = None,
            writers = None):
        targetData = self.getTargetData()
        launchUsers = targetData.get('ec2LaunchUsers', [])
        launchGroups = targetData.get('ec2LaunchGroups', [])
        readers = readers or []
        writers = writers or []
        if readers or writers:
            # This is coming from server.py's serializeBuild
            launchUsers = readers + writers
            launchGroups = []
        client = self._getEC2Client()
        amiId, amiManifestName = client.registerAMI(bucketName, manifestName,
            ec2LaunchUsers = launchUsers,
            ec2LaunchGroups = launchGroups)

        return amiId, amiManifestName

    def _getEC2Client(self):
        return self._getClient(ec2.EC2Wrapper)

    def _getS3Client(self):
        return self._getClient(ec2.S3Wrapper)

    def _getClient(self, clientClass):
        # make sure all the values are set
        amiData = self.getTargetData()
        authToken = (amiData['ec2AccountId'],
                     amiData['ec2PublicKey'],
                     amiData['ec2PrivateKey'])
        if False in [ bool(x) for x in authToken ]:
            raise mint_error.EC2NotConfigured()
        return clientClass(authToken, self.cfg.proxy.get('https'))

    def _hasAWSAccount(self, userId):
        return bool(self._getAWSAccountNumber(userId))

    def _getAWSAccountNumber(self, userId):
        awsFound, awsAccountNumber = self.db.userData.getDataValue(userId,
                                         'awsAccountNumber')
        if awsFound:
            return awsAccountNumber

    def _addAMIPermissionsForUser(self, userId, amiIds):
        self._addAMIPermissionsForUsers([userId], amiIds)

    def _addAMIPermissionsForUsers(self, userIds, amiIds):
        accountIds = set()
        for userId in userIds:
            awsAccountNumber = self._getAWSAccountNumber(userId)
            if awsAccountNumber:
                accountIds.add(awsAccountNumber)
        if accountIds:
            self._addAMIPermissionsForAccounts(accountIds, amiIds)

    def _addAMIPermissionsForAccounts(self, accountIds, amiIds):
        if not (accountIds and amiIds):
            return
        ec2Client = self._getEC2Client()
        for awsAccountNumber in accountIds:
            for amiId in amiIds:
                self._tryAMIAction(ec2Client.addLaunchPermission, 
                                   amiId, awsAccountNumber)

    def _addAMIPermissionsForAll(self, amiIds):
        if not amiIds:
            return
        ec2Client = self._getEC2Client()
        if config.isRBO():
            for amiId in amiIds:
                self._tryAMIAction(ec2Client.resetLaunchPermissions, amiId)
                self._tryAMIAction(ec2Client.addPublicLaunchPermission, amiId)
        else:
            awsAccountNumbers = []
            users = self.db.users.getUsersWithAwsAccountNumber()
            for user in users:
                awsAccountNumbers.append(user[1])
            for amiId in amiIds:
                self._tryAMIAction(ec2Client.resetLaunchPermissions, amiId)
                for awsAccountNumber in awsAccountNumbers:
                    self._tryAMIAction(ec2Client.addLaunchPermission, amiId,
                                       awsAccountNumber)

    def _removeAMIPermissionsForUser(self, userId, amiIds):
        self._removeAMIPermissionsForUsers([userId], amiIds)

    def _removeAMIPermissionsForUsers(self, userIds, amiIds):
        if not (userIds and amiIds):
            return
        ec2Client = self._getEC2Client()
        for userId in userIds:
            awsAccountNumber = self._getAWSAccountNumber(userId)
            if not awsAccountNumber:
                continue
            for amiId in amiIds:
                self._tryAMIAction(ec2Client.removeLaunchPermission, amiId, 
                                   awsAccountNumber)
    
    def _removeAMIPermissionsForAccount(self, awsAccountNumber, amiIds):
        if not amiIds:
            return
        ec2Client = self._getEC2Client()
        for amiId in amiIds:
            self._tryAMIAction(ec2Client.removeLaunchPermission, amiId, 
                               awsAccountNumber)

    def _shouldIgnoreException(self, exc):
        if not isinstance(exc, mint_error.EC2Exception):
            return False
        e = exc.ec2ResponseObj
        if not e:
            return False
        error = e.errors and e.errors[0] or None
        if error and error["code"].startswith("InvalidAMIID."):
            return True

    def _addAMIPermissionsForAccount(self, awsAccountNumber, amiIds):
        if not amiIds:
            return
        ec2Client = self._getEC2Client()
        for amiId in amiIds:
            self._tryAMIAction(
                ec2Client.addLaunchPermission, amiId, awsAccountNumber)

    def _removeAMIPermissionsForAll(self, amiIds):
        if not amiIds:
            return
        ec2Client = self._getEC2Client()
        for amiId in amiIds:
            self._tryAMIAction(ec2Client.resetLaunchPermissions, amiId)

    def _getAMIsForRelease(self, releaseId):
        pubreleaseTable = self.db.publishedReleases
        amiDataList = pubreleaseTable.getAMIBuildsForPublishedRelease(
                                                                    releaseId)
        amiIds = [ x['amiId'] for x in amiDataList ]
        if not amiIds:
            return [], False, None
        # list will be empty if all projects are public
        isPrivate = bool([x for x in amiDataList if x['isPrivate']])
        # really should only be one projectId for a release.
        projectIds = set(x['projectId'] for x in amiDataList)
        assert(len(projectIds) == 1)
        projectId = list(projectIds)[0]
        return amiIds, isPrivate, projectId

    def _getAMIsForPermChange(self, userId, projectId=None, 
                              levelOverride=None):
        """
            Returns AMIS that are relevant for a permission change
            on a project.  That is, images that that are 
            visible for a member with the current membership level
            that would not be for a non-member or someone with
            a lower membership level or if the image was unpublished.
        """
        amiData = self.db.users.getAMIBuildsForUser(userId)
        if projectId:
            amiData = [ x for x in amiData if x['projectId'] == projectId ]
        if levelOverride:
            level = levelOverride
        amiIds = []
        for data in amiData:
            isPrivate = data['isPrivate']
            memberLevel = data['level']
            isPublished = data['isPublished']
            amiId = data['amiId']
            projectId = data['projectId']
            if not levelOverride:
                level = data['level']

            if level == userlevels.USER:
                # a user only has special permissions to see private project 
                # published images.  For public projects, they don't have any 
                # special privileges so we're not interested in whether 
                # they're a member or not.
                if isPrivate and isPublished:
                    amiIds.append(amiId)
            else:
                # developers/owners of this project have special permissions 
                # for private projects, and unpublished images on public 
                # projects.
                if isPrivate or not isPublished:
                    amiIds.append(amiId)
        return amiIds

    def _tryAMIAction(self, fn, *args, **kw):
        try:
            return fn(*args, **kw)
        except mint_error.EC2Exception, e:
            if not self._shouldIgnoreException(e):
                raise

