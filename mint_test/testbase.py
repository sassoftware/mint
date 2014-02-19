#
# Copyright (c) 2008 rPath, Inc.  All Rights Reserved.
#


import tempfile

from testrunner import testcase

from conary.lib import util

class TestCase(testcase.TestCase):
    def setUp(self):
        testcase.TestCase.setUp(self)
        self.workDir = tempfile.mkdtemp(prefix='catalog-service-test-')
        self.cleanupDir = True

    def tearDown(self):
        testcase.TestCase.tearDown(self)
        if self.cleanupDir:
            util.rmtree(self.workDir, ignore_errors = True)

    @staticmethod
    def normalizeXML(data):
        """lxml will produce the header with single quotes for its attributes,
        while xmllint uses double quotes. This function normalizes the data"""
        return data.replace(
            "<?xml version='1.0' encoding='UTF-8'?>",
            '<?xml version="1.0" encoding="UTF-8"?>').strip()

    def assertXMLEquals(self, first, second):
        self.failUnlessEqual(self.normalizeXML(first),
                             self.normalizeXML(second))
