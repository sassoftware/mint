#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

import fixtures
from mint import users

def rejectMail(fromEmail, fromEmailName, toEmail, subject, body):
    raise users.MailError

def passMail(fromEmail, fromEmailName, toEmail, subject, body):
    return

class GroupTroveTest(fixtures.FixturedUnitTest):
    @fixtures.fixture('Full')
    def testEmailRejection(self, db, data):
        client = self.getClient("admin")
        cu = db.cursor()
        cu.execute("UPDATE Users SET email='nobody@localhost' WHERE userId=?",
                   data['nobody'])
        db.commit()
        sendMailWithChecks = users.sendMailWithChecks
        try:
            users.sendMailWithChecks = rejectMail
            client.notifyUsers('test', 'test')
            cu.execute('SELECT userId FROM Confirmations')
            confirmList = [x[0] for x in cu.fetchall()]
            self.failIf(data['admin'] in confirmList,
                        "Admin account was placed in confirm list")
            self.failIf(data['nobody'] in confirmList,
                        "local account was placed in confirm list")
            for userId in data['owner'], data['user'], data['developer']:
                self.failIf(userId not in confirmList,
                            "Account was not placed in confirmation jail.")
        finally:
            users.sendMailWithChecks = sendMailWithChecks

    @fixtures.fixture('Full')
    def testEmailConfirmation(self, db, data):
        client = self.getClient("admin")
        cu = db.cursor()
        sendMailWithChecks = users.sendMailWithChecks
        try:
            users.sendMailWithChecks = passMail
            client.notifyUsers('test', 'test')
            cu.execute('SELECT userId FROM Confirmations')
            self.failIf(cu.fetchall(),
                        "Account erroneously forced to confirm.")
        finally:
            users.sendMailWithChecks = sendMailWithChecks

if __name__ == "__main__":
    testsuite.main()
