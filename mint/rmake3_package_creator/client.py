#
# Copyright (c) 2011 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

import tempfile

from conary import conarycfg
from conary import versions

from rpath_repeater import client
from mint.rmake3_package_creator import constants, models

class Client(client.RepeaterClient):
    def createJob(self, namespace, params):
        return self._createRmakeJob(namespace, params)

    def pc_downloadFiles(self, urls, resultsLocation):
        # XXX we should use the config for this
        destDir = "/srv/rbuilder/package-creator-downloads"
        prefix = "pc-file-download-"
        urlList = []
        for url in urls:
            # Create a temporary file just to get a unique path. We'll close
            # it immediately after that. The file will disappear, which is
            # good, because rmake runs as user rmake while we're running as
            # apache.
            tmpf = tempfile.NamedTemporaryFile(dir=destDir, prefix=prefix)
            path = tmpf.name
            tmpf.close()
            urlList.append(models.DownloadFile(url=url, path=path))

        params = models.DownloadFilesParams()
        params.urlList = urls
        params.resultsLocation = self.ResultsLocation(path=resultsLocation)

        assert isinstance(params, models.DownloadFilesParams)
        assert isinstance(params.resultsLocation, self.ResultsLocation)
        if not isinstance(params.urlList, models.ImmutableList):
            params.urlList = models.ImmutableList(params.urlList)
        return self.createJob(constants.NS_JOB_DOWNLOAD_FILES, params)

    def pc_packageSourceCommit(self, name, version, label, factory,
                               user, password, email, resultsLocation):
        conaryLabel = versions.Label(label)

        cfg = conarycfg.ConaryConfiguration(readConfigFiles=False)
        cfg.configLine('name Automatic Commit from rBuilder')
        cfg.configLine('contact %s' % email)
        cfg.configLine('buildLabel %s' % conaryLabel.asString())
        # TODO: figure how to set the host
        host = "https://127.0.0.1/conaryrc"
        cfg.configLine('repositoryMap %s %s' % (conaryLabel.getHost(), host))
        cfg.configLine('user * %s %s' % (user, password))

        # TODO: figure how to set version, not sure we can require a Product
        # definition if a goal is to be able to just commit to any old
        # repository when you build a package.
        pdl = models.ProductDefinitionLocation(
            hostname=conaryLabel.getHost(),
            shortname=conaryLabel.getHost().split('.')[0], 
            namespace=conaryLabel.getNamespace(), 
            version='1')

        recipeContents = """
        class OverrideRecipe(FactoryRecipeClass):
            def preProcess(r):
                '''This function is run at the beginning of setup'''
            def postProcess(r):",
                '''This function is run at the end of setup'''
        """

        mincfg = models.MinimalConaryConfiguration.fromConaryConfig(cfg)
        mincfg.createConaryConfig().writeToFile("/tmp/conarycfg")

        # TODO: again, not sure we can require stageLabel here
        sourceData = models.SourceData(name='%s:source' % name,
            label=label, version=version,
            productDefinitionLocation=pdl,
            factory=factory,
            stageLabel='devel', commitMessage="Committing\n",
        )
        sourceData.fileList = models.ImmutableList([
            models.File(name="%s.recipe" % name, contents = recipeContents)
        ])

        params = models.PackageSourceCommitParams(
            mincfg=mincfg, sourceData=sourceData)
        resultsLocation = self.ResultsLocation(path=resultsLocation)
        params.resultsLocation = resultsLocation

        assert isinstance(params, models.PackageSourceCommitParams)
        assert isinstance(params.resultsLocation, self.ResultsLocation)
        return self.createJob(constants.NS_JOB_COMMIT_SOURCE, params)

    def pc_packageSourceBuild(self, params):
        assert isinstance(params, models.PackageSourceBuildParams)
        assert isinstance(params.resultsLocation, self.ResultsLocation)
        return self.createJob(constants.NS_JOB_BUILD_SOURCE, params)
