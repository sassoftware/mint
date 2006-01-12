#!/usr/bin/python2.4
#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

import testsuite
testsuite.setup()

import unittest

from mint.web.cache import AgedDict

class CacheTest(unittest.TestCase):
    def testAgedDict(self):
        ad = AgedDict()

        ad['testkey'] = 'testval'
        assert(ad['testkey'] == 'testval')

        ad.ages['testkey'] = 0

        try:
            tmp = ad['testkey']
        except AttributeError:
            pass
        except:
            self.fail("AgedDict failed to time out value")

        try:
            tmp = ad['notpresent']
        except AttributeError:
            pass
        except:
            sel.fail("AgedDict failed to report missing key")

        # test 'in'
        ad['testkey'] = 0
        assert('testkey' in ad)
        assert('notpresent' not in ad)


if __name__ == "__main__":
    testsuite.main()
