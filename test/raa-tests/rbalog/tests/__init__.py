#
# Copyright (C) 2006 rPath, Inc.
# All rights reserved.
#
import cherrypy
import raatest

from rPath.rbalog.web.rbalog import RBALog

from raatests import webPluginTest
raaFramework = webPluginTest()
raaFramework.pseudoroot = cherrypy.root.rbalog.RBALog

class RBALogTest(raatest.rAATest):
    def setUp(self):
        self.oldLogPath = RBALog.logPath
        RBALog.logPath = "/dev/null"
        raatest.rAATest.setUp(self)

    def tearDown(self):
        raatest.rAATest.tearDown(self)
        RBALog.logPath = self.oldLogPath

    def test_indexTitle(self):
        self.requestWithIdent("/rbalog/RBALog/?debug")
        print cherrypy.response.body[0]
        assert "<title>rbuilder log</title>" in cherrypy.response.body[0].lower()

    def test_downloadLog(self):
        return # SKIP because it's not isolated from the real world
        self.requestWithIdent("/rbalog/RBALog/rBuilderLog")
        print cherrypy.response.body
        assert [""] == cherrypy.response.body

    def test_downloadError(self):
        return # SKIP because it's not isolated from the real world
        RBALog.logPath = "/file/does/not/exist"
        self.requestWithIdent("/rbalog/RBALog/rBuilderLog")
        print cherrypy.response.body
        assert ["Error:  Log file not found"] == cherrypy.response.body
