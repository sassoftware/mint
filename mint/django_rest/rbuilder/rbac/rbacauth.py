from mint.django_rest.deco import ACCESS
from mint.django_rest.rbuilder.errors import PermissionDenied

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

    action can be a callback also, in which case it MUST
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
            
        # NOTE: _self == "self" of view method, not to be confused
        #       self in the signature of _callWrapper
        def callFcn(_self, request, *args, **kwargs):

            # error checking and admin/bypass:
            #    why is this a list?
            user = _self.mgr.getSessionInfo().user[0]
            if fcn.ACCESS & ACCESS.ANONYMOUS:
                # this shouldn't ever happen due to outer decorator
                raise PermissionDenied()
            if fcn.ACCESS & ACCESS.ADMIN:
                # save some database access if the user is an admin
                return fcn(_self, request, *args, **kwargs)

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
        return callFcn


