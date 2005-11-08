#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import os.path

import checkin
import tempfile
import conarycfg
from repository import netclient
import versions
from build import cook

from imagegen import ImageGenerator
from mint import projects

class GroupTroveCook(ImageGenerator):
    def write(self):
        self.status("Cooking group")
        groupTrove = self.client.getGroupTrove(self.job.getGroupTroveId())

        curDir = os.getcwd()

        ret = None
        try:
            path = tempfile.mkdtemp()
            projectId = groupTrove.projectId
            recipe = groupTrove.getRecipe()
            sourceName = groupTrove.recipeName + ":source"

            project = self.client.getProject(projectId)

            cfg = conarycfg.ConaryConfiguration()
            cfg.name = "rBuilder Online"
            cfg.contact = "http://www.rpath.org"
            cfg.quiet = True
            cfg.buildLabel = versions.Label(project.getLabel())

            cfg.initializeFlavors()
            cfg.repositoryMap = project.getConaryConfig().repositoryMap
            cfg.repositoryMap.update({'conary.rpath.com': 'http://conary-commits.rpath.com/conary/'})

            repos = netclient.NetworkRepositoryClient(cfg.repositoryMap)

            trvLeaves = repos.getTroveLeavesByLabel({sourceName : {cfg.buildLabel : None} }).get(sourceName, [])

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
            message = "Auto generated commit from rBuilder online."
            checkin.commit(repos, cfg, message)
            ret = cook.cookItem(repos, cfg, groupTrove.recipeName)
            ret = ret[0][0]
        finally:
            os.chdir(curDir)

        if ret:
            return ret[0], ret[1], ret[2].freeze()
        else:
            return None
