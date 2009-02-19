from restlib.controller import RestController
from mint.rest.modellib import xmlformatter

class BaseController(RestController):
    def __init__(self, parent, path, cfg, db):
        self.cfg = cfg
        self.db = db
        RestController.__init__(self, parent, path, [cfg, db])
