import cherrypy
import os
import raatest

from conary import dbstore
from conary.server import schema

class webPluginTest(raatest.webTest):
    def __init__(
        self, module = None, init = True, preInit = None, preConst = None):

        def func(rt):
            cherrypy.root.servicecfg.pluginDirs = [os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "raaplugins"))]
            if preInit:
                preInit(rt)

        return raatest.webTest.__init__(
            self, module=module, init=init, preInit=func, preConst=preConst)
