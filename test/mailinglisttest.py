#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#
import re
import testsuite
import unittest
testsuite.setup()

from mint import mailinglists
from mint.mailinglists import MailingListException

class StubServer:
    fail = False

    # set up so we can fail on a given call
    def checkFail(self, call):
        if self.fail == call or self.fail == True:
            raise MailingListException("fail")

    def listAdvertisedLists(self, pcre):
        self.checkFail('listAdvertisedLists')

        pcre = re.compile(pcre)
        r = [('mailman', 'Mailman Internal List'),
             ('project-commits', 'Description'),
             ('project2-commits', 'Description'),
            ]
        return [x for x in r if pcre.match(x[0])]

    def createList(self, *args, **kwargs):
        self.checkFail('createList')
        if args[5]:
            return args[5]

    def setOptions(self, *args, **kwargs):
        self.checkFail('setOptions')
        return True

    def deleteList(self, *args, **kwargs):
        self.checkFail('deleteList')
        return True

    def getOptions(self, *args, **kwargs):
        self.checkFail('getOptions')
        return {'owner': False}

    def resetListPassword(self, *args, **kwargs):
        self.checkFail('resetListPassword')
        return True


class MailmanTest(unittest.TestCase):
    def setUp(self):
        self.mmclient = mailinglists.MailingListClient('http://')
        self.mmclient.server.Mailman = StubServer()
        self.mmclient.server.Mailman.fail = False

    def setFail(self, call = True):
        self.mmclient.server.Mailman.fail = call

    def testListAllLists(self):
        r = self.mmclient.list_lists('project')

        self.failUnlessEqual([(x.name, x.description) for x in r], [('project-commits', 'Description'),])

        self.setFail()
        self.assertRaises(MailingListException, self.mmclient.list_lists, 'project')

    def testAddList(self):
        # no password, mailman generates one
        r = self.mmclient.add_list('', 'newname', '', 'desc', '')
        self.failUnlessEqual(r, False)

        # specify a password
        r = self.mmclient.add_list('', 'newname', 'specified', 'desc', '')
        self.failUnlessEqual(r, True)

        self.setFail('createList')
        self.assertRaises(MailingListException, self.mmclient.add_list,
            '', 'newname', '', 'desc', '')

        self.setFail('setOptions')
        self.assertRaises(MailingListException, self.mmclient.add_list,
            '', 'newname', 'specified', 'desc', '')

    def testDeleteList(self):
        r = self.mmclient.delete_list('pw', 'testlist')
        self.failUnlessEqual(r, True)

        self.setFail()
        self.assertRaises(MailingListException, self.mmclient.delete_list, 'pw', 'testlist')

    def testSetOwners(self):
        r = self.mmclient.set_owners('testlist', 'pw', ['owner'])
        self.failUnlessEqual(r, True)

        self.setFail()
        self.assertRaises(MailingListException, self.mmclient.set_owners,
            'testlist', 'pw', ['owner'])

    def testGetOwners(self):
        r = self.mmclient.get_owners('testlist', 'pw')
        self.failUnlessEqual(r, False)

        self.setFail()
        self.assertRaises(MailingListException, self.mmclient.get_owners,
            'testlist', 'pw')

    def testOrphanLists(self):
        r = self.mmclient.orphan_lists('pw', 'project')
        self.failUnlessEqual(r, True)

        self.setFail("setOptions")
        self.assertRaises(MailingListException, self.mmclient.orphan_lists, 'pw', 'project')

        self.setFail("resetListPassword")
        self.assertRaises(MailingListException, self.mmclient.orphan_lists, 'pw', 'project')

    def testAdoptLists(self):
        class Auth: pass
        auth = Auth()
        auth.email = "email@example.com"

        r = self.mmclient.adopt_lists(auth, 'pw', 'project')
        self.failUnlessEqual(r, None)

        self.setFail("setOptions")
        self.assertRaises(MailingListException,
            self.mmclient.adopt_lists, auth, 'pw', 'project')

        self.setFail("resetListPassword")
        self.assertRaises(MailingListException,
            self.mmclient.adopt_lists, auth, 'pw', 'project')

    def testResetListPassword(self):
        r = self.mmclient.reset_list_password('project', 'pw')
        self.failUnlessEqual(r, True)

        self.setFail()
        self.assertRaises(MailingListException,
            self.mmclient.reset_list_password, 'project', 'pw')

    def testGetLists(self):
        r = mailinglists.GetLists('project',
            [mailinglists.PROJECT_DEVEL,
             mailinglists.PROJECT_BUGS])
        self.failUnlessEqual(r.keys(), ['project-bugs', 'project-devel'])

        r = mailinglists.DefaultLists('project')
        self.failUnlessEqual(r.keys(), [])

    def testException(self):
        m = MailingListException("string")
        self.failUnlessEqual(str(m), "string")


if __name__ == "__main__":
    testsuite.main()
