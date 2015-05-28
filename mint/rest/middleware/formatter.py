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


import os
import time

profilers = {}
def get():
    return profilers.get(os.getpid(), None)

def trace(fn):
    def _traceWrapper(self, *args, **kw):
        profiler = get()
        if profiler:
            profiler.startTime(fn.func_name)
            try:
                rc = fn(self, *args, **kw)
            finally:
                profiler.stopTime(fn.func_name)
            return rc
        else:
            return fn(self, *args, **kw)
    return _traceWrapper


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
        profilers[os.getpid()] = request.profile
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
            # Save the body of the request
            # May need it to create a different model later on
            request.body = request.read()
            kw[modelName] = converter.fromText(request.responseType,
                                               request.body,
                                               model, self.controller, request)
        
    def processResponse(self, request, res):
        if not isinstance(res, response.Response):
            if res == None:
                return response.Response(status=200)
            request.profile.stopResponse()
            startConvert = time.time()
            text = converter.toText(request.responseType, res,
                                    self.controller, request)
            convertTime = time.time() - startConvert
            if False and request.contentType == 'text/plain':
                import gc
                class Results(modellib.Model):
                    profile = fields.ModelField(profile.ProfileData)
                    results = fields.ModelField(res.__class__,
                                                displayName=res._meta.name)
                request.profile.otherTimes.sort(key = lambda x: x.time)
                request.profile.convertTime = convertTime
                gc.collect()
                request.profile.references =  len(gc.get_objects())
                res = Results(profile=request.profile, 
                              results=res)
                text = converter.toText(request.responseType, res,
                                        self.controller, request)
            res = response.Response(text, content_type=request.contentType)
        res.headers['Cache-Control'] = 'private, must-revalidate, max-age=0'
        request.rootController.db.reset()
        return res
