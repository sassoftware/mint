#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder import service
from mint.django_rest.deco import return_xml


class ModuleHooksService(service.BaseService):
    @return_xml
    def rest_GET(self, request):
        return self.get()
        
    def get(self):
        return self.mgr.getModuleHooks()