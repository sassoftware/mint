from conary.repository.netrepos import proxy

import restlib.http.modpython
from restlib import response

import crest.root
import crest.webhooks

from mint.rest.db import database as restDatabase
from mint.db import database
from mint.rest.middleware import auth


def handleCrest(prefix, cfg, db, repos, req):
    handler, callback = getCrestHandler(cfg, db)
    if isinstance(repos, proxy.CachingRepositoryServer):
        callback.repos = repos.repos
    else:
        callback.repos = repos
    return handler.handle(req, prefix)

def getCrestHandler(cfg, db):
    assert(cfg)
    assert(db)
    crestController = crest.root.Controller(None, '/rest')
    crestHandler = restlib.http.modpython.ModPythonHttpHandler(crestController)
    crestCallback = CrestRepositoryCallback(db)
    crestHandler.addCallback(crestCallback)
    db = database.Database(cfg, db)
    db = restDatabase.Database(cfg, db)
    crestHandler.addCallback(CrestAuthenticationCallback(cfg, db,
        crestController))
    return crestHandler, crestCallback


class CrestAuthenticationCallback(auth.AuthenticationCallback):
    def processMethod(self, request, viewMethod, args, kw):
        return self.checkDisablement(request, viewMethod)

class CrestRepositoryCallback(crest.webhooks.ReposCallback):
    def __init__(self, db):
        self.db = db
        crest.webhooks.ReposCallback.__init__(self, None)

    def makeUrl(self, request, *args, **kwargs):
        if 'host' in kwargs:
            cu = self.db.cursor()
            fqdn = kwargs['host']
            hostname = fqdn.split('.', 1)[0]
            cu.execute('''SELECT shortname FROM Projects
                          WHERE fqdn=?''', fqdn)
            try:
                shortName, = cu.next()
            except StopIteration:
                return 'http://%s/conary/api/%s' % (fqdn, '/'.join(args))
            else:
                rootUrl = '/'.join(request.baseUrl.split('/')[:3])
                reposUrl = rootUrl + '/repos/%s/api' % (shortName,)
                return request.url(baseUrl=reposUrl, *args)
        return request.url(*args)



