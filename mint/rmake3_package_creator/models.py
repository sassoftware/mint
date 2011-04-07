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

import StringIO
from conary import conarycfg
from rmake.build import buildcfg as rmakeBuildCfg

from rpath_repeater.models import _BaseSlotCompare, _Serializable, _SerializableListMixIn
from rpath_repeater.models import Trove #pyflakes=ignore

class ImmutableDict(_BaseSlotCompare):
    __slots = [ 'data', ]

    def __init__(self, d=None):
        if isinstance(d, dict):
            self.data = tuple(d.items())

    def getDict(self):
        return dict(self.data)

class ImmutableList(_BaseSlotCompare):
    __slots__ = [ 'data', ]
    def __init__(self, l):
        if isinstance(l, list):
            ret = []
            for item in l:
                if hasattr(item, 'freeze'):
                    item = item.freeze()
                ret.append(item)
            self.data = tuple(ret)

    def __iter__(self):
        for item in self.data:
            if hasattr(item, 'thaw'):
                item = item.thaw()
            yield item

class ConaryConfiguration(_BaseSlotCompare):
    __slots__ = [ 'data' ]

    Class = conarycfg.ConaryConfiguration

    @classmethod
    def fromConfigObject(cls, cfg):
        sio = StringIO.StringIO()
        cfg.store(sio, includeDocs=False)
        self = cls(data=sio.getvalue())
        return self

    def toConfigObject(self):
        obj = self.Class(readConfigFiles=False)
        for line in self.data.splitlines():
            obj.configLine(line)
        return obj

class RmakeConfiguration(ConaryConfiguration):
    Class = rmakeBuildCfg.BuildConfiguration

class MinimalConaryConfiguration(_BaseSlotCompare):
    __slots__ = [ 'lines' ]
    fields = ['name', 'contact',
              'repositoryMap', 'buildLabel', 'user',
              'installLabelPath', 'searchPath', 'entitlement', 'conaryProxy',
              'macros', 'autoLoadRecipes', 'windowsBuildService', ]

    @classmethod
    def fromConaryConfig(cls, cfg):
        obj = cls()
        lines = []
        sio = StringIO.StringIO()
        for key in obj.fields:
            if key not in cfg:
                continue
            if not cfg[key]:
                # list constructs always get displayed.
                # this block protects against things like repositoryMap []
                # however, contact must always be set, even to empty string.
                if key == 'contact':
                    lines.append(key)
                continue
            cfg.storeKey(key, out=sio)
            lines.extend(sio.getvalue().splitlines())
            sio.seek(0)
            sio.truncate()
        obj.lines = ImmutableList(lines)
        return obj

    def createConaryConfig(self):
        """
        Create a C{conarycfg.ConaryConfiguration} object
        @return: a Conary configuration object
        @rtype: C{conarycfg.ConaryConfiguration}
        """
        cfg = conarycfg.ConaryConfiguration(readConfigFiles = False)
        for line in self.lines:
            cfg.configLine(line)
        return cfg

class File(_BaseSlotCompare):
    """
    The representation of a file, needed for committing a source.
    If contents are not specified, the file from the specified path will be
    used.
    """
    __slots__ = [ 'name', 'path', 'contents', 'isConfig', ]

class ProductDefinitionLocation(_BaseSlotCompare):
    __slots__ = [ 'hostname', 'shortname', 'namespace', 'version' ]

class SourceData(_BaseSlotCompare):
    __slots__ = [ 'name', 'label', 'version', 'fileList', 'factory',
        'productDefinitionLocation', 'stageLabel', 'commitMessage', ]

class PackageSourceCommitParams(_BaseSlotCompare):
    __slots__ = [ 'mincfg', 'sourceData', 'resultsLocation', ]

class DownloadFile(_BaseSlotCompare):
    """
    Representation of a file to be downloaded.
    """
    __slots__ = [ 'url', 'path', ]

class DownloadFilesParams(_BaseSlotCompare):
    __slots__ = [ 'urlList', 'resultsLocation', ]

class Response(_BaseSlotCompare):
    __slots__ = [ 'data', ]

class PackageSource(_BaseSlotCompare, _Serializable):
    __slots__ = ( 'trove', 'built', )
    _tag = 'package_source'

class PackageBuild(_BaseSlotCompare, _Serializable):
    __slots__ = ( 'trove', )
    _tag = 'package_build'

class PackageBuilds(ImmutableList, _SerializableListMixIn):
    _tag = 'package_builds'

class PackageSourceBuildParams(_BaseSlotCompare):
    __slots__ = ( 'rmakeCfg', 'buildSpecs', 'resultsLocation', )
