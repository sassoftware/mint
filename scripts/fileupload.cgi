#!/usr/bin/env python
# Copyright (c) 2008 rPath, Inc.
# All rights reserved

### This is a simple raw cgi handler.  It needs to be CGI so that it can
### process data as it comes in, instead of after the browser has finished
### uploading it.

import cgi
import cgitb

import os, sys, signal

from mint.web import whizzyupload
from mint import config

# TODO: Authenticate?  How?

# The philosophy is to write read status out (8 bytes network ordered) to a
# status file as it's read in 8K at a chunk via a wrapper around the stdin file
# object

def cancel_signal(num, frame):
    print "Status: 200 Ok\n"
    print "Cancelled"
    sys.exit(0)

signal.signal(signal.SIGUSR1, cancel_signal)

open('/tmp/tickler.log', 'a').write('started\n')

#Make this script testable
if "GATEWAY_INTERFACE" in os.environ:
    open('/tmp/tickler.log', 'a').write('uploading\n')
    cgitb.enable()

    open('/tmp/tickler.log', 'a').write(str(os.environ) + '\n')
    open('/tmp/tickler.log', 'a').write(os.getcwd() + '\n')

    #Read the mint configuration
    # XXX this is wrong. we need a way to use the same config settings as
    # the python code is using. without that code
    cfg = config.MintConfig()
    docRoot = os.environ.get('DOCUMENT_ROOT', '')
    cfgPath = os.path.join(docRoot, 'rbuilder.conf')

    if docRoot and os.path.exists(cfgPath):
        cfg.read(cfgPath)
    else:
        cfg.read(config.RBUILDER_CONFIG)

    wkdir = os.path.join(cfg.dataPath, 'tmp')
    open('/tmp/tickler.log', 'a').write('whizzing\n')
    whizzyupload.handle_cgi_request(sys.stdin, sys.stdout, wkdir, 'rb-pc-upload-', os.environ)
    open('/tmp/tickler.log', 'a').write('postwhizzing\n')

