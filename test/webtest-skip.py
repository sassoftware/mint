#!/usr/bin/python2.4
#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import testsuite
testsuite.setup()

import rephelp

class MintTest(rephelp.WebRepositoryHelper):
    def testLogin(self):
        page = self.assertContent('/login', 'Please log in to use the the rpath Linux Mint custom distribution server:')

if __name__ == "__main__":
    testsuite.main()
