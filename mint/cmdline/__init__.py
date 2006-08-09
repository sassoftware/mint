#!/usr/bin/python
#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import os
import sys

from conary.lib import options, util, log, cfgtypes
from conary.lib.cfg import ConfigFile

from mint import constants
from mint.client import MintClient
from mint.cmdline import builds
from mint.cmdline import users
from mint.cmdline import commands
from mint.mint_error import MintError

class RBuilderShellConfig(ConfigFile):
    serverUrl = None

    def __init__(self, readConfigFiles = True):
        ConfigFile.__init__(self)
	if readConfigFiles:
	    self.readFiles()

    def readFiles(self):
        if os.environ.has_key("HOME"):
            fn = '/'.join((os.environ["HOME"], ".rbuilderrc"))
            self.read(fn, exception=False)

class ConfigCommand(commands.RBuilderCommand):
    commands = ['config']
    docs = {'show-passwords' : 'do not mask passwords'}

    def addParameters(self, argDef):
         commands.RBuilderCommand.addParameters(self, argDef)
         argDef["show-passwords"] = options.NO_PARAM

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
commands.register(ConfigCommand)


class RBuilderClient(MintClient):
    cfg = None

    def __init__(self, cfg):
        self.cfg = cfg
        MintClient.__init__(self, self.cfg.serverUrl)


class RBuilderMain(options.MainHandler):
    name = 'rbuilder'
    version = constants.mintVersion

    commandList = commands._commands
    configClass = RBuilderShellConfig

    abstractCommand = commands.RBuilderCommand

    @classmethod
    def usage(class_, rc = 1):
        print 'rbuilder: command-line interface to an rBuilder Server'
        print ''
        print 'usage:'
        print '  build-create <project name> <trove spec> <image type> - create a new build'
        print '  build-wait <build id>                               - wait for a build to finish building'
        print '  build-url <build id>                                - show all urls related to a build'
        print '  config                                                  - dump configuration'

    def runCommand(self, thisCommand, cfg, argSet, args):
        if not cfg.serverUrl:
            raise cfgtypes.CfgError(
                'Please set the serverUrl configuration option in ~/.rbuilderrc')
        client = RBuilderClient(cfg)
        try:
            options.MainHandler.runCommand(self,
                thisCommand, client, cfg, argSet, args[1:])
        except MintError, e:
            log.error("response from rBuilder server: %s" % str(e))
            sys.exit(0)

def main():
    log.setVerbosity(log.INFO)
    rb = RBuilderMain()
    try:
        return rb.main()
    except cfgtypes.CfgError, e:
        print str(e)
        return 1
