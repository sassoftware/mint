#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint.userlevels import myProjectCompare

class ProjectTest(MintRepositoryHelper):
    def testMyProjectCompare(self):
        if not isinstance(myProjectCompare(('not tested', 1), ('ignored', 0)), int):
            self.fail("myProjectCompare did not return an int")
        if not isinstance(myProjectCompare(('not tested', 1L), ('ignored', 0L)), int):
            self.fail("myProjectCompare did not return an int")

if __name__ == "__main__":
    testsuite.main()
