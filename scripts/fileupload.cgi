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

#Make this script testable
if "GATEWAY_INTERFACE" in os.environ:
    cgitb.enable()

    #Read the mint configuration
    # RBUILDER_CONFIG is not always going to be defined to the proper path, so look it up
    # from the DOCUMENT_ROOT if available there.
    cfg = config.MintConfig()
    docRoot = os.environ.get('DOCUMENT_ROOT', '')
    cfgPath = os.path.join(docRoot, 'rbuilder.conf')

    if docRoot and os.path.exists(cfgPath):
        cfg.read(cfgPath)
    else:
        cfg.read(config.RBUILDER_CONFIG)

    wkdir = os.path.join(cfg.dataPath, 'tmp')
    whizzyupload.handle_cgi_request(sys.stdin, sys.stdout, wkdir, 'rb-pc-upload-', os.environ)

