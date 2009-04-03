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
    crestCallback = CrestRepositoryCallback(db)
    crestHandler.addCallback(crestCallback)
    db = database.Database(cfg, db)
    db = restDatabase.Database(cfg, db)
    crestHandler.addCallback(auth.AuthenticationCallback(cfg, db))
    return crestHandler


class CrestRepositoryCallback(crest.webhooks.ReposCallback):
    def __init__(self, db):
        self.db = db
        crest.webhooks.ReposCallback.__init__(self, None)

    def makeUrl(self, request, *args, **kwargs):
        if 'host' in kwargs:
            cu = self.db.cursor()
            fqdn = kwargs['host']
            hostname = fqdn.split('.', 1)[0]
            cu.execute('''SELECT COUNT(*) FROM Projects
                          WHERE hostname=?''', hostname)
            if not cu.fetchall():
                return 'http://%s/%s' % (kwargs['host'], '/'.join(args))
            baseUrl = request.getHostWithProtocol() + '/repos/%s/api' % hostname
            return request.url(*args, baseUrl=baseUrl)
        return request.url(*args)



