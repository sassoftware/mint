#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.db import connection
import logging
from mint.django_rest.rbuilder.images import models 
from mint.django_rest.rbuilder.manager import basemanager
from conary.lib import sha1helper
from mint.lib import data as datatypes
from mint import buildtypes
from conary import trovetup
from conary import versions
from conary.deps import deps
import time

log = logging.getLogger(__name__)
exposed = basemanager.exposed

class ImagesManager(basemanager.BaseManager):
 
    @exposed
    def getImageBuild(self, image_id):
        return models.Image.objects.get(pk=image_id)
        
    @exposed
    def getImageBuilds(self):
        Images = models.Images()
        Images.image = models.Image.objects.all()
        return Images

    @exposed
    def createImageBuild(self, image):
        outputToken = sha1helper.sha1ToString(file('/dev/urandom').read(20))
        buildData = [('outputToken', outputToken, datatypes.RDT_STRING)]
        buildType = image.image_type
        buildName = image.name
        if image.trove_version is None:
            image.trove_version = versions.VersionFromString(
                '/local@local:COOK/1-1-1', timeStamps = [ 0.1 ])
        
        # Look up the build type by name too - and fall back to what the user
        # specified
        buildType = buildtypes.xmlTagNameImageTypeMap.get(buildType, buildType)
        cu = connection.cursor()
        fqdn = image.project.repository_hostname
        productId = self.restDb.getProductId(fqdn)
        troveTuple = self._getOutputTrove(image)
        if image.trove_version and image.stage_name:
            stage = image.stage_name
            productVersionId = image.project.project_branches.values()[0]['branch_id']
        else:
            troveLabel = troveTuple[1].trailingLabel()
            productVersionId, stage = self.restDb.productMgr.getProductVersionForLabel(
                                                    fqdn, troveLabel)

        sql = '''INSERT INTO Builds (projectId, name, buildType, timeCreated, 
                                    buildCount, createdBy, troveName, 
                                    troveVersion, troveFlavor, stageName, 
                                    productVersionId) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

        cu.execute(
        sql, [productId, buildName, buildType, time.time(), 0, self.restDb.auth.userId,
             image.trove_name, image.trove_version, image.trove_flavor, stage, productVersionId])
        
        buildId = cu.lastrowid        
        buildDataTable = self.restDb.db.buildData
        for name, value, dataType in buildData:
            try:
                buildData = models.BuildData.objects.get(build__image_id=buildId, name=name)
            except: # come back and catch MatchingQueryDoesNotExist
                build = models.Image.objects.get(pk=buildId)
                buildData = models.BuildData(build=build, name=name)
            buildData.value = value
            buildData.data_type = dataType
            buildData.save()

        # FINISH
        
        # # clear out all "important flavors"
        # for x in buildtypes.flavorFlags.keys():
        #     buildDataTable.removeDataValue(buildId, x, commit=False)
        # 
        # # and set the new ones
        # for x in builds.getImportantFlavors(troveTuple[2]):
        #     buildDataTable.setDataValue(buildId, x, 1, data.RDT_INT, 
        #                                 commit=False)
        return image

    def _getOutputTrove(self, image):
        if image.output_trove is None:
            return None
        name, version, flavor = trovetup.TroveSpec.fromString(image.output_trove)
        version = versions.VersionFromString(version)
        if flavor is None:
            flavor = deps.Flavor()
        return trovetup.TroveTuple(name, version, flavor)
        
    @exposed
    def updateImageBuild(self, image_id, image):
        image.save()
        return image
        
    @exposed
    def deleteImageBuild(self, image_id):
        models.Image.objects.get(pk=image_id).delete()

    @exposed
    def getImageBuildFile(self, image_id, file_id):
        build_file = models.BuildFile.objects.get(file_id=file_id)
        return build_file
        
    @exposed
    def getImageBuildFiles(self, image_id):
        BuildFiles = models.BuildFiles()
        build_files = models.BuildFile.objects.filter(image=image_id)
        BuildFiles.file = build_files
        return BuildFiles
    
    @exposed
    def getUnifiedImages(self):
        ''' 
        Return all images available on both the targets & rbuilder...
        once RBAC capable, this should be a queryset redirect instead, 
        but this method should be kept around for CLI usage.

        We may also have some variations that filter it in a more fine
        grained way, like images a user can actually deploy, etc.
        '''

        # FIXME: placeholder
        images = models.Images()
        images.image = [
            models.Image(id=1, name='placeholder'),
            models.Image(id=2, name='placeholder')
        ]
        return images
        
    @exposed
    def getReleases(self):
        Releases = models.Releases()
        Releases.release = models.Release.objects.all()
        return Releases
        
    @exposed
    def getReleaseById(self, release_id):
        return models.Release.objects.get(pk=release_id)
        
    @exposed
    def createRelease(self, release):
        release.save()
        return release
        
    @exposed
    def updateRelease(self, release_id, release):
        release.save()
        return release
        
    @exposed
    def getBuildLog(self, image_id):
        image = models.Image.objects.get(pk=image_id)
        hostname = image.project.hostname
        return self.restDb.getImageFile(hostname, image_id, 'build.log')
        
    @exposed
    def getImageType(self, image_type_id):
        return models.ImageType.objects.get(image_type_id=image_type_id)
        
    @exposed
    def getImageTypes(self):
        return models.ImageType.objects.all()
        