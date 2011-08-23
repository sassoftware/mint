from django.db import models
from mint.django_rest.deco import ACCESS

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
        retval = self._callWrapper(fcn)
        return retval

    def _callWrapper(self, fcn):
            
        # NOTE: _self == "self" of view method, not to be confused
        #       self in the signature of _callWrapper
        def callFcn(_self, request, *args, **kwargs):
            user = request.user
            if fcn.ACCESS & ACCESS.ANONYMOUS:
                raise Exception('Forbidden')
            resource = fcn(_self, request, *args, **kwargs)
            if fcn.ACCESS & ACCESS.ADMIN:
                return resource
            if not isinstance(resource, models.Model):
                return Exception('rbac decorator must be closest to the method')
            if _self.mgr.userHasRbacPermission(user, resource, fcn._action, request):
                return resource
            else:
                raise Exception('Forbidden') # XXX Fixme
        return callFcn