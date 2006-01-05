#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import os.path
import tempfile
import sys

from conary import checkin
from conary import conarycfg
from conary import versions
from conary.build import cook
from conary.deps import deps
from conary import conaryclient
from conary.repository import changeset
from conary.lib import util

from imagegen import ImageGenerator
from mint import projects

import gencslist

stockFlavors = {
    "1#x86":    "~X,~!alternatives,!bootstrap,~builddocs,~buildtests,"
                "~desktop,~dietlibc,~emacs,~gcj,~gnome,~gtk,~ipv6,~kde,"
                "!kernel.smp,~krb,~ldap,~nptl,pam,~pcre,~perl,~!pie,"
                "~python,~qt,~readline,~!sasl,~!selinux,ssl,~tcl,"
                "tcpwrappers,~tk,~!xfce is: x86(~cmov,~i486,~i586,~i686,~mmx,~sse,~sse2)",

    "1#x86_64": "~X,~!alternatives,!bootstrap,~builddocs,"
                "~buildtests,~desktop,!dietlibc,~emacs,"
                "~gcj,~gnome,~gtk,~ipv6,~kde,~krb,~ldap,"
                "~nptl,pam,~pcre,~perl,~!pie,~python,~qt,"
                "~readline,~!sasl,~!selinux,ssl,~tcl,"
                "tcpwrappers,~tk,~!xfce is: x86_64(~3dnow,~3dnowext,~nx)",
}

class GroupTroveCook(ImageGenerator):
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

            cs = changeset.ChangeSetFromFile(\
                [x for x in os.listdir(path) if x.endswith('.ccs')][0])
            gencslist.extractChangeSets(client, cfg, path, grpName,
                                        versions.VersionFromString(grpVer),
                                        grpFlavor, group = cs)

        finally:
            os.chdir(curDir)

        if ret:
            return ret[0], ret[1], ret[2].freeze()
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
            else:
                checkin.newTrove(repos, cfg, groupTrove.recipeName, path)

            recipeFile = open(groupTrove.recipeName + '.recipe', 'w')
            recipeFile.write(recipe)
            recipeFile.flush()
            recipeFile.close()

            if not trvLeaves:
                checkin.addFiles([groupTrove.recipeName + '.recipe'])

            # commit recipe as changeset
            message = "Auto generated commit from %s.\n%s" % (cfg.name, groupTrove.description)
            checkin.commit(repos, cfg, message)

            troveSpec = "%s[%s]" % (groupTrove.recipeName, str(arch))
            ret = cook.cookItem(repos, cfg, troveSpec)
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
