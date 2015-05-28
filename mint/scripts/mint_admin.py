#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import getpass
import json
import os
import robj
import sys
from conary import conarycfg
from conary import conaryclient
from conary.command import HelpCommand
from conary.lib import mainhandler
from conary.lib import options
from conary.lib.command import AbstractCommand
from conary.lib.util import AtomicFile
from conary.repository import errors
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
        api = robj.connect("https://%s:%s@localhost/api" %
                (self.cfg.authUser, self.cfg.authPass))
        for v in self._collection(api.api_versions):
            if v.name == 'v1':
                self.api = v
                break

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

    @staticmethod
    def _collection(coll):
        # empty collections can't be iterated over. xml solves all problems,
        # except the ones that it doesn't solve.
        try:
            for x in coll:
                yield x
        except TypeError:
            pass

    def getConaryClient(self):
        cfg = conarycfg.ConaryConfiguration(False)
        cfg.configLine('includeConfigFile https://localhost/conaryrc')
        cfg.configLine('user * %s %s' % (self.cfg.authUser, self.cfg.authPass))
        return conaryclient.ConaryClient(cfg)


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
            json.dump({'user_id': int(user.user_id)}, sys.stdout)
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
                'name',
                'short_name',
                'repository_hostname',
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


class ProjectAdd(Command):
    commands = ['project-add']

    def addParameters(self, argDef):
        super(ProjectAdd, self).addParameters(argDef)
        argDef['Project Add Options'] = {
                'short-name': options.ONE_PARAM,
                'name': options.ONE_PARAM,
                'repository-hostname': options.ONE_PARAM,
                'description': options.ONE_PARAM,
                'hidden': options.NO_PARAM,
                'external': options.NO_PARAM,
                'upstream-url': options.ONE_PARAM,
                }

    def runCommand(self, cfg, argSet, otherArgs):
        project = dict(
            short_name=self._prompt(argSet, 'short-name', "Short name: "),
            name=self._prompt(argSet, 'name', "Display name: "),
            description=self._prompt(argSet, 'description', "Description: "),
            repository_hostname=self._prompt(argSet, 'repository-hostname', "Repository hostname: "),
            upstream_url=self._prompt(argSet, 'upstream-url', "Upstream URL: "),
            hidden='hidden' in argSet,
            external='external' in argSet,
            )
        project = self.api.projects.append(project)
        if 'json' in argSet:
            json.dump({'project_id': int(project.project_id)}, sys.stdout)
            print
        else:
            print "Created project '%s' with ID %s" % (project.short_name,
                    project.project_id)
Script.commandList.append(ProjectAdd)


class PlatformList(Command):
    commands = ['platform-list']

    def runCommand(self, cfg, argSet, otherArgs):
        ret = []
        for platform in self._collection(self.api.platforms):
            item = dict(
                    platform_name=platform.platformName,
                    label=platform.label,
                    abstract=platform.abstract.lower() == 'true',
                    enabled=platform.enabled.lower() == 'true',
                    )
            if hasattr(platform, 'upstream_url'):
                item['upstream_url'] = platform.upstream_url
            ret.append(item)
        json.dump(ret, sys.stdout)
        print
Script.commandList.append(PlatformList)


class PlatformAdd(Command):
    commands = ['platform-add']

    def addParameters(self, argDef):
        super(PlatformAdd, self).addParameters(argDef)
        argDef['Platform Add Options'] = {
                'label': options.ONE_PARAM,
                'platform-name': options.ONE_PARAM,
                'upstream-url': options.ONE_PARAM,
                'abstract': options.NO_PARAM,
                'enabled': options.NO_PARAM,
                }

    def runCommand(self, cfg, argSet, otherArgs):
        data = dict(
            label=self._prompt(argSet, 'label', "Platform label: "),
            platformName=self._prompt(argSet, 'platform-name', "Display name: "),
            upstream_url=self._prompt(argSet, 'upstream-url', "Upstream URL: "),
            abstract='abstract' in argSet,
            enabled='enabled' in argSet,
            isPlatform=True,
            )
        for platform in self._collection(self.api.platforms):
            if platform.label == data['label']:
                for key, value in data.items():
                    setattr(platform, key, value)
                platform.persist()
                break
        else:
            platform = self.api.platforms.append(data)
            # Enabling a platform doesn't currently work on the initial POST,
            # you have to PUT it again
            platform.persist(force=True)
        if 'json' in argSet:
            json.dump({'platform_id': int(platform.platformId)}, sys.stdout)
            print
        else:
            print "Created platform '%s' with ID %s" % (platform.label,
                    platform.platformId)
Script.commandList.append(PlatformAdd)


class _RmakeUser(Command):
    user = 'rmake'
    role = 'rb_internal_admin'
    cfgpath = '/etc/rmake/server.d/25_rbuilder-rapa.conf'

    def setup(self):
        for project in self._collection(self.api.projects):
            if project.short_name == 'rmake-repository':
                break
        else:
            sys.exit("error: rmake-repository project is missing")
        repos = self.getConaryClient().repos
        fqdn = str(project.repository_hostname)
        return repos, fqdn


class RmakeUserCheck(_RmakeUser):
    commands = ['rmakeuser-check']

    def runCommand(self, cfg, argSet, otherArgs):
        repos, fqdn = self.setup()
        ok = True
        if self.user not in repos.getRoleMembers(fqdn, self.role):
            ok = False
        if os.path.exists(self.cfgpath):
            with open(self.cfgpath) as f:
                if 'reposUser' not in f.read():
                    ok = False
        else:
            ok = False
        # ruby json can't parse bare ints/bools, have to wrap it in a container
        json.dump([ok], sys.stdout)
        print
        return 0
Script.commandList.append(RmakeUserCheck)


class RmakeUserCreate(_RmakeUser):
    commands = ['rmakeuser-create']

    def runCommand(self, cfg, argSet, otherArgs):
        repos, fqdn = self.setup()
        password = os.urandom(16).encode('hex')
        try:
            repos.addUser(fqdn, self.user, password)
        except errors.UserAlreadyExists:
            repos.changePassword(fqdn, self.user, password)
        if self.user not in repos.getRoleMembers(fqdn, self.role):
            repos.addRoleMember(fqdn, self.role, self.user)
        with AtomicFile(self.cfgpath, chmod=0644) as f:
            print >> f, "# Do not edit this file; it will be overwritten."
            print >> f, "reposName", fqdn
            print >> f, "reposUser", fqdn, self.user, password
            print >> f, "reposUrl https://localhost/repos/%s/" % fqdn
        print '[]'
Script.commandList.append(RmakeUserCreate)

if __name__ == '__main__':
    sys.exit(Script().run())
