#
# Copyright (c) 2010, 2011 rPath, Inc.
#
# All Rights Reserved
#

import os
import logging

from debug_toolbar import middleware

from django import http
from django.contrib.auth import authenticate
from django.contrib.redirects import middleware as redirectsmiddleware
from django.http import HttpResponse, HttpResponseBadRequest

import django.core.exceptions as core_exc 
from mint import config
from mint.django_rest import handler
from mint.django_rest.rbuilder import auth
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.metrics import models as metricsmodels
from mint.lib import mintutils

#from lxml import etree


try:
    # The mod_python version is more efficient, so try importing it first.
    from mod_python.util import parse_qsl # pyflakes=ignore
except ImportError:
    from cgi import parse_qsl # pyflakes=ignore

if parse_qsl is None:
    from cgi import parse_qsl

class BaseMiddleware(object):

    def process_request(self, request):
        try:
            return self._process_request(request)
        except Exception, e:
            return handler.handleException(request, e)

    def process_response(self, request, response):
        try:
            return self._process_response(request, response)
        except Exception, e:
            return handler.handleException(request, e)

    def _process_request(self, request):
        return None

    def _process_response(self, request, response):
        return response

class ExceptionLoggerMiddleware(BaseMiddleware):

    def process_request(self, request):
        mintutils.setupLogging(consoleLevel=logging.INFO,
                consoleFormat='apache')
        return None

    def process_exception(self, request, exception):

        if isinstance(exception, core_exc.ObjectDoesNotExist):
            fault = rbuildermodels.Fault(code=404, message=str(exception))
            response = HttpResponse(status=404, content_type='text/xml')
            response.content = fault.to_xml(request)
            return response

        return handler.handleException(request, exception)

class RequestSanitizationMiddleware(BaseMiddleware):
    def _process_request(self, request):
        # django will do bad things if the path doesn't end with / - it uses
        # urljoin which strips off the last component
        if not request.path.endswith('/'):
            request.path += '/'
        return None

class SetMethodRequestMiddleware(BaseMiddleware):
    
    def _process_request(self, request):
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
    
class SetMintAuthMiddleware(BaseMiddleware):
    """
    Set the authentication information on the request
    """
    def _process_request(self, request):
        request._auth = auth.getAuth(request)
        username, password = request._auth
        request._authUser = authenticate(username = username, password = password)
        return None

class SetMintAdminMiddleware(BaseMiddleware):
    """
    Set a flag on the request indicating whether or not the user is an admin
    """
    def _process_request(self, request):
        request._is_admin = auth.isAdmin(request._authUser)
        return None
    
class LocalSetMintAdminMiddleware(BaseMiddleware):
    def _process_request(self, request):
        request._is_admin = True
        request._is_authenticated = True
        request._authUser = rbuildermodels.Users.objects.get(pk=1)
        request._auth = ("admin", "admin")
        return None

class SetMintAuthenticatedMiddleware(BaseMiddleware):
    """
    Set a flag on the request indicating whether or not the user is authenticated
    """
    def _process_request(self, request):
        request._is_authenticated = auth.isAuthenticated(request._authUser)
        return None
       
class SetMintConfigMiddleware(BaseMiddleware):

    def _process_request(self, request):
        if hasattr(request, '_req'):
            cfgPath = request._req.get_options().get("rbuilderConfig", config.RBUILDER_CONFIG)
        else:
            cfgPath = config.RBUILDER_CONFIG
        cfg = config.getConfig(cfgPath)

        request.cfg = cfg

        return None

class LocalSetMintConfigMiddleware(BaseMiddleware):

    def _process_request(self, request):
        cfg = config.MintConfig()
        cfg.siteHost = 'localhost.localdomain'
        request.cfg = cfg


class AddCommentsMiddleware(BaseMiddleware):
    
    useXForm = True

    def _process_response(self, request, response):
        if self.useXForm and response.content and  \
            response.status_code in (200, 201, 206, 207):

            # get view + documentation
            view_name = request._view_func.__class__.__name__
            path = os.path.join(os.path.dirname(__file__), 'rbuilder/inventory/docs/%s.txt' % view_name)
            try:
                f = open(path, 'r')
            except IOError:
                return response
            try:
                contents = response.content.split('\n')
                docs = '<!--' + f.read().strip() + '-->'
                response.content = contents[0] + docs + '\n'.join(contents[1:])
            finally:
                f.close()
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        request._view_func = view_func
        return None

