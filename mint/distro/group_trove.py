#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import os.path
import sys
import tempfile
import time

from conary import checkin
from conary import conarycfg
from conary import constants
from conary import trove
from conary import versions
from conary.build import cook, loadrecipe, use, buildpackage, grouprecipe
from conary.build import errors as builderrors
from conary import build
from conary.deps import deps
from conary import conaryclient
from conary.repository import changeset
from conary.lib import util
from conary.local import database

from imagegen import Generator
from mint import projects

from flavors import stockFlavors
import gencslist

# this is stolen almost entirely from cook.py because Conary converts any
# RecipeFileError (including GroupPathConflicts) into a CookError way too early
# for us to trap the exception we need. If conary ever refactors that exception
# handling, we can switch to using their code.
def cookGroupObject(repos, db, cfg, recipeClass, sourceVersion, macros={},
                    targetLabel = None, alwaysBumpCount=False):
    fullName = recipeClass.name
    changeSet = changeset.ChangeSet()

    recipeObj = recipeClass(repos, cfg, sourceVersion.branch().label(),
                            cfg.buildFlavor, macros)

    cfg.initializeFlavors()
    use.setBuildFlagsFromFlavor(recipeClass.name, cfg.buildFlavor)
    try:
        use.track(True)
        recipeObj.setup()
        use.track(False)
    except builderrors.RecipeFileError, msg:
        raise CookError(str(msg))

    grpFlavor = deps.DependencySet()
    grpFlavor.union(buildpackage._getUseDependencySet(recipeObj))

    try:
        grouprecipe.buildGroups(recipeObj, cfg, repos)
    except builderrors.GroupPathConflicts:
        raise
    except builderrors.RecipeFileError, msg:
        raise CookError(str(msg))

    for group in recipeObj.iterGroupList():
        for (name, ver, flavor) in group.iterTroveList():
            grpFlavor.union(flavor,
                        mergeType=deps.DEP_MERGE_TYPE_DROP_CONFLICTS)

    groupNames = recipeObj.getGroupNames()
    targetVersion = cook.nextVersion(repos, db, groupNames, sourceVersion,
                                grpFlavor, targetLabel,
                                alwaysBumpCount=alwaysBumpCount)
    buildTime = time.time()

    built = []
    for group in recipeObj.iterGroupList():
        groupName = group.name
        grpTrv = trove.Trove(groupName, targetVersion, grpFlavor, None,
                             isRedirect = False)
        grpTrv.setRequires(group.getRequires())
        provides = deps.DependencySet()
        provides.addDep(deps.TroveDependencies, deps.Dependency(groupName))
        grpTrv.setProvides(provides)


        grpTrv.setBuildTime(buildTime)
        grpTrv.setSourceName(fullName + ':source')
        grpTrv.setSize(group.getSize())
        grpTrv.setConaryVersion(constants.version)
        grpTrv.setIsCollection(True)
        grpTrv.setLabelPath(recipeObj.getLabelPath())

        for (troveTup, explicit, byDefault, comps) in group.iterTroveListInfo():
            grpTrv.addTrove(byDefault = byDefault,
                            weakRef=not explicit, *troveTup)

        # add groups which were newly created by this group.
        for name, byDefault, explicit in group.iterNewGroupList():
            grpTrv.addTrove(name, targetVersion, grpFlavor,
                            byDefault = byDefault,
                            weakRef = not explicit)

        grpDiff = grpTrv.diff(None, absolute = 1)[0]
        changeSet.newTrove(grpDiff)

        built.append((grpTrv.getName(), str(grpTrv.getVersion()),
                                        grpTrv.getFlavor()))


    for primaryName in recipeObj.getPrimaryGroupNames():
        changeSet.addPrimaryTrove(primaryName, targetVersion, grpFlavor)

    return (changeSet, built, None)


