#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

from rmake3.core import types


class ImageJobData(types.SlotCompare):
    __slots__ = (
            'protocolVersion', 'type', 'buildId', 'name', 'troveName',
            'troveVersion', 'troveFlavor', 'description', 'buildType', 'data',
            'project', 'proddefLabel', 'proxy', 'pki', 'outputUrl',
            'outputToken',
            )

    @classmethod
    def fromDict(cls, values):
        out = cls()
        for key in cls.__slots__:
            setattr(out, key, values.get(key))
        return out


FrozenImageJobData = types.freezify(ImageJobData)
