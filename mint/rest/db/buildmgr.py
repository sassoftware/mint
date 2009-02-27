from conary.deps import deps
from conary import versions

from mint import buildtypes
from mint.rest import errors
from mint.rest.api import models

class BuildManager(object):
    def __init__(self, cfg, db, auth):
        self.cfg = cfg
        self.db = db
        self.auth = auth

    def _getBuilds(self, fqdn, extraJoin='', extraWhere='',
                   extraArgs=None, getOne=False):
        hostname = fqdn.split('.')[0]
        sql = '''
        SELECT buildId, hostname,
               pubReleaseId as release,  
               buildType, Builds.name, Builds.description, troveName,
               troveVersion, troveFlavor, troveLastChanged,
               Builds.timeCreated, CreateUser.username as creator, 
               Builds.timeUpdated, 
               UpdateUser.username as updater, buildCount
            FROM Builds 
            %(join)s
            JOIN Projects USING(projectId)
            JOIN Users as CreateUser ON (createdBy=CreateUser.userId)
            JOIN Users as UpdateUser ON (updatedBy=UpdateUser.userId)
            WHERE hostname=? AND deleted=0 %(where)s''' 
        sql = sql % dict(where=extraWhere, join=extraJoin)
        args = (hostname,)
        if extraArgs:
            args += tuple(extraArgs)
        cu = self.db.cursor()
        cu.execute(sql, *args)
        if getOne:
            row = dict(self.db._getOne(cu, errors.BuildNotFound, 
                                       args))
            row['troveFlavor'] = deps.ThawFlavor(row['troveFlavor'])
            row['troveVersion'] = versions.ThawVersion(row['troveVersion'])
            row['buildType'] = buildtypes.typeNamesShort[row['buildType']]
            build = models.Build(**row)
            build.files = self.listFilesForBuild(hostname, build.buildId)

        builds = models.BuildList()
        for row in cu:
            row = dict(row)
            row['troveFlavor'] = deps.ThawFlavor(row['troveFlavor'])
            row['troveVersion'] = versions.ThawVersion(row['troveVersion'])
            row['buildType'] = buildtypes.typeNamesShort[row['buildType']]
            build = models.Build(**row)
            build.files = self.listFilesForBuild(hostname, build.buildId)
            builds.builds.append(build)
        return builds

    def listBuildsForProduct(self, fqdn):
        return self._getBuilds(fqdn)

    def getBuildForProduct(self, fqdn, buildId):
        return self._getBuilds(fqdn, '', 'AND buildId=?', [buildId], getOne=True)

    def listBuildsForRelease(self, fqdn, releaseId):
        return self._getBuilds(fqdn, '', ' AND pubReleaseId=?', 
                               [releaseId])

    def listFilesForBuild(self, fqdn, buildId):
        hostname = fqdn.split('.')[0]
        cu = self.db.cursor()
        cu.execute('''SELECT fileId, buildId, filename, title, size, sha1
                      FROM BuildFiles
                      JOIN Builds USING(buildId)
                      JOIN Projects USING(projectId)
                      WHERE buildId=? and hostname=?
                      ORDER BY idx''', buildId, hostname)
        buildFiles = []
        for row in cu:
            d = dict(row)
            file = models.BuildFile(**d)
            buildFiles.append(file)
        for file in buildFiles:
            cu.execute('''SELECT urlType, url
                          FROM BuildFilesUrlsMap 
                          JOIN FilesUrls USING(urlId)
                          WHERE fileId=?''', file.fileId)
            urls = []
            for row in cu:
                d = dict(row)
                urls.append(models.FileUrl(**d))
            file.urls = urls
        return models.BuildFileList(buildFiles)
