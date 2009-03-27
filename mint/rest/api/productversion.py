#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from conary.lib import digestlib

from restlib import response

from mint import buildtypes

from mint.rest.modellib import converter
from mint.rest.api import base
from mint.rest.api import models
from mint.rest.api import requires
from mint.rest.middleware import auth

class BuildDefinitionMixIn(object):
    def _makeBuildDefinition(self, buildDef, pd, extraParams, modelClass):
        buildDefId = self.getBuildDefId(buildDef)
        # Build definitions don't have a display name, build templates do
        displayName = getattr(buildDef, "displayName", buildDef.name)
        kw = extraParams.copy()
        kw.update(dict(name = buildDef.name,
                       displayName = displayName,
                       id = buildDefId,
                       **extraParams))
        # Ignore build templates for now, they do not provide a unique
        # name
        if buildDef.flavorSetRef:
            fset = buildDef.flavorSetRef
            fset = pd.getFlavorSet(fset,
                     pd.getPlatformFlavorSet(fset, None))
            if fset:
                kw['flavorSet'] = models.FlavorSet(id = fset.name,
                                            name = fset.name,
                                            displayName = fset.displayName,
                                            **extraParams)
        if buildDef.architectureRef:
            arch = buildDef.architectureRef
            arch = pd.getArchitecture(arch,
                pd.getPlatformArchitecture(arch, None))
            if arch:
                kw['architecture'] = models.Architecture(id = arch.name,
                    name = arch.name,
                    displayName = arch.displayName,
                    **extraParams)
        if buildDef.containerTemplateRef:
            ctemplRef = buildDef.containerTemplateRef
            ctempl = pd.getContainerTemplate(ctemplRef,
                pd.getPlatformContainerTemplate(ctemplRef, None))
            if ctempl and ctemplRef in buildtypes.xmlTagNameImageTypeMap:
                displayName = buildtypes.xmlTagNameImageTypeMap[ctemplRef]
                displayName = buildtypes.typeNamesMarketing[displayName]
                if hasattr(buildDef, 'getBuildImage'):
                    # This is a build
                    imageField = buildDef.getBuildImage()
                else:
                    # This is a build template
                    imageField = ctempl
                imageParams = models.ImageParams(**imageField.fields)
                kw['container'] = models.ContainerFormat(
                    id = ctemplRef,
                    name = ctemplRef,
                    displayName = displayName,
                    options = imageParams,
                    **extraParams)
                # XXX we need to add the rest of the fields here too
        if hasattr(buildDef, 'getBuildImageGroup'):
            grp = buildDef.getBuildImageGroup()
            if grp:
                kw['imageGroup'] = grp
        if hasattr(buildDef, 'getBuildSourceGroup'):
            grp = buildDef.getBuildSourceGroup()
            if grp:
                kw['sourceGroup'] = grp
        if hasattr(buildDef, 'getBuildStages'):
            kw['stages'] = [ models.StageHref(href = x, **extraParams)
                for x in buildDef.getBuildStages() ]
        model = modelClass(**kw)
        return model

    @classmethod
    def getBuildDefId(cls, buildDef):
        if not hasattr(buildDef, 'hexDigest'):
            buildDef.hexDigest = cls.computeBuildDefinitionDigest(buildDef)
        return buildDef.hexDigest

    @classmethod
    def computeBuildDefinitionDigest(cls, buildDef):
        # Since we don't have unique IDs for builds, we need to manufacture
        # some - we'll digest the three refs.
        digest = digestlib.md5()
        if buildDef.containerTemplateRef:
            digest.update(buildDef.containerTemplateRef)
        if buildDef.architectureRef:
            digest.update(buildDef.architectureRef)
        if buildDef.flavorSetRef:
            digest.update(buildDef.flavorSetRef)
        return digest.hexdigest()

class ProductVersionStages(base.BaseController, BuildDefinitionMixIn):
    modelName = 'stageName'

    urls = {'images' : dict(GET='getImages'),
            'imageDefinitions' : dict(GET='getImageDefinitions'),
           }

    def index(self, request, hostname, version):
        return self.db.getProductVersionStages(hostname, version)

    def get(self, request, hostname, version, stageName):
        return self.db.getProductVersionStage(hostname, version, stageName)

    def getImages(self, request, hostname, version, stageName):
        return self.db.listImagesForProductVersionStage(hostname, version, stageName)

    def getImageDefinitions(self, request, hostname, version, stageName):
        extraParams = dict(hostname = hostname, version = version,
            stageName = stageName)
        pd = self.db.getProductVersionDefinition(hostname, version)
        buildDefs = pd.getBuildsForStage(stageName)
        buildDefModels = [ self._makeBuildDefinition(x, pd, extraParams,
            models.BuildDefinition) for x in buildDefs ]
        bdefs = models.BuildDefinitions(buildDefinitions = buildDefModels)
        return bdefs


