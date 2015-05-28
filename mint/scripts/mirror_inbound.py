#!/usr/bin/python
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
import sys

from conary import conaryclient
from conary import conarycfg
from conary import versions
from conary.conaryclient import mirror
from conary.repository import errors

from mint import projects
from mint import server
from mint.db import repository
from mint.scripts.mirror import MirrorScript

log = logging.getLogger(__name__)


class Script(MirrorScript):
    logFileName = "mirror-inbound.log"
    options = None

    def action(self):
        self.server = server.MintServer(self.cfg, allowPrivate=True)
        self.server._setAuth((self.cfg.authUser, self.cfg.authPass))
        self.mgr = self.server.reposMgr

        for label in self.server.getInboundMirrors():
            inboundMirrorId, targetProjectId, sourceLabels, sourceUrl, \
                    sourceAuthType, sourceUser, sourcePass, \
                    sourceEntitlement, mirrorOrder, allLabels = label
            targetProject = projects.Project(self.server, targetProjectId)
            reposHost = targetProject.fqdn
            targetUrl = self.server.labels.getLabelsForProject(
                    targetProjectId)[1][reposHost]
            log.info("Mirroring %s", targetProject.name)

            try:
                cfg = mirror.MirrorConfiguration()
                cfg.host = reposHost
                if allLabels:
                    cfg.labels = []
                else:
                    cfg.labels = [versions.Label(x) for x in sourceLabels.split()]

                # Source repository is a ShimNetClient preprogrammed to look
                # upstream for this FQDN.
                userInfo = entitlement = None
                if sourceAuthType == 'userpass':
                    userInfo = (sourceUser, sourcePass)
                elif sourceAuthType == 'entitlement':
                    entitlement = sourceEntitlement
                sourceRepos = self.mgr.getRepos(userId=repository.ANY_READER)
                sourceRepos.c.cache[reposHost] = self.mgr.getServerProxy(
                        reposHost, url=sourceUrl, user=userInfo, entitlement=entitlement)

                # Target repository is a regular dumb client using internal
                # creds.
                targetCfg = conarycfg.ConaryConfiguration(False)
                targetCfg.includeConfigFile('https://localhost/conaryrc')
                targetCfg.repositoryMap[reposHost] = targetUrl
                targetCfg.user.addServerGlob(reposHost,
                        self.cfg.authUser, self.cfg.authPass)
                targetRepos = conaryclient.ConaryClient(targetCfg).repos

                self._doMirror(cfg, sourceRepos, targetRepos)

                # Disable background mirroring now that mirror is done
                if self.server.getBackgroundMirror(targetProjectId):
                    log.info("Switching project from background mirror mode to "
                            "full mirror mode")
                    self.server.setBackgroundMirror(targetProjectId, False)

            except KeyboardInterrupt:
                log.info("Inbound mirror terminated by user")
                break
            except errors.InsufficientPermission, ie:
                log.error("%s. Check to make sure that you have been given access to mirror from the aforementioned repository.", ie)
            except:
                log.exception("Unhandled exception while mirroring %s",
                        targetProject.name)

        return 0

    def cleanup(self):
        log.info("Inbound mirror script finished")

if __name__ == "__main__":
    mi = Script()
    sys.exit(mi.run())
