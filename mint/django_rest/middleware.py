#
# Copyright (c) 2011 rPath, Inc.
#

import os
import logging
import traceback
import time
import textwrap

from debug_toolbar import middleware

from django import http
from django.contrib.auth import authenticate
from django.contrib.redirects import middleware as redirectsmiddleware
from django.http import HttpResponse, HttpResponseBadRequest
from django.db.utils import IntegrityError
from django.db import connection
import django.core.exceptions as core_exc

from mint import config
from mint.django_rest import handler
from mint.django_rest.rbuilder import auth, errors, models
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder.metrics import models as metricsmodels
from mint.django_rest.rbuilder.errors import PermissionDenied
from mint.lib import mintutils

log = logging.getLogger(__name__)

try:
    # The mod_python version is more efficient, so try importing it first.
    from mod_python.util import parse_qsl # pyflakes=ignore
except ImportError:
    from cgi import parse_qsl # pyflakes=ignore

if parse_qsl is None:
    from cgi import parse_qsl
        
RBUILDER_DEBUG_SWITCHFILE = "/srv/rbuilder/MINT_LOGGING_ENABLE"
RBUILDER_DEBUG_LOGPATH    = "/tmp/rbuilder_debug_logging/"
RBUILDER_DEBUG_HISTORY    = "/tmp/rbuilder_debug_logging/history.log"

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

    def isLocalServer(self, request):
        return not hasattr(request, '_req')

class SwitchableLogMiddleware(BaseMiddleware):
    ''' base class for Request and Response LogMiddleware '''
 
    def shouldLog(self):
        ''' dictates whether the middlware should log or not '''
        # create the switchfile and keep it newer than 1 hour to keep it logging
        if not os.path.exists(RBUILDER_DEBUG_SWITCHFILE):
            return False
        if not os.path.exists(RBUILDER_DEBUG_LOGPATH):
            return False
        if not os.access(RBUILDER_DEBUG_LOGPATH, os.W_OK):
            return False
        mtime = os.path.getmtime(RBUILDER_DEBUG_SWITCHFILE)
        delta = time.time() - mtime
        return delta < (60*60)

    def _getLogFilePath(self, localtime):
        ''' keeps directories neat and organized '''

        if not os.path.exists(RBUILDER_DEBUG_LOGPATH):
            os.makedirs(RBUILDER_DEBUG_LOGPATH, mode=0600)

        (year, month, mday, hour, min, sec, wday, yday, is_dst) = localtime
        ymd = "%d-%02d-%02d" % (year, month, mday)
        hour = "%02d" % hour
 
        filePath = os.path.join(RBUILDER_DEBUG_LOGPATH, ymd, hour)
        if not os.path.exists(filePath):
            os.makedirs(filePath)

        return (filePath, min, sec)

    def getLogFile(self, isRequest, localtime, type="full"):
        ''' returns log file and path for storing XML debug info'''
 
        filename = None
        (path, min, sec)  = self._getLogFilePath(localtime)
        minsec = "%02dm-%02ds" % (min, sec)
        counter = 0
        while True:
            if isRequest:
                filename = os.path.join(path, "%s-%s.request_%s.log" % (minsec, counter, type))
            else:
                filename = os.path.join(path, "%s-%s.response_%s.log" % (minsec, counter, type))
            counter += 1   
            if not os.path.exists(filename):
                return (open(filename, "a"), filename)

    def logPrint(self, handle, vars_dicts):
        wrap = textwrap.TextWrapper(width=80, subsequent_indent=' ', break_long_words=False, replace_whitespace=False)
        for vars_dict in vars_dicts:
            for k in sorted(vars_dict.keys()):
                v = vars_dict[k]
                if type(v) == list:
                    # just in case...
                    v = " ".join([ str(x) for x in v ])
                else:
                    v = str(v)
                v = "\n     ".join(wrap.wrap(v))
                handle.write("%s: %s\n" % (k, v))

