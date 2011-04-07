#
# Copyright (c) 2011 rPath, Inc.
#

import StringIO
import sys

from conary import conaryclient
from conary import versions
from rmake import plugins as rmakePlugins
from rmake.build import buildcfg as rmakeBuildCfg

from mint.rmake3_package_creator import proddef
from mint.rmake3_package_creator import models

class RmakeConfiguration(object):
    class BuildConfiguration(object):
        __slots__ = ('rmakeCfg', 'buildSpecs', )
        def __init__(self, rmakeCfg=None, buildSpecs=None):
            self.rmakeCfg = rmakeCfg
            self.buildSpecs = buildSpecs

        def toPackageSourceBuildParams(self):
            sio = StringIO.StringIO()
            self.rmakeCfg.store(sio, includeDocs=False)
            ret = models.PackageSourceBuildParams()
            ret.rmakeCfg = sio.getvalue()
            ret.buildSpecs = models.ImmutableList(self.buildSpecs)
            return ret

    def __init__(self, authToken, conaryCfg, pDef):
        self.authToken = authToken
        self.proddef = pDef
        self.conaryCfg = conaryCfg

    @classmethod
    def loadFromString(cls, rmakeCfgData):
        cfg = rmakeBuildCfg.BuildConfiguration(readConfigFiles=False,
            ignoreErrors=True)
        for line in rmakeCfgData.splitlines():
            cfg.configLine(line)
        return cfg

    def getBuildConfiguration(self, troveName, troveVersion):
        pdh = proddef.ProductDefinitionHelper(self.proddef)
        self.loadPlugins()
        rmakeCfgLines, buildSpecs = pdh.getRmakeCfgLines(troveName,
            troveVersion)
        rmakeCfg = self._buildRmakeConfiguration(self.conaryCfg,
            rmakeCfgLines, self.authToken)
        return self.BuildConfiguration(rmakeCfg=rmakeCfg, buildSpecs=buildSpecs)

    @classmethod
    def getPluginManager(cls):
        if not hasattr(sys, 'argv'):
            sys.argv = []
        cfg = rmakeBuildCfg.BuildConfiguration(True, ignoreErrors = True)
        return cls._getPluginManager(cfg)

    loadPlugins = getPluginManager

    @classmethod
    def _getPluginManager(cls, buildCfg):
        if not buildCfg.usePlugins:
            return rmakePlugins.PluginManager([])
        pluginmgr = rmakePlugins.getPluginManager([], rmakeBuildCfg.BuildConfiguration)
        pluginmgr.loadPlugins()
        pluginmgr.callClientHook('client_preInit', DummyMain(), [])
        return pluginmgr


    @classmethod
    def _buildRmakeConfiguration(cls, conaryCfg, rmakeCfgLines, authToken,
            root=None):
        assert(conaryCfg.buildLabel)

        # XXX we want to use searchPath, but rMake doesn't handle that yet.
        searchPath = conaryCfg.searchPath[:]
        conaryCfg.searchPath = []

        installLabelList = [ 'installLabelPath' ]
        installLabelList.extend(conaryCfg.installLabelPath)
        installLabelList.extend(x for x in searchPath if '=' not in x)
        installLabelList.extend(str(cls.labelFromTroveSpec(x))
            for x in searchPath if '=' in x)
        conaryCfg.configLine(' '.join(installLabelList))
        conaryCfg.configLine("shortenGroupFlavors True")

        # Base the rMake configuration object on the Conary one
        buildConfig = rmakeBuildCfg.BuildConfiguration(
                readConfigFiles = True,
                conaryConfig = conaryCfg,
                root = root or '',
                ignoreErrors = True)
        # Just need to load the plugins
        cls._getPluginManager(buildConfig)

        if not buildConfig['rmakeUser'] and authToken:
            buildConfig['rmakeUser'] = authToken

        # We need to reset resolveTroves, we don't need rmake's defaults
        # XXX this is also an artifact of rMake not handling searchPath
        buildConfig.configLine("resolveTroves []")
        buildConfig.configLine("resolveTroves " +
            " ".join(x for x in searchPath if '=' in x))

        for line in rmakeCfgLines:
            buildConfig.configLine(line)

        # Overwrite buildLabel from the Conary configuration
        buildConfig.configLine('buildLabel %s' % conaryCfg.buildLabel)
        return buildConfig

    @classmethod
    def labelFromTroveSpec(cls, troveSpec):
        n, versionSpec, f = conaryclient.cmdline.parseTroveSpec(troveSpec)
        return cls.labelFromVersionSpec(versionSpec)

    @classmethod
    def labelFromVersionSpec(cls, versionSpec):
        if not versionSpec:
            return None
        if versionSpec.startswith('/'):
            vfs = versions.VersionFromString(versionSpec)
            if hasattr(vfs, 'trailingLabel'):
                return vfs.trailingLabel()
            return vfs.label()
        # Not a branch specification
        versionSpec = versionSpec.split('/', 1)[0]
        return versions.Label(versionSpec)

class DummyMain:
    # We need this class for loading the rMake plugins properly
    def _registerCommand(self, *args, **kwargs):
        pass

