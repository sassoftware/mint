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
        page = self.assertCode('/register', code = 200)

        page.postForm(0, self.postAssertCode,
                      {'username': 'testuser',
                       'password': 'testpass1',
                       'password2': 'testpass1',
                       'email': 'test@example.com'},
                    301)

        page = self.assertCode('/login', code = 200)
        self.activateUsers()
        page.postForm(0, self.postAssertCode,
            {'username': 'testuser',
             'password': 'testpass1',
             'submit': 'Log In'},
             301)
             

        page = self.assertCode('/newProject', code = 200)
        
        page.postForm(0, self.postAssertCode,
            {'title': 'Test Project',
             'hostname': 'test'}, 301)

        
if __name__ == "__main__":
    testsuite.main()
