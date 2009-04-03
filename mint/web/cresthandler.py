from conary.repository.netrepos import proxy

import restlib.http.modpython
from restlib import response

import crest.root
import crest.webhooks

from mint.rest.db import database as restDatabase
from mint.db import database
from mint.rest.middleware import auth

crestHandler = None
crestCallback = None

def handleCrest(uri, cfg, db, repos, req):
    handler = getCrestHandler(cfg, db)
    if isinstance(repos, proxy.SimpleRepositoryFilter):
        crestCallback.repos = repos.repos
    else:
        crestCallback.repos = repos
    return crestHandler.handle(req, uri)

def getCrestHandler(cfg, db):
    assert(cfg)
    assert(db)
    global crestHandler
    global crestCallback
    if crestHandler is not None:
        return crestHandler
    crestController = crest.root.Controller(None, '/rest')
    crestHandler = restlib.http.modpython.ModPythonHttpHandler(crestController)
    crestCallback = CrestRepositoryCallback()
    crestHandler.addCallback(crestCallback)
    db = database.Database(cfg, db)
    db = restDatabase.Database(cfg, db)
    crestHandler.addCallback(auth.AuthenticationCallback(cfg, db))
    return crestHandler

class CrestRepositoryCallback(object):
    def processMethod(self, request, method, args, kwargs):
        cu = self.repos.db.cursor()
        kwargs['repos'] = self.repos
        kwargs['roleIds'] = self.repos.auth.getAuthRoles(
                                    cu, request.auth + (None, None))
        kwargs['cu'] = cu
        if not kwargs['roleIds']:
            return response.Response(status=403)

