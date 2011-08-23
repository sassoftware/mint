from django.db import models
from mint.django_rest.deco import ACCESS

class rbac(object):
    """
    Decorator that sets rbac permissions required to access a resource.

    usage 
         @rbac('rmember')
         @access.authenticated

    In order to have access to authenticated bits, rbac must
    always be used with access.authenticated for now.

    FIXME -- factor that otu and make it do authenticated's lifting.

    rmember -- ability to read a data member
    wmember -- ability to modify or delete a data member
    rqueryset -- ability to see a queryset
    wqueryset -- ability to modify a queryset

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
            user = _self.mgr.getSessionInfo().user
            if fcn.ACCESS & ACCESS.ANONYMOUS:
                # this shouldn't ever happen due to outer decorator
                raise Exception('Impossible access control state')
            resource = fcn(_self, request, *args, **kwargs)
            if fcn.ACCESS & ACCESS.ADMIN:
                # save some database access if the user is an admin
                return resource
            if not isinstance(resource, models.Model):
                return Exception('rbac decorator must be closest to the method')
            if _self.mgr.userHasRbacPermission(user, resource, fcn._action, request):
                return resource
            else:
                raise Exception('Forbidden') # XXX Fixme
        # ensure access decorators are still called
        access = getattr(fcn, 'ACCESS', None)
        if access:
            callFcn.ACCESS = access
        return callFcn


