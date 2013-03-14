#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder.modellib import basemodels

class ImageTypeManagerException(Exception):
    pass
    
class UnsupportedFilterArgumentsException(ImageTypeManagerException):
    pass

class ImageTypeManager(basemodels.BaseManager):
    def all(self):
        # if import not inlined here then circular dependency is created
        from mint.django_rest.rbuilder.images import models as imagesmodels
        model = self.model
        imageTypeKeys = model.ImageTypeKeys.keys()
        retval = [model.fromImageTypeId(image_type_id) for image_type_id in imageTypeKeys]
        ImageTypes = imagesmodels.ImageTypes()
        ImageTypes.image_type = retval
        return ImageTypes
        
    def get(self, *args, **kwargs):
        pk, image_type_id = kwargs.get('pk', None), kwargs.get('image_type_id', None)
        if not pk and not image_type_id:
            raise UnsupportedFilterArgumentsException('can only search by image_type_id, or pk')
        pk = int(pk if pk else image_type_id) # django casts everything to unicode, so cast back
        return self.model.fromImageTypeId(pk)

class ImageMetadataManager(basemodels.BaseManager):
    def load_from_object(self, etreeModel, request, flags=None):
        model = self.model()
        model._imageMetadata = metadata = {}
        for node in etreeModel.iterchildren():
            metadata[node.tag] = node.text
        return model
