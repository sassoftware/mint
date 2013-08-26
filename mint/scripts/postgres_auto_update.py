#
# Copyright (c) rPath, Inc.
#

"""
Shut down PostgreSQL, check if it needs updating, then start it again.
"""

import logging
import optparse
import os
import signal
import subprocess
import tempfile
import time
import traceback
from conary.lib import cfg as cfgmod
from conary.lib import cfgtypes
from conary.lib import util as cny_util

from mint import config
from mint.scripts import postgres_major_migrate

log = logging.getLogger('auto_update')


class PostgresMeta(cfgmod.ConfigFile):
    version = cfgtypes.CfgString
    binDir = cfgtypes.CfgPath
    dataDir = cfgtypes.CfgPath


class Script(postgres_major_migrate.Script):
    logFileName = 'scripts.log'
    newLogger = True

    port = 5439
    user = 'postgres'
    dataTop = '/srv/pgsql'
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

        currentMeta = self.getCurrentMeta()
        nextMeta = self.getNextMeta()
        if currentMeta and currentMeta.dataDir == nextMeta.dataDir:
            return 0

        self.stopPostgres()
        if not currentMeta:
            self.initdb(nextMeta)
        else:
            self.migrateMeta(currentMeta, nextMeta)
        self.startPostgres()

    def stopPostgres(self):
        """Kill postgres by checking its UNIX socket."""
        log.info("Stopping PostgreSQL on port %s", self.port)
        sockPath = '/tmp/.s.PGSQL.%s' % self.port
        # Send progressively more aggressive sigals until it dies.
        signals =   ([signal.SIGINT] * 4
                ) + ([signal.SIGQUIT] * 2
                ) +  [signal.SIGKILL]
        while signals:
            if not os.path.exists(sockPath):
                return

            signum = signals.pop(0)
            if not self._stopPostgres(sockPath, signum):
                # No process is listening on that socket.
                return

            sleepUntil = time.time() + 15
            while time.time() < sleepUntil:
                if not os.path.exists(sockPath):
                    return
                time.sleep(0.1)

    @staticmethod
    def _stopPostgres(sockPath, signal):
        # Use netstat to figure out what processes own the socket.
        netstat = subprocess.Popen(['netstat', '-lpnxT'],
                shell=False, stdout=subprocess.PIPE).communicate()[0]
        found = False
        for line in netstat.splitlines():
            words = line.split()
            if sockPath not in words:
                continue
            i = words.index(sockPath)
            process = words[i-1]
            pid, name = process.split('/')
            if name not in ('postmaster', 'postgres'):
                continue
            os.kill(int(pid), signal)
            found = True
        return found

    def getCurrentMeta(self):
        """Get metadata about the current PostgreSQL cluster."""
        cfg = PostgresMeta()
        if os.path.exists(self.currentMetaPath):
            cfg.read(self.currentMetaPath)
            return cfg

        # rBuilder <= 5.8.0 doesn't have a meta file. Use the highest-numbered
        # datadir as the "current" cluster.
        if not os.path.isdir(self.dataTop):
            return None
        versions = []
        for name in os.listdir(self.dataTop):
            if name[-9:] != '-rbuilder':
                continue
            path = os.path.join(self.dataTop, name)
            version = name[:-9]
            try:
                parts = [int(x) for x in version.split('.')]
            except ValueError:
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
        log.info("Initializing PostgreSQL %s cluster", meta.version)
        assert not os.path.exists(meta.dataDir)
        self.loadPrivs(user=self.user)
        parentDir = os.path.dirname(meta.dataDir)
        if not os.path.isdir(parentDir):
            os.makedirs(parentDir)
        tempDir = tempfile.mkdtemp(dir=parentDir)
        try:
            os.chown(tempDir, self.uidgid[0], self.uidgid[1])
            self.dropPrivs()

            cluster = postgres_major_migrate.Postmaster(dataDir=tempDir,
                    binDir=meta.binDir, port=65000,
                    logPath='/tmp/postgres-initdb.log')
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
        log.info("Migrating PostgreSQL from %s to %s", currentMeta.version,
                nextMeta.version)
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
