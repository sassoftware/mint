#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

class BaseManager(object):
    def __init__(self, mgr):
        # mgr is a weakref to avoid circular references. Access its fields
        # through properties
        self.mgr = mgr

    @property
    def cfg(self):
        return self.mgr.cfg

    @property
    def rest_db(self):
        return self.mgr.rest_db

    @property
    def user(self):
        return self.mgr.user

def exposed(fn):
    fn.exposed = True
    return fn
