#
# Copyright (c) SAS Institute Inc.
#

import os
import logging
import traceback
import time
import textwrap

import re
import glob
import cProfile
import pstats
import tempfile
import datetime
from cStringIO import StringIO

from debug_toolbar import middleware
from conary.lib import util

from django import http
from django.contrib.auth import authenticate
from django.contrib.redirects import middleware as redirectsmiddleware
from django.http import HttpResponse, HttpResponseBadRequest, QueryDict
from django.core.files.uploadhandler import StopFutureHandlers
from django.utils.datastructures import MultiValueDict
from django.db.utils import IntegrityError
from django.db import connection
import django.core.exceptions as core_exc

from mint.django_rest import handler
from mint.django_rest.rbuilder import auth, errors, models
from mint.django_rest.rbuilder.metrics import models as metricsmodels
from mint.django_rest.rbuilder.errors import PermissionDenied
from mint.django_rest.rbuilder.inventory import errors as ierrors
from mint.lib import mintutils

log = logging.getLogger(__name__)

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
        try:
            # We don't want exceptions on this codepath, so call
            # os.path.exists before stat
            if not os.path.exists(RBUILDER_DEBUG_SWITCHFILE):
                return False
            st = os.stat(RBUILDER_DEBUG_SWITCHFILE)
        except OSError, e:
            if e.errno != 2:
                raise
            return False
        mtime = st.st_mtime
        delta = time.time() - mtime
        return delta < (60*60)

    def _getLogFilenamePattern(self, tm):
        ''' keeps directories neat and organized '''

        ymd = "%d-%02d-%02d" % (tm.tm_year, tm.tm_mon, tm.tm_mday)
        hour = "%02d" % tm.tm_hour

        dirName = os.path.join(RBUILDER_DEBUG_LOGPATH, ymd, hour)
        util.mkdirChain(dirName)

        minsec = "%02dm-%02ds" % (tm.tm_min, tm.tm_sec)
        filenamePattern = os.path.join(dirName, '%s-%%s.log' % (minsec, ))
        return filenamePattern

    def getLogFile(self, request):
        ''' returns log file and path for storing XML debug info'''
        if getattr(request, 'debugFileName', None):
            return file(request.debugFileName, "a"), request.debugFileName

        now = time.localtime(request.startTime)
        filename = None
        filenamePattern = self._getLogFilenamePattern(now)
        counter = 0
        while True:
            try:
                filename = filenamePattern % counter
                fdesc = os.open(filename, os.O_CREAT | os.O_WRONLY | os.O_EXCL)
                break
            except OSError, e:
                if e.errno != 17:
                    raise
                counter += 1
                continue
        # At this point the file is already created on the filesystem,
        # there's no chance another process might stomp over it
        # It would be nice if os.fdopen allowed one to carry the
        # filename around
        debugFile = os.fdopen(fdesc, "w")
        request.debugFileName = filename

        method = request.META.get('REQUEST_METHOD')
        path = self._requestPath(request)

        remoteAddr = request.META.get('REMOTE_ADDR')
        remoteHost = request.META.get('REMOTE_HOST')
        if remoteHost:
            remoteAddr = "%s (%s)" % (remoteAddr, remoteHost)

        tmpl = '''%(remoteAddr)s [%(date)s] "%(method)s %(path)s %(proto)s" %(filename)s\n'''
        formattedDate = self.formatTime(now)
        with open(RBUILDER_DEBUG_HISTORY, "a") as history:
            history.write(tmpl % dict(remoteAddr=remoteAddr, method=method,
                path=path, proto=request.META.get('SERVER_PROTOCOL'),
                filename=filename, date=formattedDate))
        # Print some general things
        self.logLine(debugFile, "Remote host", remoteAddr)
        self.logLine(debugFile, "Server name", request.META.get('SERVER_NAME'))
        self.logLine(debugFile, "Server port", request.META.get('SERVER_PORT'))
        self.logLine(debugFile, "Request time",
            self.formatTime(request.startTime))
        debugFile.write("\n")

        return debugFile, request.debugFileName

    _TimeFormat = "%Y-%m-%d %H:%M:%S %z"

    @classmethod
    def formatTime(cls, tm=None):
        if tm is None:
            tm = time.localtime()
        elif isinstance(tm, (int, float)):
            tm = time.localtime(tm)
        return time.strftime(cls._TimeFormat, tm)

    @classmethod
    def formatSeconds(cls, seconds):
        return "%.2f seconds" % seconds

    def logPrint(self, handle, vars_dicts):
        wrap = textwrap.TextWrapper(width=80, subsequent_indent=' ', break_long_words=False, replace_whitespace=False)
        for vars_dict in vars_dicts:
            for k, v in sorted(vars_dict.items()):
                if isinstance(v, list):
                    # just in case...
                    v = " ".join(str(x) for x in v)
                else:
                    v = str(v)
                v = "\n     ".join(wrap.wrap(v))
                self.logLine(handle, k, v)

    _LineFormat = "%s: %s\n"
    @classmethod
    def logLine(cls, handle, key, value):
        handle.write(cls._LineFormat % (key, value))

    @classmethod
    def _requestPath(cls, request):
        path = getattr(request, 'path', None)
        if path is not None:
            return path
        path = request.META.get('SCRIPT_NAME', '')
        path += request.META.get('PATH_INFO', '')
        qs = request.META.get('QUERY_STRING')
        path = util.urlUnsplit((None, None, None, None, None,
            path, qs, None))
        return path


