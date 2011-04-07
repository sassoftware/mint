#
# Copyright (c) 2011 rPath, Inc.
#

from conary.deps import deps
from rpath_proddef import api1 as proddef

class ProductDefinitionHelper(object):
    def __init__(self, productDefinition):
        self.proddef = productDefinition


    def getRmakeCfgLines(self, troveName, troveVersion):
        flavorPairs = self._getFlavorPairs(self.proddef)
        rmakeCfgLines, buildSpecs = self._getRmakeCfgLinesForFlavors(
            troveName, troveVersion, flavorPairs)
        return rmakeCfgLines, buildSpecs

    @classmethod
    def _updateConaryConfig(self, cfg, pDef, stageLabel):
        searchPath = [ dict(troveName = x.troveName, label = x.label)
                            for x in pDef.getResolveTroves() ]
        groupSearchPaths = [ '%s=%s' % x.getTroveTup()[:2]
                            for x in pDef.getGroupSearchPaths() ]
        cfg.configLine('macros productDefinitionSearchPath %s' %
            '\n'.join(groupSearchPaths))
        if not stageLabel:
            stage = pDef.getStages()[0]
            stageLabel = pDef.getLabelForStage(stage.name)

        pDefInfo = pDef.getPlatformInformation()
        isWindows = (pDefInfo and
            'windows' in pDefInfo.platformClassifier.tags)

        # XXX windows builds to be added here
        windowsBuildServiceDest = None

        cfg.configLine('buildLabel %s' % stageLabel)
        for item in pDef.getPlatformAutoLoadRecipes():
            cfg.configLine('autoLoadRecipes %s=%s' %
                (item.getTroveName(), item.getLabel()))
        if searchPath:
            sp = cfg.searchPath + [ "%s=%s" % (src['troveName'], src['label'])
                    for src in searchPath ]
            cfg.configLine('searchPath %s' % ' '.join(sp))

        if windowsBuildServiceDest:
            cfg.configLine('windowsBuildService %s' % windowsBuildServiceDest)
        if isWindows:
            cfg.configLine('macros targetos windows')
        return cfg

    @classmethod
    def _getFlavorPairs(cls, pDef):
        flavorPairs = set()
        for build in pDef.getBuildDefinitions():
            flavor = deps.parseFlavor(str(build.getBuildBaseFlavor()))
            buildFlavor = cls._filterBuildFlavor(flavor)

            if (flavor, buildFlavor) not in flavorPairs:
                flavorPairs.add((flavor, buildFlavor))

        return list(sorted(flavorPairs))

    @classmethod
    def _filterBuildFlavor(cls, flavor):
        biarch = deps.parseFlavor('is: x86 x86_64')
        if flavor.stronglySatisfies(biarch):
            # Get a new flavor before modifying it.
            flavor = flavor.copy()
            # Remove the x86 deps.
            flavor.removeDeps(deps.InstructionSetDependency,
                [deps.Dependency('x86'), ])
        return flavor

    @classmethod
    def _productDefinitionFromStream(cls, stream):
        return proddef.ProductDefinition(fromStream=stream)

    @classmethod
    def _getRmakeCfgLinesForFlavors(cls, troveName, troveVersion, flavorPairs):
        buildSpec = "%s=%s" % (troveName, troveVersion)

        rmakeCfgLines = []
        buildSpecs = []
        descriptions = deps.getShortFlavorDescriptors(
            [ x[1] for x in flavorPairs ])
        for flavor, buildFlavor in flavorPairs:
            contextName = descriptions[buildFlavor]
            rmakeCfgLines.append('[%s]' % contextName)
            rmakeCfgLines.append('flavor %s' % flavor)
            if troveName.startswith('group-'):
                rmakeCfgLines.append('buildFlavor %s' % flavor)
            else:
                rmakeCfgLines.append('buildFlavor %s' % buildFlavor)
            buildSpecs.append('%s{%s}' % (buildSpec, contextName))
        return rmakeCfgLines, buildSpecs