class GroupTroveCook(Generator):
    def cookObject(self, repos, cfg, item):
        (name, versionStr, flavor) = cook.parseTroveSpec(item)
        if flavor:
            cfg.buildFlavor = deps.overrideFlavor(cfg.buildFlavor, flavor)

        changeSetFile = None
        targetLabel = None

        (loader, sourceVersion) = \
            loadrecipe.recipeLoaderFromSourceComponent(
                                        name, cfg, repos,
                                        versionStr = versionStr)[0:2]
        recipeClass = loader.getRecipe()

        db = database.Database(cfg.root, cfg.dbPath)
        
        troves = cookGroupObject(repos, db, cfg, recipeClass,
                            sourceVersion)
        return troves

    def _localCook(self, groupTrove):
        curDir = os.getcwd()

        ret = None
        try:
            path = tempfile.mkdtemp()
            recipe = groupTrove.getRecipe()
            sourceName = groupTrove.recipeName + ".recipe"
            arch = deps.ThawDependencySet(self.job.getDataValue("arch"))

            cfg = conarycfg.ConaryConfiguration()

            cfg.dbPath = cfg.root = ":memory:"
            cfg.name = "rBuilder Online"
            cfg.contact = "http://www.rpath.org"
            cfg.quiet = False
            cfg.buildLabel = versions.Label('conary.rpath.com@non:exist')
            cfg.dbPath=":memory:"
            cfg.buildFlavor = deps.parseFlavor(stockFlavors[arch.freeze()])
            cfg.initializeFlavors()

            for label in [x.split('@')[0] for x in groupTrove.getLabelPath()]:
                project = self.client.getProjectByFQDN(label)
                cfg.repositoryMap.update(\
                    project.getConaryConfig().repositoryMap)

            client = conaryclient.ConaryClient(cfg)
            repos = client.getRepos()

            os.chdir(path)

            recipeFile = open(groupTrove.recipeName + '.recipe', 'w')
            recipeFile.write(recipe)
            recipeFile.flush()
            recipeFile.close()

            # cook recipe as local changeset
            ret = cook.cookItem(repos, cfg, sourceName)
            sys.stderr.flush()
            sys.stdout.flush()
            grpName, grpVer, grpFlavor = ret[0][0]

            fn = path + "/%s-%s.ccs" % (groupTrove.recipeName,
                                groupTrove.upstreamVersion)

            # prepare a changeset to feed to anaconda
            cs = changeset.ChangeSetFromFile(\
                [x for x in os.listdir(path) if x.endswith('.ccs')][0])
            rc = gencslist.extractChangeSets( \
                client, cfg, path, grpName, versions.VersionFromString(grpVer),
                grpFlavor, group = cs, fn = fn)

            # FIXME: feed changeset List to anaconda.

        finally:
            os.chdir(curDir)

        if ret:
            return grpName, grpVer, grpFlavor.freeze()
        else:
            return None

    def _projectCook(self, groupTrove):
        projectId = groupTrove.projectId
        curDir = os.getcwd()

        ret = None
        try:
            path = tempfile.mkdtemp()
            recipe = groupTrove.getRecipe()
            sourceName = groupTrove.recipeName + ":source"
            arch = deps.ThawDependencySet(self.job.getDataValue("arch"))

            project = self.client.getProject(projectId)

            cfg = project.getConaryConfig(overrideSSL = True,
                                          useSSL = self.cfg.SSL)
            cfg.name = "rBuilder Online"
            cfg.contact = "http://www.rpath.org"
            cfg.quiet = True
            cfg.buildLabel = versions.Label(project.getLabel())
            cfg.buildFlavor = deps.parseFlavor(stockFlavors[arch.freeze()])
            cfg.initializeFlavors()

            repos = conaryclient.ConaryClient(cfg).getRepos()
            trvLeaves = repos.getTroveLeavesByLabel(\
                {sourceName : {cfg.buildLabel : None} }).get(sourceName, [])

            os.chdir(path)
            if trvLeaves:
                checkin.checkout(repos, cfg, path, groupTrove.recipeName)
                added = True
            else:
                checkin.newTrove(repos, cfg, groupTrove.recipeName, path)
                added = False

            tries = 0
            while tries < 2:
                recipeFile = open(groupTrove.recipeName + '.recipe', 'w')
                recipeFile.write(recipe)
                recipeFile.flush()
                recipeFile.close()

                if not trvLeaves and not added:
                    checkin.addFiles([groupTrove.recipeName + '.recipe'])
                    added = True

                # commit recipe as changeset
                message = "Auto generated commit from %s.\n%s" % \
                          (cfg.name, groupTrove.description)
                checkin.commit(repos, cfg, message)

                troveSpec = "%s[%s]" % (groupTrove.recipeName, str(arch))
                removeTroves = []
                try:
                    # try a cook
                    troves = self.cookObject(repos, cfg, troveSpec)
                except build.errors.GroupPathConflicts, e:
                    labelPath = groupTrove.getLabelPath()
                    for group, conflicts in e.conflicts.items():
                        for l in labelPath:
                            matches = []
                            # loop through each conflicting trove for each label in the path,
                            # and pick the first conflicting trove that matches.
                            for conflict in conflicts:
                                matches = [x for x in conflict if x[1].branch().label().asString() == l]
                                if matches:
                                    con = list(conflict)
                                    con.remove(matches[0])
                                    removeTroves.extend([x for x in con])
                                    break
                            if matches:
                                break
                for rm in removeTroves:
                    recipe += "        r.remove('%s', '%s', '%s')\n" % (rm[0], rm[1].asString(), rm[2].freeze())
                recipe += "\n"
                tries += 1

            sys.stderr.flush()
            sys.stdout.flush()
            repos.commitChangeSet(troves[0], callback = None)
            
            ret = troves[1][0]

        finally:
            os.chdir(curDir)
            util.rmtree(path)

        if ret:
            return ret[0], ret[1], ret[2].freeze()
        else:
            return None

    def write(self):
        self.status("Cooking group")
        groupTrove = self.client.getGroupTrove(self.job.getGroupTroveId())
        projectId = groupTrove.projectId
        if not projectId:
            return self._localCook(groupTrove)
        else:
            return self._projectCook(groupTrove)
