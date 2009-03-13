#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from restlib import response

from mint import buildtypes

from mint.rest.api import base
from mint.rest.api import models
from mint.rest.api import requires

class BuildDefinitionMixIn(object):
    def _makeBuildDefinition(self, buildDef, pd):
        # Build definitions don't have a display name, build templates do
        displayName = getattr(buildDef, "displayName", buildDef.name)
        kw = dict(name = buildDef.name,
                  displayName = displayName,
                  id = buildDef.name)
        # Ignore build templates for now, they do not provide a unique
        # name
        if buildDef.flavorSetRef:
            fset = buildDef.flavorSetRef
            fset = pd.getFlavorSet(fset,
                     pd.getPlatformFlavorSet(fset, None))
            if fset:
                kw['flavorSet'] = models.FlavorSet(href = fset.name,
                                            name = fset.name,
                                            displayName = fset.displayName)
        if buildDef.architectureRef:
            arch = buildDef.architectureRef
            arch = pd.getArchitecture(arch,
                pd.getPlatformArchitecture(arch, None))
            if arch:
                kw['architecture'] = models.Architecture(href = arch.name,
                    name = arch.name,
                    displayName = arch.displayName)
        if buildDef.containerTemplateRef:
            ctemplRef = buildDef.containerTemplateRef
            ctempl = pd.getContainerTemplate(ctemplRef,
                pd.getPlatformContainerTemplate(ctemplRef, None))
            if ctempl and ctemplRef in buildtypes.xmlTagNameImageTypeMap:
                displayName = buildtypes.xmlTagNameImageTypeMap[ctemplRef]
                displayName = buildtypes.typeNamesMarketing[displayName]
                kw['container'] = models.ContainerFormat(
                    href = ctemplRef,
                    name = ctemplRef,
                    displayName = displayName)
                # XXX we need to add the rest of the fields here too
        model = models.BuildDefinition(**kw)
        return model

class ProductVersionStagesDefinition(base.BaseController, BuildDefinitionMixIn):
    urls = {
        'builds' : dict(GET = 'getBuilds'),
    }

    def getBuilds(self, request, hostname, version, stageName):
        pd = self.db.getProductVersionDefinition(hostname, version)
        buildDefs = pd.getBuildsForStage(stageName)
        buildDefModels = [ self._makeBuildDefinition(x, pd) for x in buildDefs ]
        bdefs = models.BuildDefinitions(buildDefinitions = buildDefModels)
        return bdefs

class ProductVersionStages(base.BaseController):
    modelName = 'stageName'

    urls = {'images' : dict(GET='getImages'),
            'definition' : ProductVersionStagesDefinition }
    
    def index(self, request, hostname, version):
        return self.db.getProductVersionStages(hostname, version)

    def get(self, request, hostname, version, stageName):
        return self.db.getProductVersionStage(hostname, version, stageName)

    def getImages(self, request, hostname, version, stageName):
        return self.db.getProductVersionStageImages(hostname, version, stageName)

class ProductVersionDefinition(base.BaseController, BuildDefinitionMixIn):
    urls = dict(images = dict(GET = 'getImageDefinitions'))

    def index(self, request, hostname, version):
        pd = self.db.getProductVersionDefinition(hostname, version)
        return response.Response(self._fromProddef(pd))

    def update(self, request, hostname, version):
        pd = self._toProddef(request)
        self.db.setProductVersionDefinition(hostname, version, pd)
        return response.RedirectResponse(
                    self.url(request, 'products.versions.definition', 
                             hostname, version))

    def getImageDefinitions(self, request, hostname, version):
        pd = self.db.getProductVersionDefinition(hostname, version)
        buildTemplates = pd.platform.getBuildTemplates()
        buildDefModels = [ self._makeBuildDefinition(x, pd)
            for x in buildTemplates ]
        bdefs = models.BuildDefinitions(buildDefinitions = buildDefModels)
        return bdefs

    def _toProddef(self, request):
        from rpath_common.proddef import api1 as proddef
        return proddef.ProductDefinition(fromStream=request.read())

    def _fromProddef(self, pd):
        import cStringIO as StringIO
        sio = StringIO.StringIO()
        pd.serialize(sio)
        return sio.getvalue()


class ProductVersionController(base.BaseController):

    modelName = 'version'
    urls = {'platform'   : dict(GET='getPlatform',
                                PUT='setPlatform',
                                POST='updatePlatform'),
            'stages'     : ProductVersionStages,
            'definition' : ProductVersionDefinition,
            'images'     : dict(GET='getImages')}

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
        return response.RedirectResponse(
                           self.url(request, 'products.versions', 
                                    hostname, productVersion.name))

    def getImages(self, request, hostname, version):
        return self.db.getProductVersionImages(hostname, version)

    def getPlatform(self, request, hostname, version):
        return self.db.getProductVersionPlatform(hostname, version)

    @requires('platform', models.Platform)
    def setPlatform(self, request, hostname, version, platform):
        self.db.rebaseProductVersionPlatform(hostname, version, platform.label)
        return response.RedirectResponse(
                        self.url(request, 'products.versions.platform', 
                                 hostname, version))

    def updatePlatform(self, request, hostname, version):
        self.db.rebaseProductVersionPlatform(hostname, version)
        return response.RedirectResponse(
                        self.url(request, 'products.versions.platform', 
                                 hostname, version))



