<?xml version='1.0' encoding='UTF-8'?>
<?python
import simplejson
from mint.helperfuncs import truncateForDisplay
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Create Package: %s' % project.getNameForDisplay())}</title>
    </head>

    <body>
        <script type="text/javascript">
            <![CDATA[
var polldata = {
    sessionHandle: ${simplejson.dumps(sessionHandle)},
};

var buildlength = '';

function processResponse(res)
{
    logDebug('[JSON] response: ', res.responseText);
    //Evaluate the response
    isFinished = evalJSONRequest(res);
    //Update the status
    if (! isFinished[0])
    {
        buildlength += '.';
        if (buildlength.length > 3)
        {
            buildlength = '';
        }
        updateStatusArea({status: STATUS_RUNNING, message: isFinished[2] + buildlength}); 
        //Schedule the next
        callLater(2, makeRequest);
    }
    else
    {
        if (isFinished[1] == 2){
            updateStatusArea({status: STATUS_FINISHED, message: "Build finished, package committed."});
            // TODO: Set up a "start over" form
        }
        else {
            // TODO: Print the failure
            updateStatusArea({status: STATUS_ERROR, message: "An error occurred while building: " + isFinished[1] + ": " + isFinished[2]});
        }
    }
}

function makeRequest()
{
    var req = new JsonRpcRequest('jsonrpc/', 'getPackageBuildStatus')
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processResponse)
    req.send(false, [polldata.sessionHandle])
}

addLoadEvent(function() {roundElement('statusAreaHeader', {'corners': 'tl tr'})});
addLoadEvent(makeRequest);
            ]]>
        </script>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
            </div>

            <div id="middle">
            <p py:if="message" class="message" py:content="message"/>
            <h1>Package Creator</h1>
            <h3>Step 3 of 3</h3>

            ${statusArea("Package Build")}
            <!-- the poller -->

            <h3 style="color:#FF7001;">Step 3: Build package</h3>
            <p>Your package is building.  Please be patient while this process completes.</p>

            </div>
        </div>
    </body>
</html>
