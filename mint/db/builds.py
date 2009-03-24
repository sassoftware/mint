import time

from mint import buildtypes
from mint import helperfuncs
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
              'deleted', 'buildCount', 'productVersionId', 'stageName']

    def iterBuildsForProject(self, projectId):
        """ Returns an iterator over the all of the buildIds in a given
            project with ID projectId. The iterator is ordered by the date
            the associated group grove last changed in descending order
            (most to lease recent)."""

        cu = self.db.cursor()

        cu.execute("""SELECT buildId FROM BuildsView
                      WHERE projectId=? AND
                            troveName IS NOT NULL AND
                            troveVersion IS NOT NULL AND
                            troveFlavor IS NOT NULL AND
                            troveLastChanged IS NOT NULL
                            ORDER BY troveLastChanged DESC, buildId""",
                   projectId)

        for results in cu.fetchall():
            yield int(results[0])

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
                      FROM BuildsView
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
        cu.execute("SELECT COALESCE((SELECT pubReleaseId FROM BuildsView WHERE buildId=?), 0)", buildId)
        pubReleaseId = cu.fetchone()[0]
        if pubReleaseId:
            cu.execute("SELECT timePublished FROM PublishedReleases WHERE pubReleaseId = ?", pubReleaseId)
            res = cu.fetchone()
            if res:
                return bool(res[0])
        return False

    def getUnpublishedBuilds(self, projectId):
        cu = self.db.cursor()
        cu.execute("""SELECT buildId FROM BuildsView
                      WHERE projectId = ? AND pubReleaseId IS NULL""",
                      projectId)
        res = cu.fetchall()
        return [x[0] for x in res]

    def deleteBuild(self, buildId, commit=True):
        try:
            cu = self.db.cursor()
            cu.execute("UPDATE Builds SET deleted=1 WHERE buildId=?", buildId)
        except:
            self.db.rollback()
            raise
        else:
            if commit:
                self.db.commit()

    def buildExists(self, buildId):
        cu = self.db.cursor()

        cu.execute("SELECT count(*) FROM BuildsView WHERE buildId=?", buildId)
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
                              SET buildCount=?
                              WHERE buildId=?""", count, buildId)
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
        extraWhere = ''
        # by default, we organize builds by sha1.  This assumes
        # that builds have one file and that one file is the build.
        # not sure how to deal w/ error logs being associated since
        # we don't have an error status.
        extraSelect = ', bdf.sha1'
        extraJoin = ' JOIN buildFiles bdf ON (bdf.buildId = b.buildId)'
        if imageType == 'AMI':
            # cancel out sha1 join - we don't have any files with this build!
            extraJoin = ''

            # Extra selects:
            # add in awsAccount if it exists.
            extraSelect = ''', COALESCE(ud.value,'Unknown') AS awsAccountNumber,
                             bd.value AS amiId'''
            extraJoin += '''LEFT OUTER JOIN userData ud
                            ON (b.createdBy = ud.userId
                                AND ud.name = 'awsAccountNumber')'''

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
                                                   AND bd.name = "XEN_DOMU")'''
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
             WHERE b.buildType = ? AND b.deleted = 0
             %(extraWhere)s"""
        query = query % {'extraWhere' : extraWhere,
                         'extraSelect' : extraSelect,
                         'extraJoin' : extraJoin}

        cu.execute(query, requestingUserId, imageType)
        return [ rs for rs in cu.fetchall_dict()
                if self._filterBuildVisibility(rs, okHiddenProjectIds,
                                               limitToUserId)]

    def getAMIBuildsForProject(self, projectId):
        published = []
        unpublished = []
        cu = self.db.cursor()
        cu.execute("""SELECT COALESCE(pr.timePublished,0) != 0 AS isPublished,
                             bd.value AS amiId
                      FROM builds b
                          LEFT OUTER JOIN publishedReleases pr USING (pubReleaseId)
                          JOIN buildData bd ON (bd.buildId = b.buildId AND bd.name = 'amiId')
                      WHERE b.projectId = ? AND b.deleted = 0""", projectId)
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

