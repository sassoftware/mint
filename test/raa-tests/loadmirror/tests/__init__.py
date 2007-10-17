#
# Copyright (C) 2006 rPath, Inc.
# All rights reserved.
#
import cherrypy
import raatest

from rPath.loadmirror.web.loadmirror import LoadMirror

from raatests import webPluginTest
raaFramework = webPluginTest()
raaFramework.pseudoroot = cherrypy.root.loadmirror.LoadMirror

class LoadMirrorTest(raatest.rAATest):
    def test_indexTitle(self):
        self.requestWithIdent("/loadmirror/LoadMirror/?debug")
        print cherrypy.response.body[0]
        assert "<title>mirror pre-load</title>" in cherrypy.response.body[0].lower()
