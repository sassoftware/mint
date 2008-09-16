#
# Copyright (C) 2006-2007 rPath, Inc.
# All rights reserved.
#
import cherrypy
import raatest

from rPath.loadmirror.web.loadmirror import LoadMirror

from mintraatests import webPluginTest

class LoadMirrorTest(raatest.rAATest):
    def setUp(self):
        self.raaFramework = webPluginTest()
        self.raaFramework.pseudoroot = cherrypy.root.loadmirror.LoadMirror
        raatest.rAATest.setUp(self)

    def test_indexTitle(self):
        self.requestWithIdent("/loadmirror/LoadMirror/?debug")
        assert "<title>mirror pre-load</title>" in cherrypy.response.body[0].lower()