#class AddCommentsMiddleware(BaseMiddleware):
#    
#    useXForm = True
#    
#    def __init__(self):
#        try:
#            f = os.path.join(os.path.dirname(__file__), 'templates/comments.xsl')
#            self.styledoc = etree.parse(f)
#        except:
#            self.useXForm = False
#
#    def _process_response(self, request, response):
#        if self.useXForm and response.content and  \
#            response.status_code in (200, 201, 206, 207):
#
#            # get view + documentation
#            view = request._view_func
#            # Process view no longer exists, see generatecomments
#            # script for HOWTO reconstruct it
#            view_doc = processView(view)
#            
#            try:
#                transform = etree.XSLT(self.styledoc)
#                xmldoc = transform(etree.XML(response.content))
#                response.content = str(xmldoc).replace('@@METHODS@@', view_doc)
#            except:
#                pass
#
#        return response 
#
#    def process_view(self, request, view_func, view_args, view_kwargs):
#        request._view_func = view_func
#        return None


class NoParamsRequest(object):

    def __init__(self, request):
        self.request = request

    def get_full_path(self):
        return self.request.path

class RedirectMiddleware(BaseMiddleware, redirectsmiddleware.RedirectFallbackMiddleware):
    """
    Middleware that process redirects irregardless of any query parameters
    specified.  Overrides default django redirect middleware functionality.
    """
    def _process_response(self, request, response):
        nPRequest = NoParamsRequest(request)
        return redirectsmiddleware.RedirectFallbackMiddleware.process_response(self, nPRequest, response)


class LocalQueryParameterMiddleware(BaseMiddleware):

    def _process_request(self, request):
        if '?' in request.path:
            url, questionParams = request.path.split('?', 1)
            questionParams = parse_qsl(questionParams)
        else:
            questionParams = []
            url = request.path

        if ';' in url:
            request.path, semiColonParams = url.split(';', 1)
            request.path_info = request.path
            semiColonParams = parse_qsl(semiColonParams)
        else:
            semiColonParams = []

        qs = request.environ.get('QUERY_STRING', [])
        if qs:
            qs = parse_qsl(qs)
        else:
            qs = []

        params = questionParams + semiColonParams + qs
        request.params = ['%s=%s' % (k, v) for k, v in params]
        request.params = ';' + ';'.join(request.params)
        method = request.GET.get('_method', None)
        if method:
            request.params += ';_method=%s' % method
        request.GET = http.QueryDict(request.params)

class PerformanceMiddleware(BaseMiddleware, middleware.DebugToolbarMiddleware):

    def _process_request(self, request):
        metrics = request.GET.get('metrics', None)
        if metrics:
            middleware.DebugToolbarMiddleware.process_request(self, request)

    def _process_response(self, request, response):
        metrics = request.GET.get('metrics', None)
        if not metrics:
            return response

        debugToolbar = self.debug_toolbars.get(request, None)
        if debugToolbar:
            response = middleware.DebugToolbarMiddleware.process_response(
                self, request, response)

            metricsModel = metricsmodels.Metrics()

            for panel in debugToolbar.panels:
                if hasattr(panel, 'get_context'):
                    model = metricsmodels.panelModels[panel.__class__]
                    modelInst = model(panel.get_context())
                    tag = getattr(model._xobj, 'tag', model.__class__.__name__)
                    setattr(metricsModel, tag, modelInst)

            xobj_model = response.model.serialize(request)
            xobj_model.metrics = metricsModel.serialize(request)
            response.content = ''
            response.write(response.model.to_xml(request, xobj_model))

            return response
        else:
            if hasattr(response, 'model'):
                response.write(response.model.to_xml(request))
            return response


class SerializeXmlMiddleware(BaseMiddleware):
    def _process_response(self, request, response):
        if hasattr(response, 'model'):
            metrics = request.GET.get('metrics', None)
            if metrics:
                return response

            response.write(response.model.to_xml(request))

        return response
        
