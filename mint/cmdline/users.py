#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
import time
import os
import sys

from mint import producttypes
from mint import jobstatus
from mint.cmdline import commands

from conary import versions
from conary.lib import options, log
from conary.conaryclient.cmdline import parseTroveSpec


class UserCreateCommand(commands.RBuilderCommand):
    commands = ['user-create']
    paramHelp = "<username> <email> [--password <password>]"

    docs = {'password' : 'specify a password instead of prompting'}

    def addParameters(self, argDef):
        commands.RBuilderCommand.addParameters(self, argDef)
        argDef["password"] = options.ONE_PARAM

    def runCommand(self, client, cfg, argSet, args):
        args = args[1:]
        if len(args) < 2:
            return self.usage()

        pw1 = argSet.pop('password', None)

        if not pw1 and sys.stdin.isatty():
            from getpass import getpass

            pw1 = getpass('New Password:')
            pw2 = getpass('Reenter password:')

            if pw1 != pw2:
                print "Passwords do not match."
                sys.exit(1)
        elif not pw1:
            # chop off the trailing newline
            pw1 = sys.stdin.readline()[:-1]

        username, email = args
        userId = client.registerNewUser(username, pw1, "",
            email, "", "", active=True)

        log.info("User %s created (id %d)" % (username, userId))
        return userId
commands.register(UserCreateCommand)
