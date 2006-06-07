#!/usr/bin/python
import os
import sys

from conary.lib import options, util, log
from conary.conarycfg import ConfigFile
from conary.conaryclient import cmdline

from mint import constants
from mint.client import MintClient

sys.excepthook = util.genExcepthook()

class RBuilderShellConfig(ConfigFile):
    serverUrl = None

    def __init__(self, readConfigFiles = True):
        ConfigFile.__init__(self)
        if os.environ.has_key("HOME"):
            self.read(os.environ["HOME"] + "/" + ".rbuilderrc", exception=False)


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


class ConfigCommand(RBuilderCommand):
    commands = ['config']
    docs = {'show-passwords' : 'do not mask passwords'}

    def addParameters(self, argDef):
         RBuilderCommand.addParameters(self, argDef)
         argDef["show-passwords"] = NO_PARAM

    def runCommand(self, client, cfg, argSet, args):
        if len(args) > 1:
            return self.usage()

        showPasswords = argSet.pop('show-passwords', False)
        try:
            prettyPrint = sys.stdout.isatty()
        except AttributeError:
            prettyPrint = False
        client.cfg.setDisplayOptions(hidePassword = not showPasswords,
            prettyPrint = prettyPrint)
        client.cfg.display()
register(ConfigCommand)


class RBuilderClient(MintClient):
    cfg = None

    def __init__(self, cfg):
        self.cfg = cfg
        MintClient.__init__(self, self.cfg.serverUrl)


class RBuilderMain(options.MainHandler):
    name = 'rbuilder'
    version = constants.mintVersion

    commandList = _commands
    configClass = RBuilderShellConfig

    abstractCommand = RBuilderCommand

    @classmethod
    def usage(class_, rc = 1):
        print 'rbuilder: command-line interface to an rBuilder Server'
        print ''
        print 'usage:'
        print '  release-create <project name> <trove spec> <image type> - create a new release'
        print '  release-wait <release id>                               - wait for a release to finish building'
        print '  config                                                  - dump configuration'

    def runCommand(self, thisCommand, cfg, argSet, args):
        log.setVerbosity(log.INFO)
        client = RBuilderClient(cfg)
        options.MainHandler.runCommand(self, thisCommand, client, cfg, argSet,
                                       args[1:])

def main():
    RBuilderMain().main()
