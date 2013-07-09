#
# Copyright (c) 2011 rPath, Inc.
#

import hashlib
import logging
import sys
from conary.dbstore import sqlerrors
from mint.lib.scriptlibrary import GenericScript
from mint.db import database
from mint.db import repository
from rpath_proddef import api1 as proddef

log = logging.getLogger(__name__)

# Bump this to force all branches to be refreshed.
SYNC_VERSION = 3


class Script(GenericScript):
    logFileName = 'scripts.log'
    newLogger = True

    def action(self):
        self.loadConfig()
        args = sys.argv[1:]
        if '--debug' in args:
            args.remove('--debug')
            self.resetLogging(verbose=True)
        sync = SyncTool(self.cfg)

        if args:
            for fqdn in args:
                sync.syncReposByFQDN(fqdn)
        else:
            sync.syncAll()

class SyncTool(object):
    def __init__(self, cfg, db=None):
        self.cfg = cfg
        if not db:
            db = database.Database(cfg)
        self.db = db
        self.reposManager = repository.RepositoryManager(self.cfg, self.db.db,
                bypass=True)
        self.client = self.reposManager.getClient(userId=repository.ANY_READER)
        self.repos = self.client.getRepos()
        self._platformMap = None

    def syncAll(self):
        for handle in self.reposManager.iterRepositories():
            self._syncReposMaybe(handle)

    def syncReposByFQDN(self, fqdn):
        handle = self.reposManager.getRepositoryFromFQDN(fqdn)
        self._syncReposMaybe(handle)

    def _syncReposMaybe(self, handle):
        self._syncRepos(handle)
        self.reposManager.reset()

    def _syncRepos(self, handle):
        # FIXME: more error handling: missing or inaccessible stuff shouldn't
        # crash the whole script or make excessive noise.

        for x in range(3):
            try:
                # Get current branch/stage structure.
                cu = self.db.cursor()
                cu.execute("""SELECT label, productversionid, cache_key
                    FROM ProductVersions WHERE projectId = ?""", handle.projectId)
                branchMap = dict((x[0], x[1:]) for x in cu)

                # Resolve a list of proddef troves on this repository.
                name = 'product-definition:source'
                result = self.repos.getAllTroveLeaves(handle.fqdn, {name: None})
                if name not in result:
                    return
                for version in result[name]:
                    self._syncBranchMaybe(handle, version, branchMap)
            except sqlerrors.ColumnNotUnique:
                # Often, creating or modifying a branch through the API results
                # in the database being updated directly as well, which
                # conflicts here. Just go through the cycle again to make sure
                # everything is tidy.
                self.db.rollback()
                continue
            else:
                self.db.commit()
                break
        else:
            raise

    def _syncBranchMaybe(self, handle, version, branchMap):
        """Compute a hash of the proddef version, then compare to the existing
        one in the database to decide whether to update this branch."""
        label = str(version.trailingLabel())
        cacheKey = '\0'.join((str(SYNC_VERSION), version.freeze()))
        cacheKey = hashlib.sha1(cacheKey).hexdigest()
        if label in branchMap:
            branchId, oldKey = branchMap[label]
            if oldKey == cacheKey:
                log.debug("Skipping label %s due to matching hash", label)
                return
        self._syncBranch(handle, version, branchMap, cacheKey)

    def _syncBranch(self, handle, version, branchMap, cacheKey):
        """Synchronize the database branch and stages to the ones enumerated in
        the product definition."""
        cu = self.db.cursor()
        label = str(version.trailingLabel())
        pd = proddef.ProductDefinition()
        pd.setBaseLabel(label)
        try:
            pd.loadFromRepository(self.client)
        except proddef.ProductDefinitionFileNotFoundError:
            return
        if pd.getProductDefinitionLabel() != label:
            # baselabel does not match
            log.info("Product definition on label %s has base label %s; not "
                    "synchronizing into database", label,
                    pd.getProductDefinitionLabel())
            return

        platformLabel = pd.getPlatformSourceLabel()
        platformId = self.getPlatformMap().get(platformLabel)
        sourceGroup = pd.getSourceGroup() or pd.getImageGroup()
        fields = {
                'projectId': handle.projectId,
                'namespace': pd.getConaryNamespace(),
                'name': pd.getProductVersion(),
                'description': pd.getProductDescription(),
                'source_group': sourceGroup,
                'platform_id': platformId,
                'platform_label': platformLabel,
                'cache_key': cacheKey,
                }
        items = fields.items()
        if label in branchMap:
            branchId, _ = branchMap[label]
            setters = ', '.join('%s = ?' % x[0] for x in items)
            values = [x[1] for x in items] + [label]
            cu.execute(("UPDATE ProductVersions SET %s WHERE label = ?"
                    % setters), tuple(values))
            log.info("Updated branch information for label %s", label)
        else:
            items.append(('label', label))
            names = ', '.join(x[0] for x in items)
            placeholders = ', '.join('?' for x in items)
            values = [x[1] for x in items]
            cu.execute("INSERT INTO ProductVersions (%s) VALUES (%s)"
                    % (names, placeholders), tuple(values))
            branchId = cu.lastid()
            log.info("Created branch information for label %s", label)

        cu.execute("""SELECT name, stage_id FROM project_branch_stage
                WHERE project_branch_id = ?""", branchId)
        sqlStages = dict(cu)
        pdStages = [x.name for x in pd.getStages()]
        for stage in set(pdStages) - set(sqlStages):
            isPromotable = (stage != pdStages[-1] and not handle.isExternal)
            cu.execute("""INSERT INTO project_branch_stage (name, label,
                    project_branch_id, project_id, promotable, created_date)
                VALUES (?, ?, ?, ?, ?, now())""",
                (stage, pd.getLabelForStage(stage),
                    branchId, handle.projectId, isPromotable))
            log.info("Created stage information for stage %s on label %s",
                    stage, label)
        for stage in set(pdStages) & set(sqlStages):
            isPromotable = (stage != pdStages[-1] and not handle.isExternal)
            cu.execute("""UPDATE project_branch_stage SET name = ?, label = ?,
                    project_id = ?, promotable = ? WHERE stage_id = ?""",
                    (stage, pd.getLabelForStage(stage),
                        handle.projectId, isPromotable, sqlStages[stage]))
            log.info("Updated stage information for stage %s on label %s",
                    stage, label)
        for stage in set(sqlStages) - set(pdStages):
            cu.execute("DELETE FROM project_branch_stage WHERE stage_id = ?",
                    sqlStages[stage])
            log.info("Deleted stage information for stage %s on label %s",
                    stage, label)
        cu.execute("""UPDATE querysets_queryset SET tagged_date = NULL
            WHERE resource_type = 'project_branch_stage'
            OR resource_type = 'project'""")

    def getPlatformMap(self):
        if self._platformMap is None:
            cu = self.db.cursor()
            cu.execute("SELECT label, platformId FROM Platforms")
            self._platformMap = dict(cu)
        return self._platformMap


if __name__ == '__main__':
    sys.exit(Script().run())
