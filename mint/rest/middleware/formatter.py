#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from restlib import response

from mint.rest.modellib import converter

class FormatCallback(object):
    def __init__(self, controller):
        self.controller = controller

    def processMethod(self, request, viewMethod, args, kw):
        if hasattr(viewMethod, 'model'):
            modelName, model = viewMethod.model
            kw[modelName] = converter.fromText('xml', request.read(),
                                               model, self.controller, request)
        
    def processResponse(self, request, res):
        if not isinstance(res, response.Response):
            xml = converter.toText('xml', res,
                                   self.controller, request)
            res = response.Response(xml, content_type='text/xml')
        return res
