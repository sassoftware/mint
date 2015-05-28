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


import logging
import os
import sys
import time

# Automagically insert the mint tree into sys.path for easier debugging.
root = os.path.sep.join(__file__.split(os.path.sep)[:-__name__.count('.')-2])
if root not in sys.path:
    sys.path.insert(0, root)
del root

from conary import versions
from conary.lib import options
from conary.lib import coveragehook

from mint import config
from mint.db import database
from mint.lib import mintutils
from mint.mint_error import ItemNotFound
from mint.logerror import logErrorAndEmail
from mint.scripts import repository_sync

log = logging.getLogger(__name__)


def process(repos, cfg, commitList, srcMap, pkgMap, grpMap, argv, otherArgs):
    coveragehook.install()
    if not len(argv) and not len(otherArgs):
        return 1

    mintutils.setupLogging(consoleLevel=logging.WARNING,
            consoleFormat='apache')
    
    argDef = {
        'config' : options.ONE_PARAM,
        'user': options.ONE_PARAM,
        'hostname': options.ONE_PARAM,
    }

    # create an argv[0] for processArgs to ignore
    argv[0:0] = ['']
    argSet, someArgs = options.processArgs(argDef, {}, cfg, '', argv=argv)
    # and now remove argv[0] again
    argv.pop(0)
    if len(someArgs):
        someArgs.pop(0)
    otherArgs.extend(someArgs)

    # Double-fork so the commit hook doesn't block the caller.
    if os.fork():
        return 0

    try:
        if not os.fork():
            try:
                registerCommits(argSet, commitList)
            except:
                e_type, e_value, e_tb = sys.exc_info()
                logErrorAndEmail(None, e_type, e_value, e_tb, 'commit hook',
                        argSet)
    finally:
        os._exit(0)


def registerCommits(argSet, commitList):
    user = argSet['user']

    overrideHostname = None
    if 'hostname' in argSet:
        overrideHostname = argSet['hostname']

    cfgPath = argSet.get('config', config.RBUILDER_CONFIG)
    cfg = config.MintConfig()
    cfg.read(cfgPath)

    db = database.Database(cfg)
    db.db.transaction()

    try:
        userId = db.users.getIdByColumn("username", user)
    except ItemNotFound:
        userId = None

    now = time.time()
    projectIdCache = {}
    groups = set()
    trovesSeen = set()
    proddefHosts = set()
    for name, version, _ in commitList:
        version = versions.VersionFromString(version)

        # Map FQDN to projectId. If the FQDN isn't found, drop the commit.
        if overrideHostname:
            hostname = overrideHostname
        else:
            hostname = version.getHost()
        if name == 'product-definition:source':
            proddefHosts.add(hostname)
        if name.startswith('group-') and not name.endswith(':source'):
            groups.add((name, version))

        if hostname in projectIdCache:
            projectId = projectIdCache[hostname]
        else:
            try:
                projectId = db.projects.getProjectIdByFQDN(hostname)
            except ItemNotFound:
                projectId = None
                log.warning("Could not record commit for project %r", hostname)
            projectIdCache[hostname] = projectId

        if projectId is None:
            continue

        # Skip already-added name-version pairs -- they differ only by flavor,
        # which the commits table doesn't keep a slot for.
        if (name, version) not in trovesSeen:
            db.commits.new(projectId, now, name, version.asString(), userId)
            trovesSeen.add((name, version))
    db.db.commit()

    if proddefHosts and db.db.driver != 'sqlite':
        tool = repository_sync.SyncTool(cfg, db)
        for hostname in proddefHosts:
            tool.syncReposByFQDN(hostname)
