from django import http
# from mint.django_rest.rbuilder.rbac.manager.rbacmanager import RbacManager as rbacMgr

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
        return self._callWrapper(fcn)

    
    def _callWrapper(self, fcn):
        # NOTE: _self == "self" of view method, not to be confused
        #       self in the signature of _callWrapper
        def callFcn(_self, request, *args, **kwargs):
            user = request.user
            resource = fcn(_self, request, *args, **kwargs)
            if _self.mgr.userHasRbacPermission(user, resource, fcn._action):
                return fcn
            else:
                return lambda s, r, *args, **kwargs: http.HttpResponse(status_code=fcn._failure_status_code)
        return callFcn