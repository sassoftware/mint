#!/usr/bin/python
import logging
import os
import pwd
import sys
import tarfile
from mint.db import database
from mint.lib import scriptlibrary
from mint.rest.db import database as restdb
from mint.rest.errors import ProductNotFound
from mint.scripts import createplatforms
from mint.scripts import repository_sync

log = logging.getLogger(__name__)


class Script(scriptlibrary.GenericScript):
    logFileName = 'scripts.log'
    newLogger = True

    def action(self):
        self.loadConfig()
        self.resetLogging(verbose=True)
        args = sys.argv[1:]
        if len(args) == 1:
            dump = args[0]
            fqdn = None
        elif len(args) == 2:
            fqdn, dump = args
        else:
            sys.exit("usage: %s <dump file>" % sys.argv[0])

        # Extract actual FQDN from the metadata in the preload
        tar = tarfile.open(dump)
        tarm = tar.next()
        if tarm.name not in ('metadata', './metadata'):
            sys.exit("Invalid preload tarball: "
                    "first member must be named 'metadata'")
        metadata = {}
        for line in tar.extractfile(tarm):
            key, value = line.rstrip().split(None, 1)
            metadata[key] = value
        tar.close()

        # If the user provided a FQDN, make sure it matches
        fqdn2 = metadata['serverName']
        if fqdn and fqdn != fqdn2:
            sys.exit("Preload FQDN %s does not match requested FQDN %s" %
                    (fqdn2, fqdn))
        elif not fqdn:
            fqdn = fqdn2

        # Drop privileges to make sure created files are owned by apache
        if os.getuid() == 0:
            pwnam = pwd.getpwnam('apache')
            os.setgid(pwnam.pw_gid)
            os.setuid(pwnam.pw_uid)
            log.info("Dropped privileges to uid %d", pwnam.pw_uid)

        # Get a repository handle to restore to
        db = database.Database(self.cfg)
        self.restDb = restdb.Database(self.cfg, db)
        try:
            handle = self.restDb.reposShim.getRepositoryFromFQDN(fqdn)
        except ProductNotFound:
            # Look for a platform with that FQDN and enable it
            handle = self._enablePlatform(fqdn)
            if not handle:
                handle = self._createProject(metadata)
            if not handle:
                sys.exit("No project or platform with FQDN %s was found" %
                        (fqdn,))
        if not handle.hasDatabase:
            sys.exit("Target project does not have a database! The target "
                    "must be local project or mirror-mode external project")
        self.restDb.commit()

        # Do the restore, create helper roles, and nuke caches
        handle.restoreBundle(dump, replaceExisting=True)

        self.restDb.productMgr.reposMgr.populateUsers(handle)
        self.restDb.platformMgr.platformCache.clear()

        # Load platform sources from the platdef which is now available.
        cplatscript = createplatforms.Script()
        cplatscript.restdb = self.restDb
        cplatscript.createPlatforms(fqdn)

        # Create branches and stages
        sync = repository_sync.SyncTool(self.cfg, db)
        sync.syncReposByFQDN(fqdn)

        self.restDb.close()

    def _enablePlatform(self, fqdn):
        platforms = {}
        for platform in self.restDb.platformMgr.platforms.iterPlatforms(
                withRepositoryLookups=False):
            if platform.repositoryHostname != fqdn:
                continue
            platforms[platform.label] = platform
        if not platforms:
            return None
        # Prefer higher-sorting platforms
        platform = sorted(platforms.items())[-1][1]
        platform.enabled = True
        platform.mode = 'manual'
        # This will create an empty repository DB for the platform
        log.info("Enabling platform %s (%s)", platform.platformName,
                platform.platformId)
        self.restDb.platformMgr.updatePlatform(platform.platformId, platform)
        return self.restDb.reposShim.getRepositoryFromFQDN(fqdn)

    def _createProject(self, metadata):
        fqdn = metadata['serverName']
        host, domain = fqdn.split('.', 1)
        shortName = metadata.get('shortName')
        longName = metadata.get('longName', shortName)
        if not shortName:
            return None
        # Projects with attached platforms in 'manual' mode will not be
        # mirrored. Projects with no platforms don't have any such mechanism to
        # suppress mirroring, so create them as a local project instead.
        log.info("Creating project %s (%s)", longName, shortName)
        projectId = self.restDb.productMgr.createProduct(
                name=longName,
                description=longName,
                hostname=host,
                domainname=domain,
                namespace=None,
                projecturl='',
                shortname=shortName,
                prodtype='Appliance',
                version=None,
                commitEmail=None,
                isPrivate=False,
                )
        return self.restDb.reposShim.getRepositoryFromProjectId(projectId)


if __name__ == '__main__':
    sys.exit(Script().run())
