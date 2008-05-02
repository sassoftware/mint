<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Create Package: %s' % project.getNameForDisplay())}</title>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/whizzyupload.js?v=${cacheFakeoutVersion}" />
        <!-- Dialog and dependencies -->
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}/apps/yui/build/container/assets/container.css"/>
        <script type="text/javascript" src="${cfg.staticPath}apps/yui/build/yahoo/yahoo-min.js" />
        <script type="text/javascript" src="${cfg.staticPath}apps/yui/build/yahoo-dom-event/yahoo-dom-event.js" />
        <script type="text/javascript" src="${cfg.staticPath}apps/yui/build/container/container-debug.js" />
    </head>

    <body>
        <script type="text/javascript">
        <![CDATA[
            logDebug('Creating the fileuploadform object');
            function PkgCreatorFileUploadForm()
            {
                this.base = FileUploadForm;
                this.base('${id}', 'getPackageFactories', 'pollUploadStatus', 'cancelUploadProcess');
            }
            PkgCreatorFileUploadForm.prototype = new FileUploadForm();

            PkgCreatorFileUploadForm.prototype.cancelUploadRequest = function()
            {
                logDebug("Canceling upload request");
                req = new JsonRpcRequest('jsonrpc/', this.cancel_uri);
                req.setAuth(getCookieValue('pysid'));
                req.setCallback(function(req){
                    res = evalJSONRequest(req);
                    uploadform.cancelUploadRequestFinished(res);
                    });
                req.send(false, [this.id, this.getFieldnames()]);
            }

            PkgCreatorFileUploadForm.prototype.uploadStatus = function(key)
            {
                if (!this.cancelled){
                    logDebug("uploadStatus " + key);
                    req = new JsonRpcRequest('jsonrpc/', this.status_uri);
                    req.setAuth(getCookieValue("pysid"));
                    req.setCallbackData(key);
                    req.setCallback(evalReq);
                    req.send(false, [this.id, 'uploadfile']);
                }
            }

            var uploadform = new PkgCreatorFileUploadForm();

            function connect_form()
            {
                uploadform.submit_event = connect('getPackageFactories', 'onsubmit', uploadform, 'submitFormData');
            }
            addLoadEvent(connect_form);
            
            evalReq = function(key, req)
            {
                res = evalJSONRequest(req);
                uploadform.uploadStatusCallFinished(key, res);
            }

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
            <h3>Step 1 of 3</h3>
            <div py:def="fileupload_iframe(src, fieldname)" py:strip="True">
                <iframe id="${fieldname}_iframe" src="${src}" class="fileupload" frameborder="0"/>
                <input type="hidden" name="${fieldname}" value="" id="${fieldname}"/>
            </div>
            <form name="getPackageFactories" method="post" action="getPackageFactories" enctype="multipart/form-data" id="getPackageFactories">
                <input type="hidden" name="id" value="${id}"/>
                <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                  <tr>
                  <th>Select Product Version</th>
                  <td>
                    <select name="versionId">
                      <option py:for="(vId, projectId, version_str, desc) in versions" value="${vId}" py:attr="{'selected': vId==versionId and 'selected' or None}" py:content="version_str"/>
                    </select>
                  </td>
                  </tr>
                  <tr>
                  <th>Upload File</th>
                  <td>
                ${fileupload_iframe("upload_iframe?id=%s;fieldname=uploadfile" % id, 'uploadfile')}
                  </td>
                  </tr>
                  <!--<tr>
                  <th>Upload URL</th>
                  <td>
                <input name="upload_url" type="text" />
                  </td>
                  </tr> Not going to support urls right now -->
                </table>
                <p><input type="submit" id="submitButton_getPackageFactories" value="Create Package" onclick="javascript: signal(this.form, 'onsubmit'); return false;"/></p>
            </form>

            <h3 style="color:#FF7001;">Step 1: Upload a bundle</h3>
            <p>Select your source or binary file bundle (rpm, src rpm, tarball, zip, jar, war, ear, egg, etc.) from your computer, or provide the URL.</p>

            <div style="display:none">
            <div id="upload_progress">
                <div class="bd">
                    <div id="progress_indicator" style="border: 1px solid black; margin: auto; height: 20px; width: 90%; position: relative; left: 0px; top: 0px;">
                        <p id="upload_progress_percent_complete" style="margin: 0pt; padding: 0pt; text-align: center; color: black; z-index: 2;">0%</p>
                        <div id="progress_indicator_bar" style="height: 20px; width: 1%; background-color: green; z-index: -1; left: 0px; top: 0px; position: absolute;">
                        </div>
                    </div>
                    <div id="upload_progress_wait">Please wait...</div>
                    <div id="upload_progress_statistics" style="display:none;">
                        <span id="upload_progress_bytes"></span>
                        at <span id="upload_progress_rate"></span>,
                        <span id="upload_progress_eta"></span> remaining
                    </div>
                    <input id="upload_progress_cancel_button" type="button" value="Cancel" disabled="true"/>
                </div>
            </div>
            </div>
        </div>
        </div>
    </body>
</html>
