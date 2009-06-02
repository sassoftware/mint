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

        # postgresql on 5439 -> pgpool on 6432
        for poolName, (driver, path) in cfg.database.items():
            if driver != 'postgresql':
                continue

            if '@localhost.localdomain:5439/' in path:
                newDriver = 'pgpool'
                newPath = path.replace('@localhost.localdomain:5439/',
                        '@localhost.localdomain:6432/')
                cfg.database[poolName] = (newDriver, newPath)
                log.info("Changing database alias %s::%s to %s::%s",
                        driver, path, newDriver, newPath)

        path = config.RBUILDER_GENERATED_CONFIG
        cfg.writeGeneratedConfig(path)
        log.info("Migrated configuration written to %s", path)
        return 0
