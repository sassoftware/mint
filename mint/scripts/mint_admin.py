#
# Copyright (c) SAS Institute Inc.
#

import json
import robj
import sys
from conary.command import HelpCommand
from conary.lib import mainhandler
from conary.lib import options
from conary.lib.command import AbstractCommand
from mint import config


class Command(AbstractCommand):

    def addParameters(self, argDef):
        argDef[self.defaultGroup] = {
                'json': options.NO_PARAM,
                }

    def processConfigOptions(self, cfg, *args, **kwargs):
        AbstractCommand.processConfigOptions(self, cfg, *args, **kwargs)
        self.cfg = cfg
        self.api = robj.connect("https://%s:%s@localhost/api/v1" %
                (self.cfg.authUser, self.cfg.authPass))


class Script(mainhandler.MainHandler):
    commandList = [ HelpCommand ]
    abstractCommand = Command
    name = 'mint-admin'

    def configClass(self, readConfigFiles=True, ignoreErrors=None):
        cfg = config.MintConfig()
        if readConfigFiles:
            cfg.read(config.RBUILDER_CONFIG)
        return cfg

    def run(self):
        return self.main()


@Script.commandList.append
class UserList(Command):
    commands = ['user-list']

    def runCommand(self, cfg, argSet, otherArgs):
        if 'json' in argSet:
            ret = [dict(
                user_id=int(x.user_id),
                user_name=x.user_name,
                full_name=x.full_name,
                email=x.email,
                is_admin=True if x.is_admin.lower() == 'true' else False,
                )
                for x in self.api.users]
            json.dump(ret, sys.stdout)
            print
        else:
            users = list(self.api.users)
            fmt = '%-31s %-7s %s'
            print fmt % ('Username', 'Admin', 'Full Name')
            for x in self.api.users:
                print fmt % (x.user_name, x.is_admin.title(), x.full_name)


@Script.commandList.append
class ProjectList(Command):
    commands = ['project-list']

    def runCommand(self, cfg, argSet, otherArgs):
        ret = []
        for project in self.api.projects:
            item = dict((x, getattr(project, x, None)) for x in [
                'repository_hostname',
                'name',
                'description',
                'upstream_url',
                ])
            for x in ['external', 'hidden']:
                if getattr(project, x, '').lower() == 'true':
                    item[x] = True
                else:
                    item[x] = False
            ret.append(item)
        json.dump(ret, sys.stdout)
        print
