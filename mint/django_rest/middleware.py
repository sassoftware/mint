from mint.django_rest import logger
from mint.django_rest.rbuilder import auth

from django.contrib.auth import authenticate
from django.http import HttpResponseBadRequest

class MethodRequestMiddleware:
    
    def process_request(self, request):
        # Was a '_method' directive in the query request
        if request.REQUEST.has_key('_method'):
            request_method = request.REQUEST['_method'].upper()
            allowable_methods = ['GET','POST','PUT','DELETE',]
                
            if request_method in allowable_methods:
                try:
                    request.method = request_method
                except AttributeError:
                    request.META['REQUEST_METHOD'] = request_method
            else:
                response = \
                    HttpResponseBadRequest('INVALID METHOD TYPE: %s' \
                    % request_method)
                return response
        # Mark the request as from an admin
        request._is_admin = False        
        username, password = auth.getAuth(request)
        if username:
            user = authenticate(username = username, password = password)
            request._is_admin = auth.isAdmin(user)
        return None

    def process_exception(self, request, exception):
        logger.exception(exception)
        return None