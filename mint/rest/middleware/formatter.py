#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from restlib import response

from mint.rest.modellib.xmlformatter import XMLFormatter

class FormatCallback(object):
    def __init__(self, controller):
        self.formatter = XMLFormatter(controller)

    def processMethod(self, request, viewMethod, args, kw):
        if hasattr(viewMethod, 'model'):
            modelName, model = viewMethod.model
            kw[modelName] = self.formatter.fromText(request, model, request.read())
        
    def processResponse(self, request, res):
        if not isinstance(res, response.Response):
            xml = self.formatter.toText(request, res)
            res =  response.Response(xml, content_type='text/xml')
        return res
