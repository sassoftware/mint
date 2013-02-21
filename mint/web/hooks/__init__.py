#
# Copyright (c) 2011 rPath, Inc.
#

import logging
import sys
#from mod_python import apache

from mint import config
from mint.lib import mintutils
from mint.lib import profile
from mint import mint_error
from mint import maintenance
from mint.db.repository import RepositoryManager
from mint.helperfuncs import extractBasePath
from mint.logerror import logWebErrorAndEmail
from mint.rest.server import restHandler
from mint.web import app
from mint.web.rpchooks import rpcHandler
from mint.web.catalog import catalogHandler
from mint.web.hooks.conaryhooks import conaryHandler
from mint.web.webhandler import normPath, setCacheControl, HttpError

from conary import dbstore
from conary.lib import coveragehook

log = logging.getLogger(__name__)


# Global cached objects
_cfg = None


class Context(object):
    db = None
    cfg = None
    req = None
    pathInfo = None
    manager = None


def mintHandler(context):
    webfe = app.MintApp(context.req, context.cfg, db=context.db)
    return webfe._handle(context.pathInfo)


urls = (
    ('/changeset/',        conaryHandler),
    ('/conary/',           conaryHandler),
    ('/repos/',            conaryHandler),
    ('/catalog/',          catalogHandler),
    ('/api/',              restHandler),
    ('/xmlrpc/',           rpcHandler),
    ('/jsonrpc/',          rpcHandler),
    ('/xmlrpc-private/',   rpcHandler),
    ('/',                  mintHandler),
)


def handler(req):
    coveragehook.install()
    if not req.hostname:
        return apache.HTTP_BAD_REQUEST

    # Direct logging to httpd error_log.
    mintutils.setupLogging(consoleLevel=logging.INFO, consoleFormat='apache')
    # Silence some noisy third-party components.
    for name in ('stomp.py', 'boto'):
        logging.getLogger(name).setLevel(logging.ERROR)

    context = Context()
    context.req = req

    # only reload the configuration file if it's changed
    # since our last read
    cfgPath = req.get_options().get("rbuilderConfig", config.RBUILDER_CONFIG)

    global _cfg
    if not _cfg:
        _cfg = config.getConfig(cfgPath)
    context.cfg = cfg = _cfg

    if "basePath" not in req.get_options():
        cfg.basePath = extractBasePath(normPath(req.uri),
                normPath(req.path_info))
        pathInfo = req.path_info
    else:
        cfg.basePath = req.get_options()['basePath']
        # chop off the provided base path
        pathInfo = normPath(req.uri[len(cfg.basePath):])
    context.pathInfo = pathInfo

    if not req.uri.startswith(cfg.basePath + 'setup/') and not cfg.configured:
        if req.uri == cfg.basePath + 'pwCheck':
            # allow pwCheck requests to go through without being
            # redirected - they will simply return "False"
            pass
        else:
            req.headers_out['Location'] = cfg.basePath + "setup/"
            raise apache.SERVER_RETURN, apache.HTTP_MOVED_TEMPORARILY

    context.db = db = dbstore.connect(cfg.dbPath, cfg.dbDriver)
    context.manager = RepositoryManager(cfg, db)

    prof = profile.Profile(cfg)
    prof.startHttp(req.uri)

    ret = apache.HTTP_NOT_FOUND
    try:
        # Proxied Conary requests can have all sorts of paths, so look for a
        # header instead.
        if 'x-conary-servername' in req.headers_in:
            return _tryHandler(conaryHandler, context)
        for match, urlHandler in urls:
            if pathInfo.startswith(match):
                ret = _tryHandler(urlHandler, context)
                break
    finally:
        prof.stopHttp(req.uri)
        context.manager.close()
        if context.db:
            context.db.close()
        coveragehook.save()
        logging.shutdown()
    return ret


def _tryHandler(urlHandler, context):
    req, cfg = context.req, context.cfg

    try:
        return urlHandler(context)

    except HttpError, err:
        return err.code

    except apache.SERVER_RETURN:
        raise

    except mint_error.MaintenanceMode:
        agent = req.headers_in.get('User-agent', '')
        if 'Conary' in agent or 'rPath' in agent:
            # this is a conary client
            return apache.HTTP_SERVICE_UNAVAILABLE
        else:
            # this page offers a way to log in. vice standard error
            # we must force a redirect to ensure half finished
            # work flowpaths don't trigger more errors.
            setCacheControl(req, strict=True)
            mode = maintenance.getMaintenanceMode(cfg)
            if mode == maintenance.EXPIRED_MODE:
                # Bounce to flex UI for registration
                if cfg.basePath.endswith('web/'):
                    cfg.basePath = cfg.basePath[:-4]
                req.headers_out['Location'] = cfg.basePath + 'ui/'
            else:
                # Bounce to maintenance page
                req.headers_out['Location'] = cfg.basePath + 'maintenance'
            return apache.HTTP_MOVED_TEMPORARILY

    except:
        # we only want to handle errors in production mode
        if cfg.debugMode or req.bytes_sent > 0:
            raise

        # Generate a nice traceback and email it to
        # interested parties
        exc_info = sys.exc_info()
        logWebErrorAndEmail(req, cfg, *exc_info)
        del exc_info

        # Send an error page to the user and set the status
        # code to 500 (internal server error).
        req.status = 500
        context.pathInfo = '/unknownError'
        try:
            return mintHandler(context)
        except:
            # Some requests cause MintApp to choke on setup
            # We've already logged the error, so just display
            # the apache ISE page.
            return apache.HTTP_INTERNAL_SERVER_ERROR
