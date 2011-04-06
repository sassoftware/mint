#
# Copyright (c) 2011 rPath, Inc.
#

import logging
import simplejson

from conary import changelog, conaryclient
from conary.conaryclient import filetypes


from rmake3.worker import plug_worker
from mint.rmake3_package_creator import constants
from mint.rmake3_package_creator import models

log = logging.getLogger('rmake3.task')

class BaseTask(plug_worker.TaskHandler):
    pass

class TaskCommitSource(BaseTask):
    taskType = constants.NS_TASK_COMMIT_SOURCE

    def run(self):
        self.setConfiguration()
        pkgSource = self.commitSource()
        response = models.Response(pkgSource.toXml())
        self.setData(response.freeze())
        self.sendStatus(constants.Codes.OK, "Done")

    def setConfiguration(self):
        data = self.getData()
        self.mincfg = data.mincfg.thaw()
        self.sourceData = data.sourceData.thaw()
        self.conarycfg = self.mincfg.createConaryConfig()

    def commitSource(self):
        cfg = self.conarycfg
        client = self.getConaryClient()
        self.sendStatus(constants.Codes.MSG_STATUS, "Creating changeset")
        try:
            cs = self.createChangeSet(client, cfg, self.sourceData)
        except:
            raise
        self.sendStatus(constants.Codes.MSG_STATUS, "Committing changeset")
        repos = client.getRepos()
        try:
            repos.commitChangeSet(cs)
        except:
            raise
        trvCs = cs.iterNewTroveList().next()
        trvName, trvVersion, trvFlavor = trvCs.getNewNameVersionFlavor()
        trvModel = models.Trove.fromNameVersionFlavor(trvName,
            trvVersion, trvFlavor)
        pkgSource = models.PackageSource(trove=trvModel, built="true")
        return pkgSource

    def getConaryClient(self):
        return conaryclient.ConaryClient(self.conarycfg)

    @classmethod
    def createChangeSet(cls, client, cfg, sourceData):
        pd = sourceData.productDefinitionLocation
        productDefinitionDict = dict(
            hostname=pd.hostname, shortname=pd.shortname,
            namespace=pd.namespace, version=pd.version)
        pkgCreatorData = simplejson.dumps(dict(
            productDefinition=productDefinitionDict,
            stageLabel=sourceData.stageLabel))
        changeLog = changelog.ChangeLog(name=cfg.name,
            contact=(cfg.contact or ''),
            message=sourceData.commitMessage)

        pathDict = cls.computeFileMap(sourceData)

        cs = client.createSourceTrove(sourceData.name,
            sourceData.label, sourceData.version,
            pathDict, changeLog, factory=sourceData.factory,
            pkgCreatorData=pkgCreatorData)
        return cs

    @classmethod
    def computeFileMap(cls, sourceData):
        fmap = {}
        for fileModel in sourceData.fileList:
            if fileModel.contents is not None:
                contents = fileModel.contents
            else:
                contents = file(fileModel.path)
            fmap[fileModel.name] = filetypes.RegularFile(contents=contents,
                config = bool(fileModel.isConfig))
        return fmap

class TaskDownloadFiles(BaseTask):
    taskType = constants.NS_TASK_DOWNLOAD_FILES

    def run(self):
        self.setConfiguration()
        self.commitSource()
        response = models.Response("Hoorah!")
        self.setData(response.freeze())
        self.sendStatus(constants.Codes.OK, "Done")

