# Copyright (c) 2006 rPath, Inc
# All rights reserved

from raa.modules.raawebplugin import rAAWebPlugin
import turbogears
import os
from os import path
import re
import cherrypy

class RBALog(rAAWebPlugin):
    '''
        Display jobserver log
    '''
    displayName = _("View rBuilder Log")

    logPath = 'srv/rbuilder/logs/job-server.log'
    jsrvPath = '/srv/rbuilder/jobserver/'

    @turbogears.expose(html="rPath.rbalog.log")
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def index(self):
        return dict(logText=self.getLog())

    @turbogears.expose()
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def rBuilderLog(self):
        cherrypy.response.headerMap['Content-Type'] = 'text/plain'
        return self.getLog()

    def getLog(self):
        try:
            dirs = os.listdir(self.jsrvPath)
            jsdir = [x for x in dirs if re.match('^\d+\.\d+\.\d+$', x)][0]
            fullPath = path.join(self.jsrvPath, jsdir, self.logPath)
            f = open(fullPath)
            logText = f.read()
            f.close()
        except (IOError, AttributeError, IndexError, OSError):
            logText = 'Error:  Log file not found' 
        return logText
