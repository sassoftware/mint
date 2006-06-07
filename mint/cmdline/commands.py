#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#

from conary.lib import options

(NO_PARAM,  ONE_PARAM)  = (options.NO_PARAM, options.ONE_PARAM)
(OPT_PARAM, MULT_PARAM) = (options.OPT_PARAM, options.MULT_PARAM)

class RBuilderCommand(options.AbstractCommand):
    docs = {'config'             : ("Set config KEY to VALUE", "'KEY VALUE'"),
            'config-file'        : ("Read PATH config file", "PATH"),
            'skip-default-config': "Don't read default config file (~/.rbuilderrc)",
            'server'             : ("Set rBuilder server url to URL", "URL"),
           }

    def addParameters(self, argDef):
        d = {}
        d["config"] = MULT_PARAM
        d["config-file"] = MULT_PARAM
        d["skip-default-config"] = NO_PARAM
        d["server"] = ONE_PARAM
        argDef[self.defaultGroup] = d


_commands = []
def register(cmd):
    _commands.append(cmd)

