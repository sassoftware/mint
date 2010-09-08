#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import logging
from django.contrib.auth import authenticate
from django.http import HttpResponseBadRequest

import libxml2
import libxslt

from mint import config
from mint.django_rest.rbuilder import auth
from mint.lib import mintutils

log = logging.getLogger(__name__)


class ExceptionLoggerMiddleware(object):

    def process_request(self, request):
        mintutils.setupLogging(consoleLevel=logging.INFO,
                consoleFormat='apache')
        return None

    def process_exception(self, request, exception):
        log.exception("Unhandled error in django handler:\n")
        return None

class SetMethodRequestMiddleware(object):
    
    def process_request(self, request):
        # Was a '_method' directive in the query request
        if request.REQUEST.has_key('_method'):
            request_method = request.REQUEST['_method'].upper()
            allowable_methods = ['GET','POST','PUT','DELETE',]
                
            if request_method in allowable_methods:
                try:
                    request.method = request_method
                except AttributeError:
                    request.META['REQUEST_METHOD'] = request_method
            else:
                response = \
                    HttpResponseBadRequest('INVALID METHOD TYPE: %s' \
                    % request_method)
                return response

        return None
    
class SetMintAuthMiddleware(object):
    """
    Set the authentication information on the request
    """
    def process_request(self, request):
        request._auth = auth.getAuth(request)
        username, password = request._auth
        request._authUser = authenticate(username = username, password = password)
        return None

class SetMintAdminMiddleware(object):
    """
    Set a flag on the request indicating whether or not the user is an admin
    """
    def process_request(self, request):
        request._is_admin = False
        request._is_admin = auth.isAdmin(request._authUser)
        return None
    
class SetMintAuthenticatedMiddleware(object):
    """
    Set a flag on the request indicating whether or not the user is authenticated
    """
    def process_request(self, request):
        request._is_authenticated = False
        request._is_authenticated = auth.isAuthenticated(request._authUser)
        return None
       
class SetMintConfigMiddleware(object):

    def process_request(self, request):
        if hasattr(request, '_req'):
            cfgPath = request._req.get_options().get("rbuilderConfig", config.RBUILDER_CONFIG)
            cfg = config.getConfig(cfgPath)
            request.cfg = cfg

        return None

class AddCommentsMiddleware(object):
   
    useXForm = True
    
    def __init__(self):
        try:
            styledoc = libxml2.parseFile(__file__[0:__file__.index('.py')].replace(
                    'middleware', 'templates/comments.xsl'))
            self.style = libxslt.parseStylesheetDoc(styledoc)
        except libxml2.parserError:
            self.useXForm = False 

    def process_response(self, request, response):

        if self.useXForm and response.content and  \
            response.status_code in (200, 201, 206, 207):

            try: 
                xmldoc = libxml2.parseDoc(response.content)
                result = self.style.applyStylesheet(xmldoc, None)
                response.content = result.serialize()
                xmldoc.freeDoc()
                result.freeDoc()
            except:
                pass

        return response 

