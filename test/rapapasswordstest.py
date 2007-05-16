#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import testsuite
testsuite.setup()

import os
import sys
import time
import tempfile

import fixtures

from mint import rapapasswords

class rAPAPasswordsTest(fixtures.FixturedUnitTest):
    @fixtures.fixture("Full")
    def testPasswords(self, db, data):
        client = self.getClient('admin')
        self.failIf(client.getrAPAPassword('foo.bar.baz', 'role'), 
                     'Value returned when not present.')
        client.setrAPAPassword('blah.bar.baz', 'foo_bar_baz', 'passwd', 'role')
        client.setrAPAPassword('foo.bar.baz', 'foo_bar_baz', 'passwd', 'role')
        client.setrAPAPassword('foo.bar.baz', 'foo_bar_baz2', 'passwd2', 'role2')
        user, passwd = client.getrAPAPassword('foo.bar.baz', 'role') 
        self.failIf(user != 'foo_bar_baz' or passwd != 'passwd', "Incorrect user returned")
        user, passwd = client.getrAPAPassword('foo.bar.baz', 'role2') 
        self.failIf(user != 'foo_bar_baz2' or passwd != 'passwd2', "Incorrect user returned")

        client.setrAPAPassword('foo.bar.baz', 'foo_bar_baz', 'passwd_changed', 'role')
        user, passwd = client.getrAPAPassword('foo.bar.baz', 'role') 
        self.failIf(user != 'foo_bar_baz' or passwd != 'passwd_changed', "Password not updated.")
if __name__ == "__main__":
    testsuite.main()
