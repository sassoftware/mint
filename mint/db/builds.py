import time

from mint import buildtypes
from mint import helperfuncs
from mint import jobstatus
from mint.lib import data
from mint.lib import database
from mint.mint_error import *

class UrlDownloadsTable(database.DatabaseTable):
    name = "UrlDownloads"
    fields = ['urlId', 'timeDownloaded', 'ip']

    def add(self, urlId, ip):
        t = helperfuncs.toDatabaseTimestamp()
        cu = self.db.cursor()
        cu.execute("""INSERT INTO UrlDownloads (urlId, timeDownloaded, ip)
            VALUES (?, ?, ?)""",
            urlId, t, ip)
        self.db.commit()


class BuildsTable(database.KeyedTable):
    name = "Builds"
    key  = "buildId"

    fields = ['buildId', 'projectId', 'pubReleaseId',
              'buildType', 'name', 'description',
              'troveName', 'troveVersion', 'troveFlavor', 'troveLastChanged',
              'timeCreated', 'createdBy', 'timeUpdated', 'updatedBy',
              'buildCount', 'productVersionId', 'stageName',
              'status', 'statusMessage', 'job_uuid',
              ]

    # Not the ideal place to put these, but I wanted to easily find them later
    # --misa
    EC2TargetType = 'ec2'
    EC2TargetName = 'aws'

    def iterBuildsForProject(self, projectId):
        """ Returns an iterator over the all of the buildIds in a given
            project with ID projectId. The iterator is ordered by the date
            the associated group grove last changed in descending order
            (most to lease recent)."""

        cu = self.db.cursor()

        cu.execute("""SELECT buildId FROM Builds
                      WHERE projectId=? AND
                            troveName IS NOT NULL AND
                            troveVersion IS NOT NULL AND
                            troveFlavor IS NOT NULL AND
                            troveLastChanged IS NOT NULL
                            ORDER BY troveLastChanged DESC, buildId""",
                   projectId)

        for results in cu.fetchall():
            yield results[0]

    def setTrove(self, buildId, troveName, troveVersion, troveFlavor):
        cu = self.db.cursor()
        cu.execute("""UPDATE Builds SET troveName=?,
                                          troveVersion=?,
                                          troveFlavor=?,
                                          troveLastChanged=?
                      WHERE buildId=?""",
                   troveName, troveVersion,
                   troveFlavor, time.time(),
                   buildId)
        self.db.commit()
        return 0

    def setProductVersion(self, buildId, versionId, stageName):
        cu = self.db.cursor()
        cu.execute("""UPDATE Builds SET productVersionId=?,
                                          stageName=?,
                                          troveLastChanged=?
                      WHERE buildId=?""",
                   versionId, stageName,
                   time.time(), buildId)
        self.db.commit()

    def getTrove(self, buildId):
        cu = self.db.cursor()

        cu.execute("""SELECT troveName,
                             troveVersion,
                             troveFlavor
                      FROM Builds
                      WHERE buildId=?""",
                   buildId)
        r = cu.fetchone()

        name, version, flavor = r[0], r[1], r[2]
        if not flavor:
            flavor = "none"
        if not name or not version:
            raise TroveNotSet
        else:
            return name, version, flavor

    def getPublished(self, buildId):
        cu = self.db.cursor()
        cu.execute("SELECT COALESCE((SELECT pubReleaseId FROM Builds WHERE buildId=?), 0)", buildId)
        pubReleaseId = cu.fetchone()[0]
        if pubReleaseId:
            cu.execute("SELECT timePublished FROM PublishedReleases WHERE pubReleaseId = ?", pubReleaseId)
            res = cu.fetchone()
            if res:
                return bool(res[0])
        return False

    def getUnpublishedBuilds(self, projectId):
        cu = self.db.cursor()
        cu.execute("""SELECT buildId FROM Builds
                      WHERE projectId = ? AND pubReleaseId IS NULL""",
                      projectId)
        res = cu.fetchall()
        return [x[0] for x in res]

    def buildExists(self, buildId):
        cu = self.db.cursor()

        cu.execute("SELECT count(*) FROM Builds WHERE buildId=?", buildId)
        return cu.fetchone()[0]

    def bumpBuildCount(self, buildId):
        # This is a post-increment, unlike bumpCookCount, since we always want
        # to look at the last build.
        cu = self.db.cursor()
        cu.execute("SELECT buildCount FROM Builds WHERE buildId=?",
                   buildId)
        res = cu.fetchall()
        if res:
            count = res[0][0] + 1
            cu.execute("""UPDATE Builds
                              SET buildCount=?,
                              status=?,
                              statusMessage=?
                              WHERE buildId=?""", count, jobstatus.WAITING,
                              jobstatus.statusNames[jobstatus.WAITING],
                              buildId)
            return count
        else:
            return None

    @staticmethod
    def _filterBuildVisibility(rs, okHiddenProjectIds, limitToUserId):
        # admins see all
        if not limitToUserId:
            return True
        else:
            # restrict hidden projects unless you're a member
            if (not rs['isPrivate'] or (rs['isPrivate'] and (rs['projectId'] in okHiddenProjectIds))) and \
               (rs['isPublished'] or ((not rs['isPublished']) and (rs['role'] in ('Product Developer', 'Product Owner')))):
                return True
        return False

    def getAllBuildsByType(self, imageType, requestingUserId, 
                           limitToUserId=False):
        # By default, select builds that have at least one file that is
        # not a failed build log.
        extraSelect = ''
        extraJoin = ' LEFT JOIN buildFiles bdf ON (bdf.buildId = b.buildId)'
        extraWhere = ''' AND EXISTS (
            SELECT * FROM BuildFiles bf
            WHERE bf.buildId = b.buildId
            AND bf.title != 'Failed build log' ) '''
        if imageType == 'AMI':
            # Cancel out build file test; AMIs don't have files
            extraWhere = ''

            # Extra selects:
            # awsCredentials cannot be a single -
            # We use it to mark that we did not have credentials set for this
            # EC2 target (as opposed to None for non-ec2 targets)
            extraSelect = ''', COALESCE(subq.creds, '-') AS awsCredentials,
                             bd.value AS amiId'''
            extraJoin += ''' LEFT OUTER JOIN
                             (SELECT tuc.userId AS userId,
                                     tc.credentials AS creds
                                FROM Targets
                                JOIN TargetUserCredentials AS tuc
                                     ON (Targets.targetId = tuc.targetId)
                                JOIN TargetCredentials AS tc
                                     ON (tuc.targetCredentialsId = tc.targetCredentialsId)
                               WHERE Targets.targetType = '%s'
                                 AND Targets.targetName = '%s') as subq
                              ON (b.createdBy = subq.userId)
                            ''' % (self.EC2TargetType, self.EC2TargetName)

            # make sure that this build has an amiId.  Since it doesn't
            # have any files (thus no sha1), we need to know that it
            # has an amiId to know it uploaded correctly
            extraJoin += ''' JOIN buildData bd
                             ON (bd.buildId  = b.buildId
                                 AND bd.name = 'amiId')'''
        elif imageType == 'VWS':
            # VWS as a build type doesn't currently exist, but any
            # image that is RAW_FS_IMAGE and build as a DOMU works.
            imageType = 'RAW_FS_IMAGE'
            extraJoin += ''' JOIN buildData bd ON (bd.buildId  = b.buildId
                                                   AND bd.name = 'XEN_DOMU')'''
        try:
            imageType = buildtypes.validBuildTypes[imageType]
        except KeyError:
            raise ParameterError('Unknown image type %r' % (imageType,))
        cu = self.db.cursor()
        # Get the list of hidden projects to accept if we need to filter
        okHiddenProjectIds = []
        if limitToUserId:
            cu.execute("""
                 SELECT pu.projectId
                 FROM   projectUsers pu JOIN projects p USING (projectId)
                 WHERE  p.hidden = 1 AND pu.userId = ?
                 """, requestingUserId)
            okHiddenProjectIds = [result[0] for result in cu.fetchall()]


        query = """SELECT p.projectId,
                    p.hostname,
                    b.buildId,
                    p.name AS productName,
                    p.description AS productDescription,
                    b.name AS buildName,
                    b.troveFlavor AS troveFlavor,
                    COALESCE(b.description,'') AS buildDescription,
                    COALESCE(pr.timePublished,0) != 0 AS isPublished,
                    p.hidden AS isPrivate,
                    COALESCE(u.username, 'Unknown') AS createdBy,
                    CASE
                        WHEN pu.level = 0 THEN 'Product Owner'
                        WHEN pu.level = 1 THEN 'Product Developer'
                        WHEN pu.level = 2 THEN 'Product User'
                        ELSE ''
                    END AS role
                    %(extraSelect)s
                 FROM projects p
                 JOIN builds b USING (projectId)
                 LEFT OUTER JOIN publishedReleases pr USING (pubReleaseId)
                 LEFT OUTER JOIN users u ON (b.createdBy = u.userId)
                 LEFT OUTER JOIN projectUsers pu
                    ON (b.projectId = pu.projectId AND pu.userId = ?)
                 %(extraJoin)s
             WHERE b.buildType = ?
             %(extraWhere)s"""
        query = query % {'extraWhere' : extraWhere,
                         'extraSelect' : extraSelect,
                         'extraJoin' : extraJoin}
        keys = ['projectId', 'hostname', 'buildId', 'productName',
                'productDescription', 'buildName', 'buildDescription',
                'isPublished', 'isPrivate', 'createdBy', 'role',
                'awsCredentials', 'amiId', 'troveFlavor',
                ]

        cu.execute(query, requestingUserId, imageType)
        out = []
        for row in cu:
            if not self._filterBuildVisibility(row,
                    okHiddenProjectIds, limitToUserId):
                continue
            outRow = {}
            for key in keys:
                value = row.pop(key, None)
                if key == 'awsCredentials':
                    if value == '-':
                        value = 'Unknown'
                    elif value:
                        value = data.unmarshalTargetUserCredentials(value)
                        value = value.get('accountId')
                    # Keep the old interface for getAllBuildsByType
                    key = 'awsAccountNumber'
                elif key == 'troveFlavor':
                    key = 'architecture'
                    if value:
                        value = helperfuncs.getArchFromFlavor(value)
                if value is not None:
                    outRow[key] = value
            assert not row.fields
            out.append(outRow)
        return out

    def getAMIBuildsForProject(self, projectId):
        published = []
        unpublished = []
        cu = self.db.cursor()
        cu.execute("""SELECT COALESCE(pr.timePublished,0) != 0 AS isPublished,
                             bd.value AS amiId
                      FROM builds b
                          LEFT OUTER JOIN publishedReleases pr USING (pubReleaseId)
                          JOIN buildData bd ON (bd.buildId = b.buildId AND bd.name = 'amiId')
                      WHERE b.projectId = ?""", projectId)
        for res in cu.fetchall():
            if res[0]:
                published.append(res[1])
            else:
                unpublished.append(res[1])
        return published, unpublished

# XXX This table is deprecated in favor of BuildDataTable
class ReleaseDataTable(data.GenericDataTable):
    name = "ReleaseData"

class BuildDataTable(data.GenericDataTable):
    name = "BuildData"

