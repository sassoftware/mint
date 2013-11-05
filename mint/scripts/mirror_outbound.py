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

from conary.conaryclient import mirror
from conary import conaryclient, conarycfg
from conary import versions
from conary.repository import errors

from mint.client import MintClient
from mint.scripts.mirror import MirrorScript

log = logging.getLogger(__name__)


class Script(MirrorScript):
    logFileName = "mirror-outbound.log"

    def action(self):
        self.resetLogging()
        client = MintClient(self.mintUrl)

        outboundMirrors = client.getOutboundMirrors()
        proxyMap = self.cfg.getProxyMap()

        for (outboundMirrorId, sourceProjectId, targetLabels, allLabels,
          recurse, matchStrings, _, fullSync, useReleases,
          ) in outboundMirrors:
            cfg = mirror.MirrorFileConfiguration()

            sourceProject = client.getProject(int(sourceProjectId))
            log.info("Mirroring %s", sourceProject.name)

            try:
                cfg.host = reposHost = sourceProject.fqdn
                sourceUrl = 'https://localhost/repos/%s/' % (
                        sourceProject.shortname,)

                # Note that the mirror role must be named differently so that
                # conary does not delete it when the user is deleted at the
                # end of the mirror process. Otherwise we lose the ACLs we
                # already ate the cost of adding.
                mirrorUser = 'mirror'
                mirrorRole = 'mirror-role'

                # Configure source
                sourceCfg = cfg.setSection("source")
                sourceCfg.repositoryMap.update({reposHost: sourceUrl})
                sourceCfg.user.addServerGlob('*',
                        self.cfg.authUser, self.cfg.authPass)
                cfg.setSection('') # Switch back to the main config

                # Get a repository client for the mirror function
                sourceCCfg = conarycfg.ConaryConfiguration()
                sourceCCfg.configLine('includeConfigFile https://localhost/conaryrc')
                sourceCCfg.repositoryMap.update(sourceCfg.repositoryMap)
                sourceCCfg.user = sourceCfg.user

                # privRepos is a privileged netclient for managing the
                # mirror user and its permissions
                privRepos = sourceRepos = \
                    conaryclient.ConaryClient(sourceCCfg).getRepos()

                # Using label+group based mirroring
                if allLabels:
                    cfg.labels = []
                else:
                    cfg.labels = [versions.Label(labelStr) for labelStr in targetLabels.split(" ")]
                cfg.configLine('matchTroves ' + ' '.join(matchStrings))
                cfg.configLine('recurseGroups %s' % bool(recurse))

                # Configure targets
                obmt = client.getOutboundMirrorTargets(outboundMirrorId)
                if not obmt:
                    log.warning("Skipping %s, no Update Services specified",
                            sourceProject.name)
                    continue

                targetOrdinal = 0
                targetReposes = []
                for _, hostname, targetUser, targetPass, _ in obmt:
                    targetUrl = 'https://%s/conary/' % hostname
                    if not targetPass:
                        log.error("Skipping target %s because no password is configured.")
                        log.error("HINT: Are you trying to mirror to a proxy-mode Update Service?")
                        continue

                    if cfg.hasSection("target"):
                        targetOrdinal += 1
                        targetCfg = cfg.setSection("target%d" % targetOrdinal)
                    else:
                        targetCfg = cfg.setSection("target")
                    targetCfg.resetToDefault('repositoryMap')
                    targetCfg.configLine('repositoryMap * %s' % targetUrl)
                    targetCfg.user.addServerGlob('*', targetUser, targetPass)

                    targetCCfg = conarycfg.ConaryConfiguration()
                    targetCCfg.repositoryMap.update(targetCfg.repositoryMap)
                    targetCCfg.user = targetCfg.user
                    targetCCfg.proxyMap = proxyMap
                    t = conaryclient.ConaryClient(targetCCfg).getRepos()
                    targetReposes.append(t)

                # Do the mirror
                if targetReposes:
                    try:
                        self._doMirror(cfg, sourceRepos, targetReposes, fullSync)
                    finally:
                        if fullSync:
                            client.setOutboundMirrorSync(outboundMirrorId, False)

            except KeyboardInterrupt:
                log.info("Outbound mirror killed by user")
                break
            except errors.InsufficientPermission, ie:
                log.error("%s. Check to make sure that you have been given access to mirror from the aforementioned repository.", ie)
            except:
                log.exception("Unhandled exception while mirroring %s",
                        sourceProject.name)
        return 0

    def cleanup(self):
        log.info("Outbound mirror script finished")

if __name__ == "__main__":
    mo = Script()
    sys.exit(mo.run())
