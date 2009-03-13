#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import time

from restlib import response

from mint.rest import modellib
from mint.rest.modellib import converter
from mint.rest.modellib import fields
from mint.rest.modellib import jsonconverter
from mint.rest.middleware import profile

contentTypes = {'application/json'        : 'json',
                'application/javascript'  : 'json',
                'application/xml'         : 'xml',
                'text/xml'                : 'xml',
                '*/*'                     : 'xml'}


class FormatCallback(object):
    def __init__(self, controller):
        self.controller = controller

    def processRequest(self, request):
        request.profile = profile.ProfileData()
        request.profile.startResponse()
        responseType = None
        extension = None
        accepted = request.headers.get('Accept', '').split(',')

        for acceptedLine in accepted:
            acceptedType = acceptedLine.split(';', 1)[0]
            if acceptedType == 'text/html':
                # likely a browser - use extensions for 
                # determining type.
                contentType = 'text/plain'
                if request.unparsedPath[-5:] == '.json':
                    responseType = 'json'
                    extension = '.json'
                    request.unparsedPath = request.unparsedPath[:-5]
                elif request.unparsedPath[-4:] == '.xml':
                    responseType = 'xml'
                    extension = '.xml'
                    request.unparsedPath = request.unparsedPath[:-4]
                else:
                    # default
                    responseType = 'xml'
                    contentType = 'text/plain'
                break
            else:
                # actual header.
                responseType = contentTypes.get(acceptedType, None)
                contentType = 'application/%s' % responseType
                if responseType:
                    break
        if not responseType:
            responseType = 'xml'
            contentType = 'text/plain'
        request.extension = extension
        request.responseType = responseType
        request.contentType = contentType

    def processMethod(self, request, viewMethod, args, kw):
        self.controller.db.setProfiler(request.profile)
        if hasattr(viewMethod, 'model'):
            modelName, model = viewMethod.model
            kw[modelName] = converter.fromText(request.responseType,
                                               request.read(),
                                               model, self.controller, request)
        
    def processResponse(self, request, res):
        if not isinstance(res, response.Response):
            request.profile.stopResponse()
                        
            startConvert = time.time()
            text = converter.toText(request.responseType, res,
                                    self.controller, request)
            convertTime = time.time() - startConvert
            if request.contentType == 'text/plain':
                class Results(modellib.Model):
                    profile = fields.ModelField(profile.ProfileData)
                    results = fields.ModelField(res.__class__,
                                                displayName=res._meta.name)
                request.profile.convertTime = convertTime
                res = Results(profile=request.profile, 
                              results=res)
                text = converter.toText(request.responseType, res,
                                        self.controller, request)
            res = response.Response(text, content_type=request.contentType)
        return res
