#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

import fixtures
class NewsTest(fixtures.FixturedUnitTest):
    @fixtures.fixture('Full')
    def testBasicNews(self, db, data):
        client = self.getClient('user')
        assert(not client.getNews())

    @fixtures.fixture('Full')
    def testBasicNewsLink(self, db, data):
        client = self.getClient('user')
        assert(not client.getNewsLink())


if __name__ == "__main__":
    testsuite.main()