class RequestLogMiddleware(SwitchableLogMiddleware):
    '''
    When sentinel file is present, log request traffic...
    '''

    def _logRequest(self, request):
        method = request.META.get('REQUEST_METHOD')
        path= self._requestPath(request)
        vers = request.META.get('SERVER_PROTOCOL')
        (logFile, logFilePath) = self.getLogFile(request)

        logFile.write("%s %s %s\n" % (method, path, vers))
        for key, value in sorted(request.META.items()):
            if not key.startswith('HTTP_'):
                continue
            key = key[5:].replace('_', '-').title()
            self.logLine(logFile, key, value)
        logFile.write("\n")
        if not request.raw_post_data:
            return
        if '/xml' not in request.META.get('HTTP_CONTENT_TYPE', ''):
            logFile.write(request.raw_post_data)
            return
        from lxml import etree
        try:
            text = request.raw_post_data.decode('utf8', 'replace')
            doc = etree.fromstring(text)
            text = etree.tostring(doc, pretty_print=True, encoding='utf8')
            logFile.write("<!-- reformatted -->\n")
            logFile.write(text)
        except:
            logFile.write("<!-- reformatting failed -->\n")
            logFile.write(request.raw_post_data)

    def _process_request(self, request):
        request.startTime = time.time()
        if self.shouldLog():
            self._logRequest(request)
        return None

class ExceptionLoggerMiddleware(SwitchableLogMiddleware):

    def _logFailure(self, request, code, exception_msg):
        if not self.shouldLog():
            return
        (logFile, logFilePath) = self.getLogFile(request)
        self.logLine(logFile, "Failure", self.formatTime())
        self.logPrint(logFile, [ dict(code=code, zzz_content=exception_msg) ])

    def _process_request(self, request):
        if self.shouldLog():
            self._logRequest(request)
        return None

    def process_request(self, request):
        mintutils.setupLogging(consoleLevel=logging.INFO,
                consoleFormat='apache')
        return None

    def process_exception(self, request, exception):

        # email will only be sent if this is True AND
        # we don't return early from this function
        doEmail=True

        if isinstance(exception, PermissionDenied):
            # TODO: factor out duplication
            code = 403
            fault = models.Fault(code=code, message=str(exception))
            response = HttpResponse(status=code, content_type='text/xml')
            response.content = fault.to_xml(request)
            log.error(str(exception))
            self._logFailure(request, code, str(exception))
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
            self._logFailure(request, code, str(exception))
            return response

        if isinstance(exception, errors.RbuilderError):
            tbStr = getattr(exception, 'traceback', None)
            status = getattr(exception.__class__, 'status', 500)
            fault = models.Fault(code=status, message=str(exception), traceback=tbStr)
            response = HttpResponse(status=status, content_type='text/xml')
            for k, v in exception.iterheaders(request):
                response[k] = v
            response.content = fault.to_xml(request)
            log.error(str(exception))
            self._logFailure(request, status, str(exception))
            return response

        if isinstance(exception, IntegrityError):
            # IntegrityError is a bug but right now we're using it as a crutch
            # (bad practice, should catch and map to reasonable errors)
            # so do not log tracebacks when there's an uncaught conflict.
            # user will still get an ISE w/ details
            self._logFailure(request, 'IntegrityError', str(exception))
            return handler.handleException(request, exception,
                    doTraceback=False, doEmail=False)

        if isinstance(exception, ierrors.IncompatibleEvent):
            doEmail = False

        return handler.handleException(request, exception, doEmail=doEmail)

