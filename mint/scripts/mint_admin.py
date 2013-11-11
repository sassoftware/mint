#
# Copyright (c) SAS Institute Inc.
#

import getpass
import json
import os
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
        if not self.cfg.authPass and os.getuid() != 0:
            sys.exit("error: Can't authenticate. "
                    "This script must be run as root.")
        self.api = robj.connect("https://%s:%s@localhost/api/v1" %
                (self.cfg.authUser, self.cfg.authPass))

    def _prompt(self, argSet, arg, query):
        if arg in argSet:
            return argSet[arg]
        else:
            return raw_input(query)

    def _password(self, argSet):
        if 'password-stdin' in argSet:
            return sys.stdin.readline().rstrip('\r\n')
        elif 'password' in argSet:
            return argSet['password']
        while True:
            password = getpass.getpass("Password: ")
            password2 = getpass.getpass("Password (repeat): ")
            if password == password2:
                return password

    def _collection(self, coll):
        # empty collections can't be iterated over. xml solves all problems,
        # except the ones that it doesn't solve.
        try:
            for x in coll:
                yield x
        except TypeError:
            pass


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
                for x in self._collection(self.api.users)]
            json.dump(ret, sys.stdout)
            print
        else:
            users = list(self.api.users)
            fmt = '%-31s %-7s %s'
            print fmt % ('Username', 'Admin', 'Full Name')
            for x in self._collection(self.api.users):
                print fmt % (x.user_name, x.is_admin.title(), x.full_name)
Script.commandList.append(UserList)


class UserAdd(Command):
    commands = ['user-add']

    def addParameters(self, argDef):
        super(UserAdd, self).addParameters(argDef)
        argDef['User Add Options'] = {
                'user-name': options.ONE_PARAM,
                'full-name': options.ONE_PARAM,
                'email': options.ONE_PARAM,
                'admin': options.ONE_PARAM,
                'password': options.ONE_PARAM,
                'password-stdin': options.NO_PARAM,
                }

    def runCommand(self, cfg, argSet, otherArgs):
        user_name = self._prompt(argSet, 'user-name', "User name: ")
        full_name = self._prompt(argSet, 'full-name', "Full name: ")
        email = self._prompt(argSet, 'email', "Email: ")
        is_admin = self._prompt(argSet, 'admin', "Admin? ").lower()[0] in 'yt'
        password = self._password(argSet)
        user = dict(
                user_name=user_name,
                full_name=full_name,
                email=email,
                is_admin=is_admin,
                password=password,
                )
        user = self.api.users.append(user)
        if 'json' in argSet:
            json.dump({'user_id': int(user.user_id)})
            print
        else:
            print "Created user '%s' with ID '%s'" % (
                    user.user_name, user.user_id)
Script.commandList.append(UserAdd)


class ProjectList(Command):
    commands = ['project-list']

    def runCommand(self, cfg, argSet, otherArgs):
        ret = []
        for project in self._collection(self.api.projects):
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
Script.commandList.append(ProjectList)
