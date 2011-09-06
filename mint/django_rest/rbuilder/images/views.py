#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

# Services related to images

# from django.http import HttpResponse #, HttpResponseNotFound
from mint.django_rest.deco import return_xml, access #, requires
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.images import models

class BaseImageService(service.BaseService):
    pass

class ImagesService(BaseImageService):
    """
    URLs for discovery purposes
    """

    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return models.Images()

class ImageDefinitionDescriptorsService(BaseImageService):
    """
    Collection of valid descriptors.
    May be applicable descriptors or all of them (TBD).
    """

    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.mgr.getImageDescriptors()

class ImageDefinitionDescriptorService(BaseImageService):
    """
    Returns a particular image descriptor for a given
    image type
    """

    @access.anonymous
    @return_xml
    def rest_GET(self, request, image_descriptor_type):
        return self.mgr.getImageDescriptor(image_descriptor_type)