class RequestLogMiddleware(SwitchableLogMiddleware):
    ''' 
    When sentinel file is present, log request traffic...
    '''

    def _logRequest(self, request):

        now = time.localtime()
        nowstr =time.asctime(now)
        urlsFile = RBUILDER_DEBUG_HISTORY
        urlsFile = open(RBUILDER_DEBUG_HISTORY, "a")
        (logFile, logFilePath) = self.getLogFile(True, now)
        path = "%s %s%s" % (
            request.META.get('REQUEST_METHOD'), 
            request.META.get('PATH_INFO'), 
            request.META.get('QUERY_STRING')
        )
        urlsFile.write("[%s]\n     %s\n     %s\n" % (nowstr, path, logFilePath))
        urlsFile.close()
        with logFile as f:
            self.logPrint(f, [ request.META, dict(zzz_raw_post_data=request.raw_post_data) ])


    def _process_request(self, request):
        if self.shouldLog():
            self._logRequest(request)
        return None

class ExceptionLoggerMiddleware(BaseMiddleware):

    def process_request(self, request):
        mintutils.setupLogging(consoleLevel=logging.INFO,
                consoleFormat='apache')
        return None

    def process_exception(self, request, exception):

        if isinstance(exception, PermissionDenied):
            # TODO: factor out duplication 
            code = 403
            fault = models.Fault(code=code, message=str(exception))
            response = HttpResponse(status=code, content_type='text/xml')
            response.content = fault.to_xml(request)
            log.error(str(exception))
            return response

        if isinstance(exception, core_exc.ObjectDoesNotExist):
            # django not found in a get/delete is usually a bad URL
            # in a PUT/POST, it's usually trying to insert or 
            # mangle something in a way that does not align with the DB
            code=404
            if request.method not in [ 'GET', 'DELETE' ]:
                code = 400
 
            # log full details, but don't present to user, in case
            # XML submitted was rather confusing and we can't tell what
            # was not found on the lookup, which could happen
            # anywhere in the call chain
            log.error(traceback.format_exc())

            fault = models.Fault(code=code, message=str(exception))
            response = HttpResponse(status=code, content_type='text/xml')
            response.content = fault.to_xml(request)
            log.error(str(exception))
            return response

        if isinstance(exception, errors.RbuilderError):
            tbStr = getattr(exception, 'traceback', None)
            status = getattr(exception.__class__, 'status', 500)
            fault = models.Fault(code=status, message=str(exception), traceback=tbStr)
            response = HttpResponse(status=status, content_type='text/xml')
            response.content = fault.to_xml(request)
            log.error(str(exception))
            return response

        if isinstance(exception, IntegrityError):
            # IntegrityError is a bug but right now we're using it as a crutch
            # to not send tracebacks when there's an uncaught conflict.
            return handler.handleException(request, exception,
                    doTraceback=False, doEmail=False)

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
        request._authUser = authenticate(username=username, password=password,
                mintConfig=request.cfg)
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
        request._authUser = usersmodels.User.objects.get(pk=1)
        request._auth = ("admin", "admin")

class SetMintAuthenticatedMiddleware(BaseMiddleware):
    """
    Set a flag on the request indicating whether or not the user is authenticated
    """
    def _process_request(self, request):
        request._is_authenticated = auth.isAuthenticated(request._authUser)
        return None
       
class SetMintConfigMiddleware(BaseMiddleware):

    def _process_request(self, request):
        if not self.isLocalServer(request):
            cfgPath = request._req.get_options().get("rbuilderConfig", config.RBUILDER_CONFIG)
        else:
            cfgPath = config.RBUILDER_CONFIG

        cfg = config.getConfig(cfgPath)
        request.cfg = cfg

        return None

