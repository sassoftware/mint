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
        for line in tar.extractfile(tarm):
            key, value = line.rstrip().split(None, 1)
            if key == 'serverName':
                fqdn2 = value
                break
        else:
            sys.exit("Invalid preload tarball: "
                    "missing metadata field 'serverName'")
        tar.close()

        # If the user provided a FQDN, make sure it matches
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
        restDb = restdb.Database(self.cfg, db)
        try:
            handle = restDb.reposShim.getRepositoryFromFQDN(fqdn)
        except ProductNotFound:
            # Look for a platform with that FQDN and enable it
            platforms = {}
            for platform in restDb.platformMgr.platforms.iterPlatforms(
                    withRepositoryLookups=False):
                if platform.repositoryHostname != fqdn:
                    continue
                platforms[platform.label] = platform
            if not platforms:
                sys.exit("No project or platform with FQDN %s was found" %
                        (fqdn,))
            # Prefer higher-sorting platforms
            platform = sorted(platforms.items())[-1][1]
            platform.enabled = True
            platform.mode = 'manual'
            # This will create an empty repository DB for the platform
            log.info("Enabling platform %s (%s)", platform.platformName,
                    platform.platformId)
            restDb.platformMgr.updatePlatform(platform.platformId, platform)
            handle = restDb.reposShim.getRepositoryFromFQDN(fqdn)

        # Do the restore, create helper roles, and nuke caches
        handle.restoreBundle(dump, replaceExisting=True)

        restDb.productMgr.reposMgr.populateUsers(handle)
        restDb.platformMgr.platformCache.clear()

        restDb.close()


sys.exit(Script().run())
