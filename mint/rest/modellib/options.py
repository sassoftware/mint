#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

class Options(object):
    def __init__(self, cls, meta):
        className = cls.__name__
        name = className[0].lower()  + className[1:]
        self.name = getattr(meta, 'name', name)
