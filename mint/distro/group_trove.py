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
from conary import versions
from conary.build import cook
from conary import build
from conary.deps import deps
from conary import conaryclient
from conary.repository import changeset
from conary.lib import util

from imagegen import Generator
from mint import projects

from flavors import stockFlavors
import gencslist


class GroupTroveCook(Generator):
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
                    ret = cook.cookItem(repos, cfg, troveSpec)
                except build.errors.GroupPathConflicts, e:
                    labelPath = groupTrove.getLabelPath()
                    for group, conflicts in e.conflicts.items():
                        for l in labelPath:
                            matches = []
                            # loop through each conflicting trove for each label in the path,
                            # and pick the first conflicting trove that matches.
                            for conflict in conflicts:
                                matches = [x for x in conflict[0] if x[1].branch().label().asString() == l]
                                if matches:
                                    con = list(conflict[0])
                                    con.remove(matches[0])
                                    removeTroves.extend([x for x in con])
                                    break
                            if matches:
                                break
                else:
                    break
                for rm in removeTroves:
                    recipe += "        r.remove('%s', '%s', '%s')\n" % (rm[0], rm[1].asString(), rm[2].freeze())
                recipe += "\n"
                tries += 1

            sys.stderr.flush()
            sys.stdout.flush()
            ret = ret[0][0]
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
