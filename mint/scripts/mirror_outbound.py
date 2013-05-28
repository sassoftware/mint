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
from conary.deps import deps
from conary.repository import errors

from mint import helperfuncs
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

                if useReleases:
                    # Using published release based mirroring
                    releases = client.getMirrorableReleasesByProject(
                        int(sourceProjectId))

                    # Create the mirror user, deleting it if it already
                    # exists
                    try:
                        privRepos.deleteUserByName(reposHost, mirrorUser)
                    except errors.UserNotFound:
                        pass
                    mirrorPassword = helperfuncs.genPassword(64)
                    privRepos.addUser(reposHost, mirrorUser, mirrorPassword)

                    # Create the mirror role if it doesn't exist yet
                    try:
                        privRepos.addRole(reposHost, mirrorRole)
                        privRepos.addAcl(reposHost, mirrorRole, 'ravenous-bugblatter-beast',
                            reposHost + '@dummy:label')
                    except errors.RoleAlreadyExists:
                        pass
                    privRepos.setRoleCanMirror(reposHost, mirrorRole, True)
                    privRepos.updateRoleMembers(reposHost, mirrorRole,
                        [mirrorUser])

                    # Get the list of troves that *should* be mirrored
                    newTroves = set()
                    for pubReleaseId in releases:
                        builds = client.getBuildsForPublishedRelease(
                          pubReleaseId)
                        for buildId in builds:
                            build = client.getBuild(buildId)
                            name = build.troveName
                            # troveVersion has a timestamp;
                            # listTroveAccess will not. "un-freeze"
                            #the version to make sure they match.
                            version = str(versions.ThawVersion(
                                build.troveVersion))
                            flavor = deps.ThawFlavor(build.troveFlavor)
                            newTroves.add((name, version, flavor))

                    # Get the list of troves that *are* marked for mirroring
                    oldTroves = set()
                    for name, version, flavor in privRepos.listTroveAccess(
                      reposHost, mirrorRole):
                        oldTroves.add((name, str(version), flavor))

                    # Add and remove trove access as needed to make
                    # trove access match the mirrorable published
                    # release list.
                    removeAccess = [(n, versions.VersionFromString(v), f)
                        for (n, v, f) in oldTroves - newTroves]
                    if removeAccess:
                        privRepos.deleteTroveAccess(mirrorRole, removeAccess)

                    addAccess = [(n, versions.VersionFromString(v), f)
                        for (n, v, f) in newTroves - oldTroves]
                    if addAccess:
                        privRepos.addTroveAccess(mirrorRole, addAccess)

                    # Now that we've brought trove access up to date,
                    # delete our admin access to this project's
                    # repository and replace it with the mirror user.
                    sourceCfg.user.addServerGlob(reposHost, mirrorUser,
                            mirrorPassword)

                    # And re-open the repository
                    sourceRepos = conaryclient.ConaryClient(sourceCCfg).getRepos()

                    # Configure for recursive mirroring of available groups
                    names = set('+' + x[0] for x in newTroves)
                    cfg.labels = []
                    cfg.configLine('matchTroves ' + ' '.join(names))
                    cfg.configLine('recurseGroups True')

                    # For now, always force a full sync, as older
                    # releases may have been added to the mirrorable
                    # list since the last mirror. Later we might be
                    # able to only force a sync if the oldest
                    # unmirrored group is newer than the oldest
                    # mirror mark, but this would require a new repos
                    # call (to get the trove timestamp).
                    fullSync = True
                else:
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

                if useReleases:
                    # Delete temporary mirror user
                    privRepos.deleteUserByName(reposHost, mirrorUser)

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
