#
# Copyright 2011 rPath, Inc.
#

import restlib.http.modpython

import crest.root
import crest.webhooks

from mint.rest.db import database as restDatabase
from mint.db import database
from mint.rest.middleware import auth


def handleCrest(prefix, cfg, db, repos, req, authToken):
    handler, callback = getCrestHandler(cfg, db, authToken)
    callback.repos = repos.repos
    return handler.handle(req, prefix)

def getCrestHandler(cfg, db, authToken):
    assert(cfg)
    assert(db)
    crestController = crest.root.Controller(None, '/rest')
    crestHandler = restlib.http.modpython.ModPythonHttpHandler(crestController)
    crestCallback = CrestRepositoryCallback(db)
    crestHandler.addCallback(crestCallback)
    db = database.Database(cfg, db)
    db = restDatabase.Database(cfg, db)
    auth = CrestAuthenticationCallback(cfg, db, crestController)
    auth.authToken = authToken
    crestHandler.addCallback(auth)
    return crestHandler, crestCallback


class CrestAuthenticationCallback(auth.AuthenticationCallback):
    authToken = None

    def processRequest(self, request):
        ret = auth.AuthenticationCallback.processRequest(self, request)
        request.authToken = self.authToken
        return ret


class CrestRepositoryCallback(crest.webhooks.ReposCallback):
    def __init__(self, db):
        self.db = db
        crest.webhooks.ReposCallback.__init__(self, None)

    def makeUrl(self, request, *args, **kwargs):
        if 'host' in kwargs:
            cu = self.db.cursor()
            fqdn = kwargs['host']
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



