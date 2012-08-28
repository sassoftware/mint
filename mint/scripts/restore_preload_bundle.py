#!/usr/bin/python
import logging
import os
import pwd
import sys
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
        if len(sys.argv) < 3:
            sys.exit("usage: %s <fqdn> <dump file>" % sys.argv[0])
        fqdn, dump = sys.argv[1:]

        if os.getuid() == 0:
            pwnam = pwd.getpwnam('apache')
            os.setgid(pwnam.pw_gid)
            os.setuid(pwnam.pw_uid)
            log.info("Dropped privileges to uid %d", pwnam.pw_uid)

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

        handle.restoreBundle(dump, replaceExisting=True)

        restDb.productMgr.reposMgr.populateUsers(handle)
        restDb.platformMgr.platformCache.clear()

        restDb.close()


sys.exit(Script().run())
