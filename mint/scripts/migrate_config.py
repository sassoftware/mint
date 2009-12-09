#
# Copyright (c) 2008-2009 rPath, Inc.
#

"""
General mint configuration maintenance.

This script is responsible for updating rbuilder-generated.conf when the
options written to that file change.
"""

import logging
import optparse
import os
import sys

from mint import config
from mint.lib import scriptlibrary

log = logging.getLogger(__name__)


class MigrateConfig(scriptlibrary.GenericScript):
    logFileName = 'scripts.log'
    newLogger = True

    def handle_args(self):
        op = optparse.OptionParser()
        op.add_option("--migrate", action="store_true")
        op.add_option("--rbuilder-config", default=config.RBUILDER_CONFIG)
        self.options, self.args = op.parse_args()
        if not self.options.migrate:
            op.error("Nothing to do. Try --migrate.")

        cfg = config.MintConfig()
        cfg.read(self.options.rbuilder_config)
        self.setConfig(cfg)
        return True

    def action(self):
        cfg = self.cfg
        if not cfg.configured:
            log.info("Not migrating rBuilder configuration: not configured.")
            return 0

        # defaultBranch -> namespace
        if cfg.namespace in (None, '', 'yournamespace'):
            branch = cfg.defaultBranch.split(':')[0].strip()
            if branch:
                cfg.namespace = branch
                log.info("Namespace has been set to %r", branch)

        # reposDBDriver/reposDBPath -> database
        poolName = 'default'
        if cfg.reposDBDriver:
            cfg.database[poolName] = pool = (cfg.reposDBDriver, cfg.reposDBPath)
            log.info("Set database alias %r to %r", poolName, pool)

        for poolName, (driver, path) in cfg.database.items():
            if (driver == 'postgresql' and
                    '@localhost.localdomain:5439/' in path):
                # Move postgresql on 5439 to pgpool on 6432
                driver = 'pgpool'
                path = path.replace('@localhost.localdomain:5439/',
                        '@localhost.localdomain:6432/')

            if (driver == 'pgpool' and
                    'rbuilder@localhost.localdomain:' in path):
                path = path.replace('rbuilder@localhost.localdomain:',
                        'postgres@localhost.localdomain:')

            oldDriver, oldPath = cfg.database[poolName]
            if (oldDriver, oldPath) != (driver, path):
                cfg.database[poolName] = (driver, path)
                log.info("Changing database alias %s::%s to %s::%s",
                        oldDriver, oldPath, driver, path)

        path = config.RBUILDER_GENERATED_CONFIG
        cfg.writeGeneratedConfig(path)
        log.info("Migrated configuration written to %s", path)
        return 0
