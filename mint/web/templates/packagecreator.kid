<?xml version='1.0' encoding='UTF-8'?>
<?python
import simplejson
from mint.packagecreator import drawField, isChecked, isSelected, effectiveValue, expandme

lang = None;
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#" py:extends="'library.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <div py:strip="True" py:def="createPackage(uploadDirectoryHandle, sessionHandle, name)">
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
        <h3>Upload an Archive</h3>
        <p>Select your binary (not source) archive (rpm, tar archive) from your computer.</p>
        <div id="getPackageFactories_outerdiv">
        <div py:def="fileupload_iframe(src, fieldname)" py:strip="True">
            <iframe id="${fieldname}_iframe" src="${src}" class="fileupload" frameborder="0"/>
            <input type="hidden" name="${fieldname}" value="" id="${fieldname}"/>
        </div>
        <form name="getPackageFactories" method="post" action="getPackageFactories" enctype="multipart/form-data" id="getPackageFactories">
            <input type="hidden" name="uploadDirectoryHandle" value="${uploadDirectoryHandle}"/>
            <input type="hidden" name="sessionHandle" value="${sessionHandle}"/>
            <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
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
        </div><!-- #getPackageFactories_outerdiv -->
        <div style="display:none">
            <div id="upload_progress" title="File Upload Progress">
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

    <div py:def="drawLabel(fieldId, field)" py:strip="True">
      <label for="${fieldId}" id="${fieldId}_label" py:attrs="{'class': field.required and 'required' or None}">${field.descriptions[lang]}</label>
    </div>

    <div py:def="drawDescription(fieldId, field)" py:strip="True">
        <?python
            desc = field.constraintsDescriptions.get(lang, '')
        ?>
        <div py:if="desc" id='${fieldId}_help' class="help">${desc}</div>
    </div>

    <div py:def="drawHiddenReference(fieldId, field, prefilled, prevChoices)" py:strip="True">
      <input id="${fieldId + '_reference'}" type="hidden" name="${field.name + '_reference'}" value="${effectiveValue(field, prefilled, prevChoices)[1]}"/>
    </div>

    <div py:def="drawTextField(fieldId, field, possibles, prefilled, prevChoices)" py:strip="True">
      ${drawLabel(fieldId, field)}
      <?python
        value, reference = effectiveValue(field, prefilled, prevChoices)
      ?>
      <div class="expandableformgroupItems">
        <div py:if="not expandme(value)" py:strip="True">
          <input type="text" id="${fieldId}" name="${field.name}"
              value="${value}"/>
          <div id="${fieldId}_expander" class="resize expander" onclick="javascript:toggle_textarea(${simplejson.dumps(fieldId)})">
            &nbsp;
          </div>
        </div>
        <div py:if="expandme(value)" py:strip="True">
          <textarea id="${fieldId}" name="${field.name}" rows="5">${value}</textarea>
        </div>
        ${drawDescription(fieldId, field)}
        ${drawHiddenReference(fieldId, field, prefilled, prevChoices)}
      </div>
    </div>

    <div py:def="drawSelectField(fieldId, field, possibles, prefilled, prevChoices)" py:strip="True">
      ${drawLabel(fieldId, field)}
      <div class="expandableformgroupItems">
        <select name="${field.name}" id="${fieldId}" py:attrs="{'multiple': field.multiple and 'multiple' or None}">
          <option py:for="val in sorted(possibles)" id="${fieldId}_${val}" value="${val}" py:attrs="{'selected': isSelected(field, val, prefilled, prevChoices) and 'selected' or None}" py:content="val"/>
        </select>
        ${drawDescription(fieldId, field)}
        ${drawHiddenReference(fieldId, field, prefilled, prevChoices)}
      </div>
    </div>

    <div py:def="drawCheckBoxes(fieldId, field, possibles, prefilled, prevChoices)" py:strip="True">
      ${drawLabel(fieldId, field)}
         <div class="expandableformgroupItems">
         <div py:for="val in sorted(possibles)">
           <input id="${fieldId}_${val}" name="${field.name}" class="check fieldgroup_check" py:attrs="{'type': field.multiple and 'checkbox' or 'radio', 'checked': isSelected(field, val, prefilled, prevChoices) and 'checked' or None}" value="${val}"/>
           <label class="check_label" for="${fieldId}_${val}">${val}</label>
         </div> <!--possibles-->
         ${drawDescription(fieldId, field)}
         ${drawHiddenReference(fieldId, field, prefilled, prevChoices)}
         </div> <!--expandableformgroupItems-->
    </div>

    <div py:def="drawBooleanField(fieldId, field, prefilled, prevChoices)" py:strip="True">
      ${drawLabel(fieldId, field)}
        <div class="expandableformgroupItems">
        <div py:for="val in ['True', 'False']">
          <input id="${fieldId}_${val}" name="${field.name}" class="check fieldgroup_check" type="radio" py:attrs="{'checked': isChecked(field, val, prefilled, prevChoices) and 'checked' or None}" value="${val}"/>
          <label class="check_label" for="${fieldId}_${val}">${val}</label>
        </div> <!--for-->
        ${drawDescription(fieldId, field)}
        ${drawHiddenReference(fieldId, field, prefilled, prevChoices)}
        </div> <!--expandableformgroupItems-->
    </div>


    <div py:strip="True" py:def="createPackageInterview(editing, sessionHandle, factories, prevChoices)">
        <script type="text/javascript">
        <![CDATA[
        function changeFactory(){
            var sel = $('factoryHandle');

            //See that the only child of "chosen_factory" isn't the one we're looking for
            var chosen = $('chosen_factory');
            for (var child=0; chosen.childNodes.length > child; child++)
            {
                var elem = chosen.childNodes[child];
                if (sel.value != elem.id)
                {
                    //Don't ever want to have two of the same ID, so remove it
                    swapDOM(elem, null);
                    // put this factory back in the holding tank
                    appendChildNodes('factory_dumping_ground', elem);
                }
                else{
                    //Otherwise, we're changing to what we were before, do nothing
                    return;
                }
            }

            //Grab the selected factory and move it into "chosen_factory"
            var elem = $(sel.value);
            swapDOM(elem, null);
            appendChildNodes('chosen_factory', elem);
        }

        function shrinkToTextInput(e)
        {
            swapDOM(e, INPUT({name: e.name, id: e.id, value: e.value}, null));
            removeElementClass(e.id + "_expander", 'collapser');
            addElementClass(e.id + "_expander", 'expander')
        }

        function expandToTextArea(e)
        {
            swapDOM(e, TEXTAREA({name: e.name, id: e.id, rows: 5}, e.value));
            removeElementClass(e.id + "_expander", 'expander');
            addElementClass(e.id + "_expander", 'collapser')
        }

        function toggle_textarea(tid)
        {
            var e = $(tid);
            if (e.tagName.toLowerCase() == 'input')
            {
                expandToTextArea(e);
            }
            else
            {
                shrinkToTextInput(e);
            }
        }

        addLoadEvent(changeFactory);
        ]]>
        </script>
        <h3>Confirm Package Details</h3>
        <p>Package Creator has selected a list of possible package type(s) to use with the archive that you uploaded, and has gathered as much information from it as possible.  Please confirm the correct package type, and verify the information displayed.</p>

        <form name="savePackage" method="post" action="savePackage" id="savePackage">
            <input type="hidden" name="sessionHandle" value="${sessionHandle}"/>
            <div class="expandableformgroupTitle">Package Details</div>
            <div class="expandableformgroup">
              <div>
                <label for="factoryHandle" class="required">Package Type</label>
                <div class="expandableformgroupItems">
                    <select py:if="len(factories) > 1" name="factoryHandle" id="factoryHandle" onchange="javascript:changeFactory()">
                      <option py:for="(factoryHandle, factoryDef, values) in factories" value="${factoryHandle}">${str(factoryDef.getDisplayName())}</option>
                    </select>
                    <p py:if="len(factories) == 1" py:strip="True">
                        ${factories[0][1].getDisplayName()}
                        <input id="factoryHandle" type="hidden" name="factoryHandle" value="${factories[0][0]}"/>
                    </p>
                    <p py:if="1 > len(factories)" py:strip="True">
                        Shouldn't get here, should show an error instead.
                    </p>
                  <div class="expandableformgroupSeparator">&nbsp;</div>
                </div>
              </div>
              <!-- The factory interview -->

              <div id="chosen_factory" />

              <!-- End factory interview -->
            </div>
            <p py:if="editing"><input type="submit" id="submitButton_savePackage" value="Save Package" /></p>
            <p py:if="not editing"><input type="submit" id="submitButton_savePackage" value="Create Package" /></p>
        </form>

        <div style="display: none" id="factory_dumping_ground">
            <div py:for="(factoryIndex, (factoryHandle, factoryDef, values)) in enumerate(factories)" id="${factoryHandle}">
              <div py:for="field in factoryDef.getDataFields()" py:strip="True">
        ${drawField(factoryIndex, field, values, prevChoices, dict(unconstrained = drawTextField, medium_enumeration=drawSelectField, small_enumeration=drawCheckBoxes, large_enumeration=drawTextField, boolean = drawBooleanField))}
                <div class="expandableformgroupSeparator">&nbsp;</div>
              </div>
            </div>
        </div>
    </div>

    <div py:strip="True" py:def="buildPackage(sessionHandle, type='Package')">
        <script type="text/javascript">
            <![CDATA[
var polldata = {
    sessionHandle: ${simplejson.dumps(sessionHandle)}
};

var buildlength = '';

function buildSuccess()
{
    hideElement('building');
    showElement('build_success');
    hideElement('build_fail');
}

function buildFail()
{
    hideElement('building');
    showElement('build_fail');
    hideElement('build_success');
}

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
            buildSuccess();
        }
        else {
            // TODO: Print the failure
            updateStatusArea({status: STATUS_ERROR, message: "An error occurred while building: " + isFinished[1] + ": " + isFinished[2]});
            buildFail();
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

        <h3>Build ${type.title()}</h3>
        <p id="building">Your ${type.lower()} has been created and is now building.  Please be patient while the build completes.</p>

        <!-- the poller -->
        ${statusArea("%s Build" % type.title())}
        <p id="build_log"><a href="getPackageBuildLogs?sessionHandle=${sessionHandle}" target="_NEW">Full build log</a></p>
    </div>

</html>
