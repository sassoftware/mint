from restlib.controller import RestController

class BaseController(RestController):
    def __init__(self, parent, path, cfg, db):
        self.cfg = cfg
        self.db = db
        RestController.__init__(self, parent, path, [cfg, db])