class AddCommentsMiddleware(BaseMiddleware):
    
    useXForm = True

    def _process_response(self, request, response):

        # do not add comments to error messages
        if response.status_code != 200:
            return response

        if self.useXForm and response.content and  \
            response.status_code in (200, 201, 206, 207):

            # get view + documentation
            viewFunc = request._view_func
            view_name = viewFunc.__class__.__name__
            appName = self._getAppNameFromViewFunc(viewFunc)
            path = os.path.join(os.path.dirname(__file__),
                'rbuilder/docs/%s/%s.txt' % (appName, view_name))
            try:
                f = open(path, 'r')
            except IOError:
                return response
            try:
                contents = response.content.split('\n')
                docs = '\n<!--\n' + f.read().strip() + '\n-->\n'
                response.content = contents[0] + docs + '\n'.join(contents[1:])                
            finally:
                f.close()
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        request._view_func = view_func
        return None

    def _getAppNameFromViewFunc(self, viewFunc):
        module = viewFunc.__module__
        return module.split('.')[-2]

class FlashErrorCodeMiddleware(BaseMiddleware):
    def _process_response(self, request, response):
        isFlash = False
        try:
            isFlash = request._meta.get('HTTP_HTTP_X_FLASH_VERSION')
        except:
             # test code mocking things weirdly?
             pass
        if isFlash and (response.status_code >= 400):
            response.status_code = 200
        return response

class CachingMiddleware(BaseMiddleware):
    def _process_request(self, request):
        from mint.django_rest.rbuilder import modellib
        modellib.Cache.reset()

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
    ''' 
    Adds timing info to the requests, should be off all the time, makes things slower 
    by doing extra serialization even if that's not reflected in metrics!
    '''

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
            # was response.write()
            response.content = response.model.to_xml(request, xobj_model)

            return response
        else:
            if hasattr(response, 'model'):
                # was response.write()
                response.content = response.model.to_xml(request)
            return response


class SerializeXmlMiddleware(SwitchableLogMiddleware):

    def _logResponse(self, outdata, response):
        now = time.localtime()
        urlsFile = RBUILDER_DEBUG_HISTORY
        urlsFile = open(RBUILDER_DEBUG_HISTORY, "a")
        (logFile, logFilePath) = self.getLogFile(False, now)
        urlsFile.write("     (%d)\n" % response.status_code)
        urlsFile.write("     %s\n" % logFilePath)
        urlsFile.close()
        with logFile as f:
            self.logPrint(f, [ dict(status=response.status_code, zzz_content=str(outdata)) ])

    def _process_response(self, request, response):
        if hasattr(response, 'model'):
            metrics = request.GET.get('metrics', None)
            if metrics:
                return response

            format = request.GET.get('format', 'xml')
            outdata = ''
            if format == 'json':
                response['Content-Type'] = 'application/json'
                outdata = response.model.to_json(request)
            else:
                response['Content-Type'] = 'text/xml'
                outdata = response.model.to_xml(request)
            response.write(outdata)
            if self.shouldLog():
                self._logResponse(outdata, response)

        # Originally opened in BaseService. Unfortunately models in collections
        # aren't finalized until this method, so the manager can't be closed in
        # the same scope in which it was opened.
        from mint.django_rest.rbuilder import modellib
        if getattr(modellib.XObjModel, '_rbmgr', None):
            modellib.XObjModel._rbmgr.restDb.close()
            modellib.XObjModel._rbmgr = None

        return response

class AuthHeaderMiddleware(BaseMiddleware):
    # details on mod_python+Django issue below, marked "won't fix" in Django bug tracker
    # https://code.djangoproject.com/ticket/4354
    # this needs to be loaded at the end of the middleware chain
    def _process_response(self, request, response):
        if response.status_code == 401:
            response['WWW-Authenticate'] = "Basic realm=\"rBuilder\""
        return response
      
# NOTE: must also set DEBUG=True in settings to use this. 
class SqlLoggingMiddleware(BaseMiddleware):
    '''log each database hit to a file, profiling use only'''
    def process_response(self, request, response):
        fd = open("/tmp/sql.log", "a")
        for query in connection.queries:
            fd.write("\033[1;31m[%s]\033[0m \033[1m%s\033[0m\n" % (query['time'],
 " ".join(query['sql'].split())))
        fd.close()
        return response
 
