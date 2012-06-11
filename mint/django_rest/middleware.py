#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import logging
import sys
import traceback

import libxml2
import libxslt

from django.contrib.auth import authenticate
from django.contrib.redirects import middleware as redirectsmiddleware
from django.http import HttpResponseBadRequest, HttpResponse

from mint import config
from mint import logerror
from mint import mint_error
from mint.django_rest.rbuilder import auth
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import models
from mint.lib import mintutils

log = logging.getLogger(__name__)

class ExceptionLoggerMiddleware(object):

    def process_request(self, request):
        mintutils.setupLogging(consoleLevel=logging.INFO,
                consoleFormat='apache')
        return None

    def process_exception(self, request, exception):
        ei = sys.exc_info()
        tb = ''.join(traceback.format_tb(ei[2]))
        msg = str(ei[1])
        self.logError(request, ei[0], ei[1], ei[2])

        code = getattr(ei[1], 'status', 500)
        fault = models.Fault(code=code, message=msg, traceback=tb)
        response = HttpResponse(status=code, content_type='text/xml')
        response.content = fault.to_xml(request)

        return response

    def logError(self, request, e_type, e_value, e_tb, doEmail=True):
        info = {
                'path'              : request.path,
                'method'            : request.method,
                'headers_in'        : request.META,
                'request_params'    : request.GET,
                'is_secure'         : request.is_secure,
                }
        if request.raw_post_data:
            info.update(raw_post_data = request.raw_post_data)
        try:
            logerror.logErrorAndEmail(request.cfg, e_type, e_value,
                    e_tb, 'API call (django handler)', info, doEmail=doEmail)
        except mint_error.MailError, err:
            log.error("Error sending mail: %s", str(err))


class RequestSanitizationMiddleware(object):
    def process_request(self, request):
        # django will do bad things if the path doesn't end with / - it uses
        # urljoin which strips off the last component
        if not request.path.endswith('/'):
            request.path += '/'
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
        request._is_admin = auth.isAdmin(request._authUser)
        return None
    
class LocalSetMintAdminMiddleware(object):
    def process_request(self, request):
        request._is_admin = True
        request._is_authenticated = True
        request._authUser = rbuildermodels.Users.objects.get(pk=1)
        request._auth = ("admin", "admin")
        return None

class SetMintAuthenticatedMiddleware(object):
    """
    Set a flag on the request indicating whether or not the user is authenticated
    """
    def process_request(self, request):
        request._is_authenticated = auth.isAuthenticated(request._authUser)
        return None
       
class SetMintConfigMiddleware(object):

    def process_request(self, request):
        if hasattr(request, '_req'):
            cfgPath = request._req.get_options().get("rbuilderConfig", config.RBUILDER_CONFIG)
        else:
            cfgPath = config.RBUILDER_CONFIG
        cfg = config.getConfig(cfgPath)

        request.cfg = cfg

        return None

class SetMintConfigLocalMiddleware(object):

    def process_request(self, request):
        cfg = config.MintConfig()
        cfg.siteHost = 'localhost.localdomain'
        request.cfg = cfg

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

class NoParamsRequest(object):

    def __init__(self, request):
        self.request = request

    def get_full_path(self):
        return self.request.path

class RedirectMiddleware(redirectsmiddleware.RedirectFallbackMiddleware):
    def process_response(self, request, response):
        nPRequest = NoParamsRequest(request)
        return redirectsmiddleware.RedirectFallbackMiddleware.process_response(self, nPRequest, response)

