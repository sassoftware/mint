#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import base64
import simplejson
import sys
import xmlrpclib

from mod_python import apache

from mint import config
from mint import server
from mint.web.webhandler import getHttpAuth
from mint import maintenance

from mint.rmakeconstants import buildjob, buildtrove

from conary import versions
from conary.deps import deps

def makeXMLCall(srvr, method, XMLParams):
    return srvr.callWrapper(method, ('anonymous', 'anonymous'), XMLParams)

def rMakeHandler(req, cfg, pathInfo = None):
    maintenance.enforceMaintenanceMode(cfg)

    if req.method.upper() != 'POST':
        return apache.HTTP_METHOD_NOT_ALLOWED
    (paramList, method) = xmlrpclib.loads(req.read())
    if req.headers_in['Content-Type'] != 'text/xml':
        return apache.HTTP_BAD_REQUEST
    if method != 'receiveEvents':
        return apache.HTTP_METHOD_NOT_ALLOWED
    UUID = req.unparsed_uri.split('/')[2]

    # instantiate a MintServer
    srvr = server.MintServer(cfg, allowPrivate = True, req = req)

    eventList = paramList[0]
    for event in eventList:
        stateInfo, eventDetails = event
        # job level notifications
        if stateInfo[0] in ('JOB_STATE_UPDATED', 'JOB_LOG_UPDATED'):
            jobId, status, statusMessage = eventDetails
            if status == buildjob.STATE_COMMITTING:
                statusMessage = 'Committing...'
            if status == buildjob.STATE_COMMITTED:
                statusMessage = 'Successfully Committed'
            if stateInfo[1] == buildjob.STATE_STARTED:
                # set the job ID
                makeXMLCall(srvr, 'setrMakeBuildJobId',
                            (UUID, jobId))
            method = 'setrMakeBuildStatus'
            makeXMLCall(srvr, method, (UUID, status, statusMessage))
        # job troves notification. submit them all.
        elif stateInfo[0] in ('JOB_TROVES_SET', 'JOB_COMMITTED'):
            method = 'setrMakeBuildTroveStatus'
            for trvName, trvVersion, trvFlavor in eventDetails[1]:
                trvSpecVersion = str(versions.ThawVersion(trvVersion))
                trvSpecFlavor = str(deps.ThawFlavor(trvFlavor))
                statusMessage = trvName + '=' + trvSpecVersion + '[' + \
                                trvSpecFlavor + ']'
                status = buildtrove.TROVE_STATE_INIT
                makeXMLCall(srvr, method, (UUID, trvName, trvVersion,
                                           status, statusMessage))
        # trove level status functions
        elif stateInfo[0] in ('TROVE_STATE_UPDATED', 'TROVE_LOG_UPDATED'):
            jobId, troveTuple = eventDetails[0]
            status, statusMessage = eventDetails[1:]
            trvName, trvVersion, trvFlavor = troveTuple
            method = 'setrMakeBuildTroveStatus'
            makeXMLCall(srvr, method, (UUID, trvName, trvVersion,
                                       status, statusMessage))

    resp = xmlrpclib.dumps((False,), methodresponse=1)
    req.content_type = "text/xml"
    req.write(resp)
    return apache.OK

def handler(req):
    cfg = config.MintConfig()
    cfg.read(req.filename)

    return rMakeHandler(req, cfg)
