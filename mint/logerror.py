#
# Copyright (c) 2005-2008 rPath, Inc.
# All rights reserved
#

"""
Methods for logging and reporting errors.
"""

import os
import socket
import sys
import tempfile
import time
import traceback
from conary.lib import util as conary_util

from mint.mint_error import MailError
from mint.lib import maillib


def logWebErrorAndEmail(req, cfg, e_type, e_value, e_tb,
  location='web interface', doEmail=True):
    from mod_python import apache
    
    conn = req.connection
    req.add_common_vars()
    info_dict = {
        'local_addr'     : conn.local_ip + ':' + str(conn.local_addr[1]),
        'local_host'     : conn.local_host,
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

    apache.log_error('sending mail to %s and %s' % (cfg.bugsEmail,
        cfg.smallBugsEmail))
    try:
        logErrorAndEmail(cfg, e_type, e_value, e_tb, location, info_dict,
           smallStream=sys.stderr, doEmail=doEmail)
    except MailError, error:
        apache.log_error("Failed to send e-mail to %s, reason: %s" %
            (cfg.bugsEmail, str(error)))
    sys.stderr.flush()


def logErrorAndEmail(cfg, e_type, e_value, e_tb, location, info_dict,
  prefix='mint-error-', smallStream=sys.stderr, doEmail=True):
    timeStamp = time.ctime(time.time())
    realHostName = socket.getfqdn()

    # Format large traceback to file
    (tbFd, tbPath) = tempfile.mkstemp('.txt', prefix)
    large = os.fdopen(tbFd, 'w+')
    print >> large, ('Unhandled exception from %s on %s:'
        % (location, realHostName))
    print >> large, 'Time of occurrence: %s' % timeStamp
    print >> large, 'See also: %s' % tbPath
    print >> large
    conary_util.formatTrace(e_type, e_value, e_tb, stream=large,
        withLocals=False)
    print >> large
    print >> large, 'Full stack:'
    print >> large
    try:
        conary_util.formatTrace(e_type, e_value, e_tb, stream=large,
            withLocals=True)
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
        print >> large
        print >> large, '*** Traceback formatter crashed! ***'
        print >> large, 'Formatter crash follows:'
        conary_util.formatTrace(handlerErrorType, handlerErrorValue,
            handlerErrorTB, stream=large, withLocals=False)
        print >> large, '*** End formatter crash log ***'
    print >> large
    print >> large, 'Environment:'
    for key, val in sorted(info_dict.items()):
        print >> large, '%s: %s' % (key, val)
    large.seek(0)

    # Format small traceback
    small = conary_util.BoundedStringIO()
    print >> small, ('Unhandled exception from %s on %s:'
        % (location, realHostName))
    conary_util.formatTrace(e_type, e_value, e_tb, stream=small,
        withLocals=False)
    print >> small, 'Extended traceback at %s' % tbPath

    small.seek(0)
    conary_util.copyfileobj(small, smallStream)
    smallStream.flush()

    # send email
    if cfg and doEmail:
        base_exception = traceback.format_exception_only(
            e_type, e_value)[-1].strip()
        if cfg.rBuilderOnline:
            subject = '%s: %s' % (realHostName, base_exception)
        else:
            extra = {'hostname': realHostName}
            subject = cfg.bugsEmailSubject % extra

        if cfg.bugsEmail:
            maillib.sendMailWithChecks(cfg.bugsEmail, cfg.bugsEmailName,
                                     cfg.bugsEmail, subject, large.read())
        if cfg.smallBugsEmail:
            small.seek(0)
            maillib.sendMailWithChecks(cfg.bugsEmail, cfg.bugsEmailName,
                cfg.smallBugsEmail, subject, small.read())

    large.close()
