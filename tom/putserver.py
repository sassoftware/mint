from mod_python import apache
import os, sys
from conary.lib import util

def handler(req):
    if req.method.upper() != "PUT":
        return apache.METHOD_NOT_ALLOWED

    fn = os.path.normpath('output/' + req.parsed_uri[6])

    util.mkdirChain(os.path.dirname(fn))
    f = file(fn, 'w+')
    l = util.copyfileobj(req, f)
    f.close()

    apache.log_error("wrote %d bytes of %s" % (l, fn), apache.APLOG_INFO)

    return apache.OK
