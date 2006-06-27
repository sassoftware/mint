#!/usr/bin/python2.4
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper

from mint import config
from mint import producttypes

class ConfigTest(MintRepositoryHelper):
    # these tests should be fairly specific in nature, since testing cfg
    # in general terms will overlap conary.
    def testProductTypes(self):
        cEnum = config.CfgProductEnum()

        self.failIf(dict([(x[0].lower(), x[1]) for x in \
                          producttypes.validProductTypes.iteritems()]) != \
                    cEnum.validValues,
                    "Base value list can't be compared. "
                    "results of this test will be invalid")

        self.failIf(dict([(x[1],x[0]) for x in cEnum.origName.iteritems()]) !=\
                    producttypes.validProductTypes,
                    "Original names are not correct, no basis for comparison")

        for productType in producttypes.validProductTypes.keys():
            # productType is a string
            self.failIf(cEnum.parseString(productType) != \
                        producttypes.__dict__[productType],
                        "cfg parsing did not translate %s correctly" % \
                        productType)

        for enumVal in producttypes.TYPES:
            # enumVal is an int
            self.failIf(cEnum.parseString(cEnum.format(enumVal)) != enumVal,
                        "Enum format didn't divine correct name for %d" % \
                        enumVal)

        # if we get here, there are no apparent issues with the CfgProductType
        # class. errors with the cfg object manipulation generated elsewhere.
        cfg = config.MintConfig()
        self.failIf(cfg.visibleProductTypes,
                    "Product type illegally appeared as visible")

        cfg.configLine("visibleProductTypes INSTALLABLE_ISO")
        self.failIf(cfg.visibleProductTypes != [producttypes.INSTALLABLE_ISO],
                    "visibleProductTypes did not incorporate first product type")

        cfg.configLine("visibleProductTypes RAW_HD_IMAGE")
        self.failIf(cfg.visibleProductTypes != \
                    [producttypes.INSTALLABLE_ISO, producttypes.RAW_HD_IMAGE],
                    "visibleProductTypes did not properly incorporate "
                    "a second product")

if __name__ == "__main__":
    testsuite.main()
