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

from rpath_repeater import client
from mint.rmake3_package_creator import constants, models

class Client(client.RepeaterClient):
    def createJob(self, namespace, params):
        return self._createRmakeJob(namespace, params)

    def pc_downloadFiles(self, params):
        assert isinstance(params, models.DownloadFilesParams)
        assert isinstance(params.resultsLocation, self.ResultsLocation)
        if not isinstance(params.urlList, models.ImmutableList):
            params.urlList = models.ImmutableList(params.urlList)
        return self.createJob(constants.NS_JOB_DOWNLOAD_FILES, params)

    def pc_packageSourceCommit(self, params):
        assert isinstance(params, models.PackageSourceCommitParams)
        assert isinstance(params.resultsLocation, self.ResultsLocation)
        return self.createJob(constants.NS_JOB_COMMIT_SOURCE, params)