class ProductVersionDefinition(base.BaseController):

    def index(self, request, hostname, version):
        pd = self.db.getProductVersionDefinition(hostname, version)
        return response.Response(self._fromProddef(pd))

    def update(self, request, hostname, version):
        pd = self._toProddef(request)
        self.db.setProductVersionDefinition(hostname, version, pd)
        return self.index(request, hostname, version)

    def _toProddef(self, request):
        from rpath_common.proddef import api1 as proddef
        return proddef.ProductDefinition(fromStream=request.read())

    def _fromProddef(self, pd):
        import cStringIO as StringIO
        sio = StringIO.StringIO()
        pd.serialize(sio)
        return sio.getvalue()


class ProductVersionController(base.BaseController, BuildDefinitionMixIn):

    modelName = 'version'
    urls = {'platform'   : dict(GET='getPlatform',
                                PUT='setPlatform',
                                POST='updatePlatform'),
            'stages'     : ProductVersionStages,
            'definition' : ProductVersionDefinition,
            'images'     : dict(GET='getImages'),
            'imageTypeDefinitions' : dict(GET='getImageTypeDefinitions'),
            'imageDefinitions' : dict(GET='getImageDefinitions',
                                      PUT='setImageDefinitions'),}

    @auth.public
    def index(self, request, hostname):
        return self.db.listProductVersions(hostname)

    def get(self, request, hostname, version):
        return self.db.getProductVersion(hostname, version)

    @requires('productVersion', models.ProductVersion)
    def update(self, request, hostname, version, productVersion):
        return self.db.updateProductVersion(hostname, version, productVersion)
        
    @requires('productVersion', models.ProductVersion)
    def create(self, request, hostname, productVersion):
        self.db.createProductVersion(hostname, productVersion)
        return self.get(request, hostname, productVersion.name)

    def getImages(self, request, hostname, version):
        return self.db.listImagesForProductVersion(hostname, version)

    def getPlatform(self, request, hostname, version):
        return self.db.getProductVersionPlatform(hostname, version)

    @requires('platform', models.Platform)
    def setPlatform(self, request, hostname, version, platform):
        self.db.rebaseProductVersionPlatform(hostname, version, platform.label)
        return self.getPlatform(request, hostname, version)

    def updatePlatform(self, request, hostname, version):
        self.db.rebaseProductVersionPlatform(hostname, version)
        return self.getPlatform(request, hostname, version)

    def getImageTypeDefinitions(self, request, hostname, version):
        extraParams = dict(hostname = hostname, version = version)
        pd = self.db.getProductVersionDefinition(hostname, version)
        buildTemplates = pd.platform.getBuildTemplates()
        # XXX Grab build templates from the product too
        buildDefModels = [ self._makeBuildDefinition(x, pd, extraParams,
            models.BuildTemplate) for x in buildTemplates ]
        bdefs = models.BuildTemplates(buildTemplates = buildDefModels)
        return bdefs

    def getImageDefinitions(self, request, hostname, version):
        extraParams = dict(hostname = hostname, version = version)
        pd = self.db.getProductVersionDefinition(hostname, version)
        buildDefs = pd.getBuildDefinitions()
        buildDefModels = [ self._makeBuildDefinition(x, pd, extraParams,
            models.BuildDefinition) for x in buildDefs ]
        bdefs = models.BuildDefinitions(buildDefinitions = buildDefModels)
        return bdefs

    def setImageDefinitions(self, request, hostname, version):
        imageDefinitionsData = request.read()
        model = converter.fromText('xml', imageDefinitionsData,
            models.BuildDefinitions, self, None)
        pd = self.db.setProductVersionBuildDefinitions(hostname, version,
            model)
        buildDefs = pd.getBuildDefinitions()
        extraParams = dict(hostname = hostname, version = version)
        buildDefModels = [ self._makeBuildDefinition(x, pd, extraParams,
            models.BuildDefinition) for x in buildDefs ]
        bdefs = models.BuildDefinitions(buildDefinitions = buildDefModels)
        return bdefs

