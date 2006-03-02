#!/usr/bin/python2.4
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper

from mint import config
from mint import releasetypes

class ConfigTest(MintRepositoryHelper):
    # these tests should be fairly specific in nature, since testing cfg
    # in general terms will overlap conary.
    def testImageTypes(self):
        cEnum = config.CfgImageEnum()

        self.failIf(dict([(x[0].lower(), x[1]) for x in \
                          releasetypes.validImageTypes.iteritems()]) != \
                    cEnum.validValues,
                    "Base value list can't be compared. "
                    "results of this test will be invalid")

        self.failIf(dict([(x[1],x[0]) for x in cEnum.origName.iteritems()]) !=\
                    releasetypes.validImageTypes,
                    "Original names are not correct, no basis for comparison")

        for imageType in releasetypes.validImageTypes.keys():
            # imageType is a string
            self.failIf(cEnum.parseString(imageType) != \
                        releasetypes.__dict__[imageType],
                        "cfg parsing did not translate %s correctly" % \
                        imageType)

        for enumVal in releasetypes.TYPES:
            # enumVal is an int
            self.failIf(cEnum.parseString(cEnum.format(enumVal)) != enumVal,
                        "Enum format didn't divine correct name for %d" % \
                        enumVal)

        # if we get here, there are no apparent issues with the CfgImageType
        # class. errors with the cfg object manipulation generated elsewhere.
        cfg = config.MintConfig()
        self.failIf(cfg.visibleImageTypes,
                    "Image type illegally appeared as visible")

        cfg.configLine("visibleImageTypes INSTALLABLE_ISO")
        self.failIf(cfg.visibleImageTypes != [releasetypes.INSTALLABLE_ISO],
                    "visibleImageTypes did not incorporate first release type")

        cfg.configLine("visibleImageTypes RAW_HD_IMAGE")
        self.failIf(cfg.visibleImageTypes != \
                    [releasetypes.INSTALLABLE_ISO, releasetypes.RAW_HD_IMAGE],
                    "visibleImageTypes did not properly incorporate "
                    "a second release")

if __name__ == "__main__":
    testsuite.main()
