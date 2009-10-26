from django_restapi.responder import SerializeResponder
from xobj import xobj

class xobjResponder(SerializeResponder):
    """
    
    """
    def __init__(self, model_list = None, paginate_by=None, allow_empty=False):
        self.model_list = model_list
        SerializeResponder.__init__(self, 'xobj', 'text/plain',
                    paginate_by=paginate_by, allow_empty=allow_empty)
    
    def element(self, request, elem):
        self.request = request
        return SerializeResponder.element(self, request, elem)   
        
    def list(self, request, queryset, page=None):
        self.request = request
        return SerializeResponder.list(self, request, queryset, page)             
   
    def render(self, object_list):
        for obj in list(object_list):
            if getattr(obj, 'populateElements'):
                obj.populateElements(self.request)
        
        if self.model_list:
            self.model_list.addQueryset(object_list)
            obj = self.model_list
        
        response = xobj.toxml(obj, obj.__class__.__name__)
        
        return response
            