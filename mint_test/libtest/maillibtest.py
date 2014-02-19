#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#

import smtplib

from mint_test.mint_rephelp import rephelp
from mint.lib import maillib

class MaillibTest(rephelp.RepositoryHelper):
    def testSMTPServerDisconnected(self):
        # RBL-8425
        origSMTP = smtplib.SMTP
        class MockSMTP(origSMTP):
            _counter = 1
            def connect(slf):
                pass
            def sendmail(slf, *args, **kwargs):
                slf.__class__._counter -= 1
                if slf._counter > 0:
                    raise smtplib.SMTPServerDisconnected("Connection unexpectedly closed")
            def close(slf):
                pass

        self.mock(smtplib, 'SMTP', MockSMTP)
        maillib.sendMail(fromEmail="from@example.com",
            fromEmailName="Joe Sender",
            toEmail="to@example.com",
            subject="email subject",
            body="email body")
        self.failUnlessEqual(MockSMTP._counter, 0)

        MockSMTP._counter = 5
        import logging
        import StringIO
        sio = StringIO.StringIO()
        handler = logging.StreamHandler(sio)
        handler.setLevel(logging.DEBUG)
        logger = logging.getLogger()
        logger.addHandler(handler)

        self.mock(smtplib, 'SMTP', MockSMTP)
        maillib.sendMail(fromEmail="from@example.com",
            fromEmailName="Joe Sender",
            toEmail="to@example.com",
            subject="email subject",
            body="email body")
        self.failUnlessEqual(MockSMTP._counter, 3)

        logger.removeHandler(handler)

        self.failUnlessEqual(sio.getvalue(),
            'Unable to send email to to@example.com:\nemail body\n')


