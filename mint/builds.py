#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

import time

from mint import buildtemplates
from mint import buildtypes
from mint import database
from mint import flavors
from mint import helperfuncs

from mint.data import RDT_ENUM
from mint.mint_error import *

from conary import versions
from conary.deps import deps

PROTOCOL_VERSION = 1

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
              'deleted', 'buildCount']

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

def getExtraFlags(buildFlavor):
    """Return a list of human-readable strings describing various
       characteristics that a flavor may have, defined by the
       flavorFlags dictionary in buildtypes.py.
    """
    if type(buildFlavor) == str:
        buildFlavor = deps.ThawFlavor(buildFlavor)

    extraFlags = []
    for flag, flavor in buildtypes.flavorFlagFlavors.items():
        if buildFlavor.stronglySatisfies(deps.parseFlavor(flavor)):
            extraFlags.append(buildtypes.flavorFlagNames[flag])

    return extraFlags


def getImportantFlavors(buildFlavor):
    """Return a list of machine-readable string suitable for storage
       in a database, to store various 'important' pieces of information about
       a flavor for quick retrieval and search.
    """
    if type(buildFlavor) == str:
        buildFlavor = deps.ThawFlavor(buildFlavor)

    flavors = []
    for id, flavor in buildtypes.flavorFlagFlavors.items():
        if buildFlavor is not None and buildFlavor.stronglySatisfies(deps.parseFlavor(flavor)):
            flavors.append(buildtypes.flavorFlagsFromId[id])

    return flavors


