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
              'buildCount', 'productVersionId', 'stageName', 'proddef_version',
              'status', 'statusMessage', 'job_uuid', 'base_image',
              'image_model',
              ]

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
                                          troveLastChanged=?,
                                          image_model=NULL
                      WHERE buildId=?""",
                   troveName, troveVersion,
                   troveFlavor, time.time(),
                   buildId)
        self.db.commit()
        return 0

    def setModel(self, buildId, imageModel):
        cu = self.db.cursor()
        cu.execute("UPDATE Builds SET image_model = ? WHERE buildId = ?",
                ''.join(imageModel), buildId)
        self.db.commit()

    def _getStageId(self, cu, projectBranchId, stageName):
        cu.execute("""SELECT stage_id FROM project_branch_stage
            WHERE project_branch_id = ? AND name = ?""",
            projectBranchId, stageName)
        row = cu.fetchone()
        if not row:
            return None
        return row[0]

    def setProductVersion(self, buildId, versionId, stageName,
            proddefVersion=None):
        cu = self.db.cursor()
        stageId = self._getStageId(cu, versionId, stageName)
        if proddefVersion:
            proddefVersion = str(proddefVersion)
        else:
            proddefVersion = None
        cu.execute("""UPDATE Builds SET productVersionId=?,
                                          stageId=?,
                                          stageName=?,
                                          troveLastChanged=?,
                                          proddef_version=?
                      WHERE buildId=?""",
                   versionId, stageId, stageName,
                   time.time(), proddefVersion, buildId)
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
        extraSelect = ', NULL AS baseBuildId'
        extraJoin = ' LEFT JOIN buildFiles bdf ON (bdf.buildId = b.buildId)'
        extraWhere = ''' AND EXISTS (
            SELECT * FROM BuildFiles bf
            WHERE bf.buildId = b.buildId
            AND bf.title != 'Failed build log' ) '''
        if imageType == 'VWS':
            # VWS as a build type doesn't currently exist, but any
            # image that is RAW_FS_IMAGE and build as a DOMU works.
            imageType = 'RAW_FS_IMAGE'
            extraJoin += ''' JOIN buildData bd ON (bd.buildId  = b.buildId
                                                   AND bd.name = 'XEN_DOMU')'''
        try:
            imageTypeId = buildtypes.validBuildTypes[imageType]
        except KeyError:
            raise ParameterError('Unknown image type %r' % (imageType,))
        cu = self.db.cursor()
        # Get the list of hidden projects to accept if we need to filter
        okHiddenProjectIds = []
        if limitToUserId:
            cu.execute("""
                 SELECT pu.projectId
                 FROM   projectUsers pu JOIN projects p USING (projectId)
                 WHERE  p.hidden AND pu.userId = ?
                 """, requestingUserId)
            okHiddenProjectIds = [result[0] for result in cu.fetchall()]


        queryTmpl = """SELECT p.projectId,
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
        query = queryTmpl % {'extraWhere' : extraWhere,
                         'extraSelect' : extraSelect,
                         'extraJoin' : extraJoin}
        keys = ['projectId', 'hostname', 'buildId', 'productName',
                'productDescription', 'buildName', 'buildDescription',
                'isPublished', 'isPrivate', 'createdBy', 'role',
                'troveFlavor', 'baseBuildId',
                ]

        imageIdToImageHash = {}
        cu.execute(query, requestingUserId, imageTypeId)
        out = []
        for row in cu:
            if not self._filterBuildVisibility(row,
                    okHiddenProjectIds, limitToUserId):
                continue
            outRow = {}
            for key in keys:
                value = row.pop(key, None)
                if key == 'troveFlavor':
                    key = 'architecture'
                    if value:
                        value = helperfuncs.getArchFromFlavor(value)
                if value is not None:
                    outRow[key] = value
            # Expose the build type as well
            outRow['imageType'] = imageType
            assert not row.fields
            out.append(outRow)
            imageIdToImageHash[outRow['buildId']] = outRow
        return out


class BuildDataTable(data.GenericDataTable):
    name = "BuildData"


class AuthTokensTable(database.KeyedTable):
    name = 'auth_tokens'
    key = 'token_id'

    fields = [
            'token_id',
            'token',
            'expires_date',
            'user_id',
            'image_id',
            ]

    def addToken(self, token, user_id, image_id=None):
        cu = self.db.cursor()
        cu.execute("""INSERT INTO auth_tokens
            (token, expires_date, user_id, image_id)
            VALUES (?, now() + '1 day', ?, ?)""",
            token, user_id, image_id)

    def removeTokenByImage(self, image_id):
        cu = self.db.cursor()
        cu.execute("DELETE FROM auth_tokens WHERE image_id = ?", image_id)
