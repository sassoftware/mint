#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

"""
Shut down PostgreSQL, check if it needs updating, then start it again.
"""

import logging
import optparse
import os
import subprocess
import tempfile
import time
import traceback
from conary.lib import cfg as cfgmod
from conary.lib import cfgtypes
from conary.lib import util as cny_util

from mint import config
from mint.scripts import postgres_major_migrate

log = logging.getLogger(__name__)


class PostgresMeta(cfgmod.ConfigFile):
    version = cfgtypes.CfgString
    binDir = cfgtypes.CfgPath
    dataDir = cfgtypes.CfgPath


class Script(postgres_major_migrate.Script):
    logFileName = 'scripts.log'
    newLogger = True

    port = 5439
    user = 'postgres'
    currentMetaPath = '/srv/rbuilder/data/postgres-meta'
    nextMetaPath = '/usr/share/rbuilder/postgres-meta'

    def action(self):
        parser = optparse.OptionParser()
        parser.add_option('-c', '--config-file',
                default=config.RBUILDER_CONFIG)
        parser.add_option('-q', '--quiet', action='store_true')
        parser.add_option('--init', action='store_true')
        options, args = parser.parse_args()

        self.loadConfig(options.config_file)
        self.resetLogging(quiet=options.quiet)

        self.stopPostgres()

        nextMeta = self.getNextMeta()
        if options.init:
            self.initdb(nextMeta)
        else:
            currentMeta = self.getCurrentMeta()
            if currentMeta.dataDir != nextMeta.dataDir:
                self.migrateMeta(currentMeta, nextMeta)

        self.startPostgres()

    def stopPostgres(self):
        """Kill postgres by checking its UNIX socket."""
        sockPath = '/tmp/.s.PGSQL.%s' % self.port
        # Send progressively more aggressive sigals until it dies.
        signals = (['-TERM'] * 3) + (['-QUIT'] * 3) + ['-KILL']
        while signals:
            if not os.path.exists(sockPath):
                return

            signame = signals.pop(0)
            proc = subprocess.Popen(['fuser', '-sk', signame, sockPath],
                    shell=False, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
            stdout, _ = proc.communicate()
            if proc.returncode:
                # fuser failed, postgres must not be running?
                return

            time.sleep(1)

    def getCurrentMeta(self):
        """Get metadata about the current PostgreSQL cluster."""
        cfg = PostgresMeta()
        if os.path.exists(self.currentMetaPath):
            cfg.read(self.currentMetaPath)
            return cfg

        # rBuilder <= 5.8.0 doesn't have a meta file. Use the highest-numbered
        # datadir as the "current" cluster.
        versions = []
        for name in os.listdir('/srv/pgsql'):
            if name[-9:] != '-rbuilder':
                continue
            path = os.path.join('/srv/pgsql', name)
            version = name[:-9]
            try:
                parts = [int(x) for x in version.split('.')]
            except ValueError:
                continue
            # Sanity check: make sure there's more than the 3 default databases
            # (template0, template1, postgres)
            basedir = os.path.join(path, 'base')
            if not os.path.isdir(basedir) or len(os.listdir(basedir)) <= 3:
                log.warning("Ignoring (empty?) cluster at %s", path)
                continue
            versions.append((parts, version, path))
        if not versions:
            # No postgres data dir found.
            return None

        versions.sort()
        _, cfg.version, cfg.dataDir = versions[-1]
        cfg.binDir = '/opt/postgresql-%s/bin' % (cfg.version,)
        cfg.writeToFile(self.currentMetaPath, includeDocs=False)
        return cfg

    def getNextMeta(self):
        """Get metadata about the version of PostgreSQL that will be used after
        the (possible) upgrade.
        """
        cfg = PostgresMeta()
        cfg.read(self.nextMetaPath)
        return cfg

    def updateMeta(self, nextMeta):
        """Update the "current" metadata file."""
        nextMeta.writeToFile(self.currentMetaPath, includeDocs=False)

    def initdb(self, meta):
        """Create a new postgres cluster at the given location."""
        assert not os.path.exists(meta.dataDir)
        self.loadPrivs(user=self.user)
        tempDir = tempfile.mkdtemp(dir=os.path.dirname(meta.dataDir))
        try:
            os.chown(tempDir, self.uidgid[0], self.uidgid[1])
            self.dropPrivs()

            cluster = postgres_major_migrate.Postmaster(dataDir=tempDir,
                    binDir=meta.binDir, port=65000)
            cluster.initdb()

            self.restorePrivs()
            self.updateMeta(meta)
            os.rename(tempDir, meta.dataDir)
        finally:
            try:
                if os.path.isdir(tempDir):
                    try:
                        self.restorePrivs()
                    except:
                        traceback.print_exc()
                    log.info("Cleaning up temporary target dir")
                    cny_util.rmtree(tempDir)
            except:
                traceback.print_exc()

    def migrateMeta(self, currentMeta, nextMeta):
        """Migrate postgres cluster to a new version and datadir."""
        assert currentMeta.dataDir != nextMeta.dataDir
        if os.path.exists(nextMeta.dataDir):
            # Nuke any existing data directory -- either an explicit meta file
            # told us that a different datadir is in use, or the heuristic
            # decided there was nothing of value in this one.
            cny_util.rmtree(nextMeta.dataDir)

        self.runMigration(
                from_bindir=currentMeta.binDir,
                from_datadir=currentMeta.dataDir,
                from_port=None,
                to_bindir=nextMeta.binDir,
                to_datadir=nextMeta.dataDir,
                user=self.user,
                )
        self.updateMeta(nextMeta)
        os.rename(currentMeta.dataDir, currentMeta.dataDir + '.old')

    def startPostgres(self):
        os.system("/sbin/service postgresql-rbuilder start")
        cluster = postgres_major_migrate.DummyCluster(self.port, user=self.user)
        cluster.waitForPostgres()
