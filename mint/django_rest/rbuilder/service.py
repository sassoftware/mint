#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import logging
import random
import time

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError, transaction
from django.http import HttpResponseNotAllowed, HttpResponseNotFound

from django_restapi import resource

from mint.db import database
from mint import users
from mint.django_rest.deco import getHeaderValue, access, ACCESS, HttpAuthenticationRequired, HttpAuthorizationRequired
from mint.django_rest.rbuilder.manager import rbuildermanager

MANAGER_CLASS = rbuildermanager.RbuilderManager
log = logging.getLogger(__name__)

def undefined(function):
    function.undefined = True
    return function

class BaseService(resource.Resource):

    MAX_RETRIES = 10
    RETRY_WAIT_TIME = 1

    def __init__(self):
        self.mgr = MANAGER_CLASS(cfg=None)
        permitted_methods = ['GET', 'PUT', 'POST', 'DELETE']
        resource.Resource.__init__(self, permitted_methods=permitted_methods)

    def __call__(self, request, *args, **kw):
        self.mgr = MANAGER_CLASS(cfg=getattr(request, 'cfg', None))
        self.setManagerAuth(request)

        retries = 0
        while True:
            try:
                return resource.Resource.__call__(self, request, *args, **kw)
            except DatabaseError as e:
                if 'deadlock' in e.args[0]:
                    retries += 1
                    random.seed(time.time())
                    wait = random.randint(1, retries)
                    log.warning(
                        'Deadlock detected, retry %s in %ss', retries, wait
                        )
                    time.sleep(wait)
                    if self.MAX_RETRIES <= retries:
                        raise
                    transaction.rollback()
                    transaction.set_clean()
                    continue
                raise

    def setManagerAuth(self, request):
        user_name, password = request._auth
        user = request._authUser
        if user_name and password and user:
            mintAuth = users.Authorization(user_name=user_name,
                token=(user_name, password), admin=request._is_admin,
                userId=user.user_id)
            self.mgr.setAuth(mintAuth, user)

    def read(self, request, *args, **kwargs):
        resp = None
        try:
            resp = self._auth(self.rest_GET, request, *args, **kwargs)
        except ObjectDoesNotExist:
            resp = HttpResponseNotFound()
        return resp

    def create(self, request, *args, **kwargs):
        return self._auth(self.rest_POST, request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return self._auth(self.rest_PUT, request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self._auth(self.rest_DELETE, request, *args, **kwargs)

    @classmethod
    def getHeaderValue(cls, *args, **kwargs):
        return getHeaderValue(*args, **kwargs)

    # Overwrite these functions when inheriting
    @undefined
    @access.anonymous
    def rest_GET(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(self._getPermittedMethods())

    @undefined
    @access.anonymous
    def rest_POST(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(self._getPermittedMethods())

    @undefined
    @access.anonymous
    def rest_PUT(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(self._getPermittedMethods())

    @undefined
    @access.anonymous
    def rest_DELETE(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(self._getPermittedMethods())


    @classmethod
    def _getPermittedMethods(cls):
        methods = [ 'GET', 'POST', 'PUT', 'DELETE' ]
        # Methods of this class are undefined
        return [ x for x in methods
            if not getattr(getattr(cls, 'rest_%s' % x), 'undefined', False) ]
        

    def _auth(self, method, request, *args, **kwargs):
        """
        Verify authentication and run the specified method
        """
        # By default, everything has to be authenticated
        access = getattr(method, 'ACCESS', ACCESS.AUTHENTICATED)
        # If authentication is present, but it's bad, simply give up, even if
        # we're allowing anonymous access
        if request._auth != (None, None) and not request._is_authenticated:
            return HttpAuthenticationRequired
        (authOk, errorResponse) = self._auth_filter(request, access, kwargs)
        if not authOk:
            return errorResponse
        # Set the manager into one of the model's base classes. It will be
        # freed in SerializeXmlMiddleware, which is the last place that might
        # need access to the attached database.
        from mint.django_rest.rbuilder import modellib
        modellib.XObjModel._rbmgr = self.mgr
        return method(request, *args, **kwargs)

    def _auth_filter(self, request, access, kwargs):
        """Return C{True} if the request passes authentication checks."""
        # Access flags are permissive -- if a function specifies more than one
        # method, the authentication is successful if any of those methods
        # succeed.

        if access & ACCESS.LOCALHOST:
            if self._check_localhost(request):
                return (True, None)

        if access & ACCESS.ADMIN:
            if not request._is_authenticated:
                return (False, HttpAuthenticationRequired)
            return (request._is_admin, HttpAuthorizationRequired)
        if access & ACCESS.AUTHENTICATED:
            return (request._is_authenticated, HttpAuthenticationRequired)
        if access & ACCESS.ANONYMOUS:
            return (True, None)

        # no decorator supplied for method 
        # should be a 500 internal error perhaps?
        return (False, HttpAuthorizationRequired)

    @classmethod
    def _check_localhost(cls, request):
        # Ignore requests that are forwarded through the repeater since
        # they are not trustworthy.
        headerName = 'X-rPath-Repeater'
        headerValue = cls.getHeaderValue(request, headerName)
        return (headerValue is None and request.META['REMOTE_ADDR'] in (
            '127.0.0.1', '::1', '::ffff:127.0.0.1'))

class BaseAuthService(BaseService):
    def _auth_filter(self, request, access, kwargs):
        """Return C{True} if the request passes authentication checks."""
        # Access flags are permissive -- if a function specifies more than one
        # method, the authentication is successful if any of those methods
        # succeed.

        if access & ACCESS.LOCALHOST:
            if self._check_localhost(request):
                return (True, None)

        if access & ACCESS.AUTH_TOKEN:
            ret = self._check_uuid_auth(request, kwargs)
            if ret is not None:
                # A bad event UUID should fail the auth check
                return (ret, HttpAuthenticationRequired)

        if access & ACCESS.ADMIN:
            if not request._is_authenticated:
                return (False, HttpAuthenticationRequired)
            return (request._is_admin, HttpAuthorizationRequired)
        if access & ACCESS.AUTHENTICATED:
            return (request._is_authenticated, HttpAuthenticationRequired)

        if access & ACCESS.ANONYMOUS:
            return (True, None)

        return (False, HttpAuthorizationRequired)

    def _check_uuid_auth(self, request, kwargs):
        return False

    def _setMintAuth(self, user=None):
        db = database.Database(self.mgr.cfg)
        if user is None:
            authToken = (self.mgr.cfg.authUser, self.mgr.cfg.authPass)
            cu = db.cursor()
            cu.execute("SELECT MIN(userId) FROM Users WHERE is_admin = ?", True)
            ret = cu.fetchall()
            userId = ret[0][0]
            isAdmin = True
        else:
            authToken = (user.user_name, "FAKE PASSWORD")
            userId = user.user_id
            isAdmin = bool(user.is_admin)
        userName = authToken[0]
        mintAuth = users.Authorization(username=userName,
            token=authToken, admin=isAdmin, userId=userId)
        self.mgr.setAuth(mintAuth, user)

