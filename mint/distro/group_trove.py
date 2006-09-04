#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import os.path
import sys
import tempfile
import time

from mint import helperfuncs
from mint import projects
from mint.flavors import stockFlavors
import mint.distro.gencslist
from mint.distro.imagegen import Generator

from conary import checkin
from conary import conarycfg
from conary import versions
from conary.build import cook
from conary import build
from conary.deps import deps
from conary import conaryclient
from conary.repository import changeset
from conary.lib import util


class GroupTroveCook(Generator):
    def _projectCook(self, groupTrove):
        projectId = groupTrove.projectId
        curDir = os.getcwd()

        ret = None
        e = None
        try:
            path = tempfile.mkdtemp()
            recipe = groupTrove.getRecipe()
            sourceName = groupTrove.recipeName + ":source"
            flavor = deps.ThawFlavor(self.job.getDataValue("arch"))

            # XXX: this depends on dictionary ordering for x86_64 to work properly, since
            # an x86_64 flavor also includes an x86 dep.
            arch = deps.Flavor()
            arch.addDep(deps.InstructionSetDependency, flavor.members[deps.DEP_CLASS_IS].members.values()[0])

            project = self.client.getProject(projectId)

            cfg = project.getConaryConfig()
            cfg.name = "rBuilder Online"
            cfg.contact = "http://www.rpath.org"
            cfg.quiet = True
            cfg.buildLabel = versions.Label(project.getLabel())
            cfg.buildFlavor = deps.parseFlavor(stockFlavors[arch.freeze()])
            cfg.initializeFlavors()
            self.readConaryRc(cfg)

            repos = conaryclient.ConaryClient(cfg).getRepos()
            trvLeaves = repos.getTroveLeavesByLabel(\
                {sourceName : {cfg.buildLabel : None} }).get(sourceName, [])

            os.chdir(path)
            if trvLeaves:
                checkin.checkout(repos, cfg, path, [groupTrove.recipeName])
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
                checkin.commit(repos, cfg, message.encode('ascii', 'replace'))

                troveSpec = "%s[%s]" % (groupTrove.recipeName, str(arch))
                removeTroves = []
                try:
                    ret = cook.cookItem(repos, cfg, troveSpec)
                except build.errors.GroupPathConflicts, e:
                    if tries:
                        import itertools
                        conflicts = [y for y in itertools.chain( \
                            *[x[1] for x in e.conflicts.items()])]
                        break
                    labelPath = groupTrove.getLabelPath()
                    for group, conflicts in e.conflicts.items():
                        for conflict in conflicts:
                            expMatches = [x for x in conflict[0] \
                                      if groupTrove.troveInGroup( \
                                x[0].split(':')[0], str(x[1]), x[2].freeze())]

                            for l in labelPath:
                                # if expMatches is not empty, we must honor it.
                                # otherwise fallback to all conflicts.
                                matches = [x for x in \
                                          (expMatches or conflict[0]) \
                                          if x[1].branch().label().asString() == l]
                                if matches:
                                    con = list(conflict[0])
                                    # very rare corner case: 2 matches on same
                                    # branch: largest version number is best.
                                    con.remove(max(matches))
                                    con = [(x[0].split(':')[0], x[1], x[2], group) \
                                         for x in con]
                                    for trvCon in con:
                                        if trvCon not in removeTroves:
                                            removeTroves.append(trvCon)
                                    break
                else:
                    break
                for rm in removeTroves:
                    recipe += "        r.remove('%s', '%s', '%s', groupName='%s')\n" % (rm[0], rm[1].asString(), str(rm[2]), rm[3])
                recipe += "\n"
                tries += 1

            sys.stderr.flush()
            sys.stdout.flush()

            if not ret:
                raise RuntimeError("Conflicts which couldn't be automatically "
                                   "corrected have occured:\n%s " % \
                                   '\n'.join(\
                    ['\n'.join([z[0] + "=" + str(z[1]) + "[" + str(z[2]) + "]"\
                               for z in y]) for y in [x[0] \
                                                      for x in conflicts]]))

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
        return self._projectCook(groupTrove)
