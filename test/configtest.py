#!/usr/bin/python2.4
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper

from mint import config
from mint import buildtypes

class ConfigTest(MintRepositoryHelper):
    # these tests should be fairly specific in nature, since testing cfg
    # in general terms will overlap conary.
    def testBuildTypes(self):
        cEnum = config.CfgBuildEnum()

        self.failIf(dict([(x[0].lower(), x[1]) for x in \
                          buildtypes.validBuildTypes.iteritems()]) != \
                    cEnum.validValues,
                    "Base value list can't be compared. "
                    "results of this test will be invalid")

        self.failIf(dict([(x[1],x[0]) for x in cEnum.origName.iteritems()]) !=\
                    buildtypes.validBuildTypes,
                    "Original names are not correct, no basis for comparison")

        for buildType in buildtypes.validBuildTypes.keys():
            # buildType is a string
            self.failIf(cEnum.parseString(buildType) != \
                        buildtypes.__dict__[buildType],
                        "cfg parsing did not translate %s correctly" % \
                        buildType)

        for enumVal in buildtypes.TYPES:
            # enumVal is an int
            self.failIf(cEnum.parseString(cEnum.format(enumVal)) != enumVal,
                        "Enum format didn't divine correct name for %d" % \
                        enumVal)

        # if we get here, there are no apparent issues with the CfgBuildType
        # class. errors with the cfg object manipulation generated elsewhere.
        cfg = config.MintConfig()
        self.failIf(cfg.visibleBuildTypes,
                    "Build type illegally appeared as visible")

        cfg.configLine("visibleBuildTypes INSTALLABLE_ISO")
        self.failIf(cfg.visibleBuildTypes != [buildtypes.INSTALLABLE_ISO],
                    "visibleBuildTypes did not incorporate first build type")

        cfg.configLine("visibleBuildTypes RAW_HD_IMAGE")
        self.failIf(cfg.visibleBuildTypes != \
                    [buildtypes.INSTALLABLE_ISO, buildtypes.RAW_HD_IMAGE],
                    "visibleBuildTypes did not properly incorporate "
                    "a second build")

if __name__ == "__main__":
    testsuite.main()
