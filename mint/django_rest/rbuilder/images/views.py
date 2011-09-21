#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

# Services related to images -- expect heavy changes
# as target service evolves

#from django.http import HttpResponse 
from mint.django_rest.deco import requires, return_xml, access #, requires
from mint.django_rest.rbuilder import service
#from mint.django_rest.rbuilder.images import models

class BaseImageService(service.BaseService):
    pass

class ImagesService(BaseImageService):

    # leaving as admin until we can determine RBAC policy
    # and create an "All Images" queryset
    @access.admin
    @return_xml
    def rest_GET(self, request):
        # unified images are the
        # images on the targets + images we can deploy
        return self.mgr.getUnifiedImages()

class ImageService(BaseImageService):

    @access.admin
    @return_xml
    def rest_GET(self, request, image_id):
        return self.mgr.getUnifiedImage(image_id)
        
    @access.admin
    @requires('image')
    @return_xml
    def rest_PUT(self, request, image_id, image):
        return self.mgr.updateUnifiedImage(image_id, image)

