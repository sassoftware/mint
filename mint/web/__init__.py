#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#

import os, time, socket, tempfile, sys, traceback, shutil
from conary.lib import util as conary_util
from mod_python import apache

from mint.mint_error import MailError
from mint import users

def logErrorAndEmail(req, cfg, exception, e, bt):
    c = req.connection
    req.add_common_vars()
    info_dict = {
        'local_addr'     : c.local_ip + ':' + str(c.local_addr[1]),
        'local_host'     : c.local_host,
        'protocol'       : req.protocol,
        'hostname'       : req.hostname,
        'request_time'   : time.ctime(req.request_time),
        'status'         : req.status,
        'method'         : req.method,
        'headers_in'     : req.headers_in,
        'headers_out'    : req.headers_out,
        'uri'            : req.uri,
        'subprocess_env' : req.subprocess_env,
        'referer'        : req.headers_in.get('referer', 'N/A')
    }

    timeStamp = time.ctime(time.time())
    realHostName = socket.getfqdn()

    # Format large traceback to file
    (fd, tb_path) = tempfile.mkstemp('.txt', 'mint-error-')
    large = os.fdopen(fd, 'w')
    print >>large, 'Unhandled exception from mint web interface on %s:' \
        % realHostName
    print >>large, 'Time of occurrence: %s' % timeStamp
    print >>large, 'See also: %s' % tb_path
    print >>large
    conary_util.formatTrace(exception, e, bt, stream=large, withLocals=False)
    print >>large
    print >>large, 'Full stack:'
    print >>large
    try:
        conary_util.formatTrace(exception, e, bt, stream=large, withLocals=True)
    except:
        # The extended traceback formatter can crash when uncooperative
        # objects do something special when marshalled. For example,
        # derivatives of Thread may abort before Thread itself is
        # initialized, which causes __repr__ to crash, and
        # ServerProxy derivatives may crash when __safe_str__ is
        # improperly sent as a remote procedure call instead of
        # throwing an AttributeError.
        #
        # None of these conditions should prevent the original
        # exception from being logged and emailed, if only in their
        # short form.

        handlerErrorType, handlerErrorValue, handlerErrorTB = sys.exc_info()
        print >>large
        print >>large, '*** Traceback formatter crashed! ***'
        print >>large, 'Formatter crash follows:'
        conary_util.formatTrace(handlerErrorType, handlerErrorValue,
            handlerErrorTB, stream=large, withLocals=False)
    print >>large
    print >>large, 'Environment:'
    for key, val in sorted(info_dict.items()):
        print >>large, '%s: %s' % (key, val)
    large.seek(0)

    # Format small traceback to memory
    small = conary_util.BoundedStringIO()
    print >>small, 'Unhandled exception from mint web interface on %s:' \
        % realHostName
    conary_util.formatTrace(exception, e, bt, stream=small, withLocals=False)
    print >>small, 'Extended traceback at %s' % tb_path
    small.seek(0)

    # Log to apache
    apache.log_error('sending mail to %s and %s' % (cfg.bugsEmail, cfg.smallBugsEmail))
    shutil.copyfileobj(small, sys.stderr)
    sys.stderr.flush()
    small.seek(0)

    # send email
    base_exception = traceback.format_exception_only(exception, e)[-1].strip()
    if cfg.rBuilderOnline:
        subject = '%s: %s' % (realHostName, base_exception)
    else:
        extra = {'hostname': realHostName}
        subject = cfg.bugsEmailSubject % extra
    try:
        if cfg.bugsEmail:
            users.sendMailWithChecks(cfg.bugsEmail, cfg.bugsEmailName,
                                     cfg.bugsEmail, subject, large.read())
        if cfg.smallBugsEmail:
            users.sendMailWithChecks(cfg.bugsEmail, cfg.bugsEmailName,
                                     cfg.smallBugsEmail, subject, small.read())
    except MailError, e:
        apache.log_error("Failed to send e-mail to %s, reason: %s" % \
            (cfg.bugsEmail, str(e)))

    small.close()
    large.close()


