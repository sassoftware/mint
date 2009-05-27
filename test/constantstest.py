#!/usr/bin/python2.4
#
# Copyright (c) 2006-2007 rPath, Inc.
#
# All rights reserved
#

import testsuite
testsuite.setup()

from testrunner import testhelp

from mint import buildtypes as refbuildtypes

class ConstantsTest(testhelp.TestCase):
    def testCompareTypes(self):
        try:
            from jobslave import buildtypes
        except ImportError:
            raise testhelp.SkipTestException, 'Jobslave not found, cannot verify constants'

        if buildtypes.validBuildTypes != refbuildtypes.validBuildTypes:
            types = set(buildtypes.validBuildTypes.iteritems())
            reftypes = set(refbuildtypes.validBuildTypes.iteritems())
            missing = reftypes.difference(types)
            extra = types.difference(reftypes)

            errorStr = ""
            if missing:
                errorStr += ', '.join([x[0] for x in missing]) + \
                    " need%s to be defined" % (len(missing) == 1 and 's' or '')
            self.failIf(errorStr, errorStr + ". This test can safely be "
                        "disabled if not comparing tip to tip.")


if __name__ == "__main__":
    testsuite.main()
