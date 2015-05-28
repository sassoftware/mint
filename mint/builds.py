#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from mint import buildtemplates
from mint import buildtypes
from mint import flavors
from mint import helperfuncs
from mint.db import builds
from mint.lib import database
from mint.lib.data import RDT_ENUM
from mint.mint_error import *

from conary import versions
from conary.deps import deps

PROTOCOL_VERSION = 1


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
    __slots__ = builds.BuildsTable.fields

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

    def getDefaultName(self):
        """ Returns a generated build name based on the group trove
            the build is based upon and its version. This should be
            as a default name if the user doesn't supply one in the UI."""
        return "%s=%s" % (self.getTroveName(),
                self.getTroveVersion().trailingRevision().asString())

    def getDesc(self):
        return self.description

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

    def setBuildType(self, buildType):
        assert(buildType in buildtypes.TYPES)
        self.buildType = buildType
        return self.server.setBuildType(self.buildId, buildType)

    def getBuildType(self):
        return self.buildType

    def getFiles(self):
        filenames = self.server.getBuildFilenames(self.buildId)
        for bf in filenames:
            if 'size' in bf:
                bf['size'] = int(bf['size'])
        return filenames

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
