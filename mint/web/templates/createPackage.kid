<?xml version='1.0' encoding='UTF-8'?>
<?python
import simplejson
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
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/whizzyupload.js?v=${cacheFakeoutVersion}" />
        <!-- Dialog and dependencies -->
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}/apps/yui/build/container/assets/container.css"/>
        <script type="text/javascript" src="${cfg.staticPath}apps/yui/build/yahoo/yahoo-min.js" />
        <script type="text/javascript" src="${cfg.staticPath}apps/yui/build/yahoo-dom-event/yahoo-dom-event.js" />
        <script type="text/javascript" src="${cfg.staticPath}apps/yui/build/container/container-min.js" />
    </head>

    <body>
        <script type="text/javascript">
        <![CDATA[
            logDebug('Creating the fileuploadform object');
            function PkgCreatorFileUploadForm()
            {
                this.base = FileUploadForm;
                this.base(${simplejson.dumps(uploadDirectoryHandle)}, 'getPackageFactories', 'pollUploadStatus', 'cancelUploadProcess');
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
              <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
            <h2>Package Creator<span py:if="name" py:strip="True"> - Editing ${name.replace(':source', '')}</span></h2>
            <h3>Step 1 of 3</h3>
            <div py:def="fileupload_iframe(src, fieldname)" py:strip="True">
                <iframe id="${fieldname}_iframe" src="${src}" class="fileupload" frameborder="0"/>
                <input type="hidden" name="${fieldname}" value="" id="${fieldname}"/>
            </div>
            <div id="getPackageFactories_outerdiv">
            <form name="getPackageFactories" method="post" action="getPackageFactories" enctype="multipart/form-data" id="getPackageFactories">
                <input type="hidden" name="uploadDirectoryHandle" value="${uploadDirectoryHandle}"/>
                <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                  <tr>
                  <th>Product Version</th>
                  <td py:if='versions'>
                    ${versionSelection(dict(name='versionId'), versions, False)}
                  </td>
                  <td py:if="not versions">
                    ${prodVer} (${namespace})
                    <input type="hidden" name="sessionHandle" value="${sessionHandle}"/>
                  </td>
                  </tr>
                  <tr>
                  <th>Archive</th>
                  <td>
                      ${fileupload_iframe("upload_iframe?uploadId=%s;fieldname=uploadfile" % uploadDirectoryHandle, 'uploadfile')}
                  </td>
                  </tr>
                  <!--<tr>
                  <th>Upload URL</th>
                  <td>
                <input name="upload_url" type="text" />
                  </td>
                  </tr> Not going to support urls right now -->
                </table>
                <p><input type="submit" id="submitButton_getPackageFactories" value="Upload" onclick="javascript: signal(this.form, 'onsubmit'); return false;"/></p>
            </form>
            </div>

            <h3 style="color:#FF7001;">Step 1: Upload an Archive</h3>
            <p>Select your binary archive (rpm, tar archive) from your computer.</p>

            <div style="display:none">
            <div id="upload_progress">
                <div class="bd">
                    <div id="progress_indicator">
                        <p id="upload_progress_percent_complete">0%</p>
                        <div id="progress_indicator_bar">
                        </div>
                    </div>
                    <div id="upload_progress_wait">Please wait...</div>
                    <div id="upload_progress_statistics" style="display:none;">
                        <span id="upload_progress_bytes"></span>
                        &nbsp;at <span id="upload_progress_rate"></span>,
                        <span id="upload_progress_eta"></span>&nbsp;remaining
                    </div>
                    <form><!-- IE Errors out if the YUI has to embed its own "form" control -->
                    <input id="upload_progress_cancel_button" type="button" value="Cancel" disabled="true"/>
                    </form>
                </div>
            </div>
            </div>
        </div>
        </div>
    </body>
</html>
