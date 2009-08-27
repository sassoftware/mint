import cherrypy
import os
import raatest
import raa.web

from conary import dbstore
from conary.server import schema

from testrunner import pathManager

class webPluginTest(raatest.webTest):
    def __init__(
        self, module = None, init = True, preInit = None, preConst = None):

        def func(rt):
            dirs = pathManager.getPath('RAA_PLUGINS_PATH')
            raa.web.getWebRoot().servicecfg.pluginDirs = dirs.split(':')
            if preInit:
                preInit(rt)

        return raatest.webTest.__init__(
            self, module=module, init=init, preInit=func, preConst=preConst)