class RequestSanitizationMiddleware(BaseMiddleware):
    def _process_request(self, request):
        # django will do bad things if the path doesn't end with / - it uses
        # urljoin which strips off the last component
        if not request.path.endswith('/'):
            request.path += '/'
        from mint.django_rest import deco
        if deco.getHeaderValue(request, 'X-rPath-Repeater'):
            request.META['wsgi.url_scheme'] = 'https'
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


class SetMintConfigMiddleware(BaseMiddleware):

    def _process_request(self, request):
        context = request.META['mint.wsgiContext']
        request.cfg = context.cfg
        request._auth = auth.getAuth(request)
        username, password = request._auth
        request._authUser = authenticate(username=username, password=password,
                mintConfig=request.cfg)
        request._is_admin = auth.isAdmin(request._authUser)
        request._is_authenticated = auth.isAuthenticated(request._authUser)
        return None


class AddCommentsMiddleware(BaseMiddleware):

    useXForm = True

    def _process_response(self, request, response):
        try:
            return self._internal_process_response(request, response)
        except:
            return response


    def _internal_process_response(self, request, response):

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
            isFlash = request._meta.get('HTTP_HTTP_X_FLASH_VERSION') or request._meta.get('HTTP_X_WRAP_RESPONSE_CODES')
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


class QueryParameterMiddleware(BaseMiddleware):

    def _process_request(self, request):
        script_name = request.META.get('SCRIPT_NAME') or ''
        path = request.META['PATH_INFO']
        if ';' in path:
            path, semiColonParams = path.split(';', 1)
            semiColonParams = parse_qsl(semiColonParams)
        else:
            semiColonParams = []
        questionParams = parse_qsl(request.META.get('QUERY_STRING') or '')
        params = questionParams + semiColonParams
        request.path = script_name + path
        request.path_info = path
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

    def _logResponse(self, request, outdata, response):
        (logFile, logFilePath) = self.getLogFile(request)
        now = time.time()
        self.logLine(logFile, "Response time", self.formatTime(now))
        self.logLine(logFile, "Duration", self.formatSeconds(now - request.startTime))
        logFile.write("\nHTTP/1.1 %s\n" % (response.status_code,))
        for key, value in sorted(response.items()):
            self.logLine(logFile, key.title(), value)
        logFile.write('\n')
        logFile.write(str(outdata))

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
                self._logResponse(request, outdata, response)

        # Originally opened in BaseService. Unfortunately models in collections
        # aren't finalized until this method, so the manager can't be closed in
        # the same scope in which it was opened.
        from mint.django_rest.rbuilder import modellib
        if getattr(modellib.XObjModel, '_rbmgr', None):
            modellib.XObjModel._rbmgr.close()
            modellib.XObjModel._rbmgr = None

        return response

    def process_response(self, request, response):
        try:
            return self._process_response(request, response)
        except Exception, e:
            # Don't spam if the exception has a status code lower than 500
            isISE = (getattr(e, 'status', 500) >= 500)
            return handler.handleException(request, e,
                doEmail=isISE, doTraceback=isISE)


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

