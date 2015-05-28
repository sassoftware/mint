#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


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
