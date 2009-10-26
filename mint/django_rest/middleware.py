from django_restapi.resource import HttpMethodNotAllowed

class MethodRequestMiddleware:
    
    def process_request(self, request):
        # Was a '_method' directive in the query request
        
        if request.REQUEST.has_key('_method'):
            request_method = request.REQUEST['_method'].upper()
            allowable_methods = ['GET','POST','PUT','DELETE',]
                
            if request_method in allowable_methods:
                request.method = request_method
            else:
                raise HttpMethodNotAllowed
                
        return None