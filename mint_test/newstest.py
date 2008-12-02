#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import testsuite
testsuite.setup()

import fixtures
class NewsTest(fixtures.FixturedUnitTest):
    @fixtures.fixture('Full')
    def testBasicNews(self, db, data):
        client = self.getClient('user')
        assert(client.getNews())

    @fixtures.fixture('Full')
    def testBasicNewsLink(self, db, data):
        client = self.getClient('user')
        assert(client.getNewsLink())


if __name__ == "__main__":
    testsuite.main()
