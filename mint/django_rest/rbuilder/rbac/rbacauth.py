from mint.django_rest.deco import ACCESS
from mint.django_rest.rbuilder.errors import PermissionDenied

def manual_rbac(*args, **kwargs):
    """
    For marking methods with a manual rbac.  Use as follows:
    
    @rbac(manual)
    ...
    def rest_GET(self, request, ...):
        pass
    """
    return True

class rbac(object):
    """
    Decorator that sets rbac permissions required to access a resource.

    usage 
         @rbac(permission_constant) # from rbacmanager.py
         OR @rbac(custom_callback_returns_boolean_access_ok)

    if action is a callback also, in which case it MUST
    use self.mgr.userHasRbacPermission to implement itself

    """
    def __init__(self, action):
        # TODO: check type of action and use as callback if it's callable
        self._action = action
 
    def __call__(self, fcn):
        fcn._action  = self._action
        retval = self._callWrapper(fcn)
        return retval

    def _callWrapper(self, fcn):
        # inlining @access.authenticated from deco.py
        fcn.ACCESS = getattr(fcn, 'ACCESS', 0) | ACCESS.AUTHENTICATED
        # NOTE: _self == "self" of view method, not to be confused
        #       self in the signature of _callWrapper
        def callFcn(_self, request, *args, **kwargs):
            # error checking and admin/bypass:
            #    why is this a list?
            user = request._authUser
            if fcn.ACCESS is None:
                raise Exception("@access.authenticated missing in conjunction with @rbac?")
            if fcn.ACCESS & ACCESS.ANONYMOUS:
                # this shouldn't ever happen due to outer decorator
                raise PermissionDenied()
            if fcn.ACCESS & ACCESS.ADMIN:
                # save some database access if the user is an admin
                raise Exception("can't use rbac with ACCESS.ADMIN")

            # determine the rbac result based on the return of the function
            # unless an "allowed callback" is provided, in which case call
            # that function.  It is assumed this function ALWAYS
            # will call userHasRbacPermission internally.

            if not callable(fcn._action):
                # depends on the resource
                resource = fcn(_self, request, *args, **kwargs)
                allowed = _self.mgr.userHasRbacPermission(user, resource, 
                    fcn._action, request)
                if allowed:
                    return resource
                else:
                    raise PermissionDenied()
            else:
                # call check function first, then get resource
                allowed = fcn._action(_self, request, *args, **kwargs)
                if allowed:
                    return fcn(_self, request, *args, **kwargs)
                else:
                    raise PermissionDenied()

        # ensure access decorators are still called
        access = getattr(fcn, 'ACCESS', None)
        if access:
            callFcn.ACCESS = access
        # setting RBAC flag on fcn helps build time comment generation to
        # correctly determine which type of authentication is being used
        callFcn.RBAC = True
        return callFcn


