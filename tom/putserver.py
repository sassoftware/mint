from mod_python import apache
import os, sys
from conary.lib import util
import xmlrpclib

def handler(req):
    if req.method.upper() != "PUT":
	req.write(xmlrpclib.dumps((0, '')))
        return apache.OK

    fn = os.path.normpath('output/' + req.parsed_uri[6])

    util.mkdirChain(os.path.dirname(fn))
    f = file(fn, 'w+')
    l = util.copyfileobj(req, f)
    f.close()

    apache.log_error("wrote %d bytes of %s" % (l, fn), apache.APLOG_INFO)

    return apache.OK
