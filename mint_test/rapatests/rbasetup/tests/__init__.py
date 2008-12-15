#
# Copyright (C) 2006-2008 rPath, Inc.
# All rights reserved.
#
import raa.web
import cherrypy
import raatest

from rPath.outboundmirror.srv.outboundmirror import OutboundMirror

from mintraatests import webPluginTest
import os
import re
import StringIO


class rBASetupTest(raatest.rAATest):
    def setUp(self):
        self.raaFramework = webPluginTest()
        self.pseudoroot = raa.web.getWebRoot().outboundmirror.OutboundMirror
        raatest.rAATest.setUp(self)

    def tearDown(self):
        raatest.rAATest.tearDown(self)

    def test_index(self):
        # TODO
