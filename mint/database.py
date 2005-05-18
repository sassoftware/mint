#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

class TableObject:
    __slots__ = ['server', 'id']

    def getItem(self, id):
        raise NotImplementedError

    def __init__(self, server, id):
        self.id = id
        self.server = server
        self.refresh()

    def refresh(self):
        data = self.getItem(self.id)
        self.__dict__.update(data)

    def getId(self):
        return self.id
