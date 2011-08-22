from django import http
from mint.django_rest.rbuilder.rbac import manager as rbacMgr

class rbac(object):
    """
    Decorator that sets rbac roles.
    """
    def __init__(self, action, failure_status_code=403):
        self._action = action
        self._failure_status_code = failure_status_code
        
    def __call__(self, fcn):
        fcn._action  = self._action
        fcn._failure_status_code = self._failure_status_code
        fcn.__call__ = self._callWrapper(fcn)
    
    def _callWrapper(self, fcn):
        # NOTE: _self == "self" of view method, not to be confused
        #       self in the signature of _callWrapper
        def callFcn(_self, request, *args, **kwargs):
            user = request.user
            resource = fcn(_self, request, *args, **kwargs)
            # Check rbac perms for a given user on a resource
            if rbacMgr.userHasRbacPermission(user, resource, fcn._action):
                return resource
            return http.HttpResponse(status_code=fcn._failure_status_code)
        return callFcn