class Build(database.TableObject):
    __slots__ = BuildsTable.fields

    def __eq__(self, val):
        for item in [x for x in self.__slots__ if x not in \
                     ('buildId', 'troveLastChanged', 'timeCreated')]:
            if self.__getattribute__(item) != val.__getattribute__(item):
                return False
        return self.getDataDict() == val.getDataDict()

    def getItem(self, id):
        return self.server.getBuild(id)

    def getId(self):
        return self.buildId

    def getName(self):
        return self.name

    def setName(self, name):
        return self.server.setBuildName(self.buildId, name.strip())

    def getDefaultName(self):
        """ Returns a generated build name based on the group trove
            the build is based upon and its version. This should be
            as a default name if the user doesn't supply one in the UI."""
        return "%s=%s" % (self.getTroveName(),
                self.getTroveVersion().trailingRevision().asString())

    def getDesc(self):
        return self.description

    def setDesc(self, desc):
        return self.server.setBuildDesc(self.buildId, desc.strip())

    def getProjectId(self):
        return self.projectId

    def getUserId(self):
        return self.userId

    def getTrove(self):
        return tuple(self.server.getBuildTrove(self.buildId))

    def getTroveName(self):
        return self.troveName

    def getTroveVersion(self):
        return versions.ThawVersion(self.troveVersion)

    def getTroveFlavor(self):
        return deps.ThawFlavor(self.troveFlavor)

    def getChangedTime(self):
        return self.troveLastChanged

    def setTrove(self, troveName, troveVersion, troveFlavor):
        self.server.setBuildTrove(self.buildId,
            troveName, troveVersion, troveFlavor)
        self.refresh()

    def setBuildType(self, buildType):
        assert(buildType in buildtypes.TYPES)
        self.buildType = buildType
        return self.server.setBuildType(self.buildId, buildType)

    def getBuildType(self):
        if not self.buildType:
            self.buildType = self.server.getBuildType(self.buildId)
        return self.buildType

    def getStatus(self):
        return self.server.getBuildStatus(self.id)

    def getFiles(self):
        filenames = self.server.getBuildFilenames(self.buildId)
        for bf in filenames:
            if 'size' in bf:
                bf['size'] = int(bf['size'])
        return filenames

    def setFiles(self, filenames):
        for f in filenames:
            if len(f) == 4:
                f[2] = str(f[2])
        return self.server.setBuildFilenames(self.buildId, filenames)

    def getArch(self):
        """Return a printable representation of the build's architecture."""
        return helperfuncs.getArchFromFlavor(self.getTrove()[2])

    def getArchFlavor(self):
        """Return a conary.deps.Flavor object representing the build's architecture."""
        f = deps.ThawFlavor(self.getTrove()[2])

        if f.members and deps.DEP_CLASS_IS in f.members:
            # search through our pathSearchOrder and find the
            # best single architecture flavor for this build
            for x in [deps.ThawFlavor(y) for y in flavors.pathSearchOrder]:
                if f.satisfies(x):
                    return x
        return deps.Flavor()

    def setPublished(self, pubReleaseId, published):
        return self.server.setBuildPublished(self.buildId,
                pubReleaseId, published)

    def getPublished(self):
        return self.server.getBuildPublished(self.buildId)

    def getDataTemplate(self):
        return buildtemplates.getDataTemplate(self.buildType)

    def setDataValue(self, name, value, dataType = None, validate = True):
        template = self.getDataTemplate()
        if (name not in template and validate) or (dataType is None and not validate):
            raise BuildDataNameError("Named value not in data template: %s" %name)
        if dataType is None:
            dataType = template[name][0]
        if dataType == RDT_ENUM and value not in template[name][3].values():
            raise ParameterError("%s is not a legal enumerated value" % value)
        return self.server.setBuildDataValue(self.getId(), name, value, dataType)

    def getDataValue(self, name, validate = True):
        template = self.getDataTemplate()
        isPresent, val = self.server.getBuildDataValue(self.getId(), name)
        if (not isPresent and name not in template) and validate:
            raise BuildDataNameError( "%s not in data template" % name)
        if not isPresent and name in template:
            val = template[name][1]
        return val

    def getDataDict(self):
        dataDict = self.server.getBuildDataDict(self.getId())
        template = self.getDataTemplate()
        for name in list(template):
            if name not in dataDict:
                dataDict[name] = template[name][1]
        return dataDict

    def serialize(self):
        return self.server.serializeBuild(self.buildId)

    def addFileUrl(self, fileId, urlType, url):
        return self.server.addFileUrl(self.getId(), fileId, urlType, url)

    def removeFileUrl(self, fileId, urlId):
        return self.server.removeFileUrl(self.getId(), fileId, urlId)

    def deleteBuild(self):
        return self.server.deleteBuild(self.getId())

    def _getOverride(self):
        buildFlavor = self.getTrove()[2]
        if type(buildFlavor) == str:
            buildFlavor = deps.ThawFlavor(buildFlavor)
        for (buildType, flavorFlag), override \
          in buildtypes.typeFlavorOverride.iteritems():
            if buildType != self.getBuildType():
                continue

            flavor = buildtypes.flavorFlagFlavors[flavorFlag]
            if buildFlavor.stronglySatisfies(deps.parseFlavor(flavor)):
                return override

        return {}

    def getMarketingName(self, buildFile=None):
        '''
        Return the marketing name for display on build or release pages
        taking into account any variations related to the flavors the
        build was created with; e.g. a domU HD image should not use the
        QEMU/Parallels branding.
        '''

        override = self._getOverride().get('marketingName', None)
        if override is not None:
            name = override
        else:
            name = buildtypes.typeNamesMarketing[self.getBuildType()]

        if 'CD/DVD' in name and buildFile and buildFile.has_key('size'):
            disc_type = buildFile['size'] > 734003200 and 'DVD' or 'CD'
            name = name.replace('CD/DVD', disc_type)

        return name

    def getBrandingIcon(self):
        '''
        Return the icon to be placed beneath build types with some kind
        of third-party download, e.g. a Parallels icon for HD images.
        Check for any flavor qualifications (e.g. the Parallels example
        will not match domU groups.
        '''

        override = self._getOverride().get('icon', None)
        if override is not None:
            return override
        else:
            return buildtypes.buildTypeIcons.get(self.getBuildType(), None)

    def getBaseFileName(self):
        """
        Return the baseFileName of a build. This was either set by the user
        from advanced options or is <hostname>-<upstream version>-<arch>
        Note this is not the full build filename: the extension is not supplied.
        """
        return self.server.getBuildBaseFileName(self.buildId)

    def getBuildPageUrl(self):
        """
        Return the URL to the build's rBuilder page.
        """
        return self.server.getBuildPageUrl(self.buildId)