class ApplicationOctetStreamHandlerMiddleware(BaseMiddleware):
    '''Process application/octet-stream uploads'''
    def _process_request(self, request):
        # @TODO support any large, non-multipart file upload w/o breaking
        # @TODO support base64 encoding
        # @TODO support content-disposition header and filename
        content_type = request.META.get('CONTENT_TYPE')
        try:
            content_length = int(request.META.get('CONTENT_LENGTH', 0))
        except (ValueError, TypeError):
            content_length = 0

        if not request.method in ('POST', 'PUT'):
            return None

        if not content_type == 'application/octet-stream':
            return None

        request._post = QueryDict('')
        request._files = MultiValueDict()
        request._raw_post_data = None

        # HTTP spec says that Content-Length >= 0 is valid
        if content_length == 0:
            return None

        handlers = request.upload_handlers
        unused_handlers = []

        # For compatibility with low-level network APIs (with 32-bit integers),
        # the chunk size should be < 2^31, but still divisible by 4.
        possible_sizes = [x.chunk_size for x in handlers if x.chunk_size]
        chunk_size = min([2**31-4] + possible_sizes)

        # See if the handler will want to take care of the parsing.
        # This allows overriding everything if somebody wants it.
        for handler in handlers:
            result = handler.handle_raw_input(request, request.META,
                                              content_length, '', encoding=None)
            if result is not None:
                return result[0], result[1]

        try:
            for i, handler in enumerate(handlers):
                handler.new_file('', '', content_type, content_length,
                                 charset=None)
        except StopFutureHandlers:
            # put aside the remaining handlers
            unused_handlers = handlers[i+1:]
            handlers = handlers[:i+1]

        counters = [0]*len(handlers)

        while True:
            chunk = request.read(chunk_size)
            if not chunk:
                break

            for i, handler in enumerate(handlers):
                handler.receive_data_chunk(chunk, counters[i])
                counters[i] += len(chunk)

        for i, handler in enumerate(handlers):
            file_obj = handler.file_complete(counters[i])
            if file_obj is not None:
                request.FILES.appendlist('', file_obj)

        for handler in handlers + unused_handlers:
            handler.upload_complete()

        return None

class ProfilingMiddleware(object):
    """
    Profile view calls. If the request has a session ID, accumulate
    stats across requests. Without session ID, profiling will be on
    per-request basis. Profiling data is served in markup comment
    inside each request, and also dumped in /tmp with filenames
    containing session ID or timestamp.
    """
    TEMPDIR  = "/tmp/"
    TEMPLATE = "profiling_%s_"
    COMMENT_SYNTAX = ((re.compile(r'^text/xml|application/x-www-form-urlencoded$', re.I), '<!--', '-->'),
                      (re.compile(r'^application/j(avascript|son)$', re.I), '/*',   '*/' ))


    def find_matching_filenames(self, match_string, latest=100):
        dir = self.TEMPDIR
        # "/tmp/" + "profiling_[SESSION-ID]_" + "*"
        matcher = dir + match_string + "*"
        files = [f for f in glob.glob(matcher) if os.path.isfile(f) and 
                 os.path.getsize(f) > 0]
        files.sort(key=lambda x: -os.path.getmtime(x))
        return files[:latest]

    def process_view(self, request, callback, args, kwargs):
        prefix = self.TEMPLATE % request.COOKIES.get('pysid', datetime.datetime.now().strftime('%s%f'))
        _, filename = tempfile.mkstemp(dir=self.TEMPDIR, prefix=prefix)

        prof = cProfile.Profile()
        args = [request] + list(args)
        response = prof.runcall(callback, *args, **kwargs) # runcall = undocumented.

        prof.dump_stats(filename)
        all_files = self.find_matching_filenames(prefix) # Current file plus any older.
        p = pstats.Stats(*all_files, stream=StringIO())

        # If we have got a 3xx status code, further
        # action needs to be taken by the user agent
        # in order to fulfill the request. So don't
        # attach any stats to the content, because of
        # the content is supposed to be empty and is
        # ignored by the user agent.
        if response.status_code // 100 == 3:
            return response

        # Detect the appropriate syntax based on the
        # Content-Type header.
        for regex, begin_comment, end_comment in self.COMMENT_SYNTAX:
            if regex.match(response['Content-Type'].split(';')[0].strip()):
                break
        else:
            # If the given Content-Type is not
            # supported, don't attach any stats to
            # the content and return the unchanged
            # response.
            return response

        p.sort_stats('time')
        p.print_stats()  # You wouldn't think this'd be necessary, but you'd be wrong.

        # Construct an HTML/XML or Javascript comment, with
        # the formatted stats, written to the StringIO object
        # and attach it to the content of the response.
        comment = '\n%s\n\n%s\n\n%s\n' % (begin_comment, p.stream.getvalue(), end_comment)
        response.content += comment

        # If the Content-Length header is given, add the
        # number of bytes we have added to it. If the
        # Content-Length header is omitted or incorrect,
        # it remains so in order to not change the
        # behaviour of the web server or user agent.
        if response.has_header('Content-Length'):
            response['Content-Length'] = int(response['Content-Length']) + len(comment)

        return response
