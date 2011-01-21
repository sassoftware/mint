<?xml version='1.0' encoding='UTF-8'?>
<?python
import json
from mint.packagecreator import drawField, isChecked, isSelected, effectiveValue, expandme

lang = None;
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#" py:extends="'library.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <div py:strip="True" py:def="createPackage(uploadDirectoryHandle, sessionHandle, name, helpText)">
        <script type="text/javascript">
        <![CDATA[
            logDebug('Creating the fileuploadform object');
            function PkgCreatorFileUploadForm()
            {
                this.base = FileUploadForm;
                this.base(${json.dumps(uploadDirectoryHandle)}, 'getPackageFactories', 'pollUploadStatus', 'cancelUploadProcess');
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
        <h2>Package Files</h2>
        <p py:content="helpText">Select your binary (not source) archive (rpm, tar archive) from your computer.</p>
        <div id="getPackageFactories_outerdiv">
        <div py:def="fileupload_iframe(src, fieldname)" py:strip="True">
            <iframe id="${fieldname}_iframe" src="${src}" class="fileupload" frameborder="0"/>
            <input type="hidden" name="${fieldname}" value="" id="${fieldname}"/>
        </div>
        <form name="getPackageFactories" method="post" action="getPackageFactories" enctype="multipart/form-data" id="getPackageFactories">
            <input type="hidden" name="uploadDirectoryHandle" value="${uploadDirectoryHandle}"/>
            <input type="hidden" name="sessionHandle" value="${sessionHandle}"/>
            <table class="mainformhorizontal">
              <tr>
              <td class="form-label">Archive:</td>
              <td>
                  ${fileupload_iframe("upload_iframe?uploadId=%s;fieldname=uploadfile" % uploadDirectoryHandle, 'uploadfile')}
                  <div class="help">Specify a binary archive in RPM, deb or tar format.</div>
              </td>
              </tr>
              <!--<tr>
              <th>Upload URL</th>
              <td>
            <input name="upload_url" type="text" />
              </td>
              </tr> Not going to support urls right now -->
            </table>
            <p class="p-button"><input type="submit" id="submitButton_getPackageFactories" value="Upload" onclick="javascript: signal(this.form, 'onsubmit'); return false;"/></p>
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
      <label for="${fieldId}" id="${fieldId}_label" py:attrs="{'class': field.required and 'required' or None}">${field.descriptions[lang]}:</label>
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
        <table class="singlerowhorizontal">
        <tr>
            <td>${drawLabel(fieldId, field)}</td>
            <?python
                value, reference = effectiveValue(field, prefilled, prevChoices)
            ?>
            <td class="expandableformgroupItems">
            <div py:if="not expandme(value)" py:strip="True">
                <input type="text" id="${fieldId}" name="${field.name}" value="${value}"/>
                <div id="${fieldId}_expander" class="resize expander" onclick="javascript:toggle_textarea(${json.dumps(fieldId)})">
                    <img src="${cfg.staticPath}/apps/mint/images/spacer.gif" width="18" height="18" border="0" />
                </div>
            </div>
            <div py:if="expandme(value)" py:strip="True">
                <textarea id="${fieldId}" name="${field.name}" rows="5">${value}</textarea>
            </div>
            ${drawDescription(fieldId, field)}
            ${drawHiddenReference(fieldId, field, prefilled, prevChoices)}
            </td>
        </tr>
        </table>
    </div>

    <div py:def="drawSelectField(fieldId, field, possibles, prefilled, prevChoices)" py:strip="True">
        <table class="singlerowhorizontal">
        <tr>
            <td>${drawLabel(fieldId, field)}</td>
            <td class="expandableformgroupItems">
            <select name="${field.name}" id="${fieldId}" py:attrs="{'multiple': field.multiple and 'multiple' or None}">
                <option py:for="val in sorted(possibles)" id="${fieldId}_${val}" value="${val}" py:attrs="{'selected': isSelected(field, val, prefilled, prevChoices) and 'selected' or None}" py:content="val"/>
            </select>
            ${drawDescription(fieldId, field)}
            ${drawHiddenReference(fieldId, field, prefilled, prevChoices)}
            </td>
        </tr>
        </table>
    </div>

    <div py:def="drawCheckBoxes(fieldId, field, possibles, prefilled, prevChoices)" py:strip="True">
        <table class="singlerowhorizontal">
        <tr>
            <td>${drawLabel(fieldId, field)}</td>
            <td class="expandableformgroupItems">
                <div py:for="val in sorted(possibles)">
                <input id="${fieldId}_${val}" name="${field.name}" class="check fieldgroup_check" py:attrs="{'type': field.multiple and 'checkbox' or 'radio', 'checked': isSelected(field, val, prefilled, prevChoices) and 'checked' or None}" value="${val}"/>
                <label class="check_label" for="${fieldId}_${val}">${val}</label>
                </div> <!--possibles-->
                ${drawDescription(fieldId, field)}
                ${drawHiddenReference(fieldId, field, prefilled, prevChoices)}
            </td>
        </tr>
        </table>
    </div>

    <div py:def="drawBooleanField(fieldId, field, prefilled, prevChoices)" py:strip="True">
        <table class="singlerowhorizontal">
        <tr>
            <td>${drawLabel(fieldId, field)}</td>
            <td class="expandableformgroupItems">
                <div py:for="val in ['True', 'False']">
                <input id="${fieldId}_${val}" name="${field.name}" class="check fieldgroup_check" type="radio" py:attrs="{'checked': isChecked(field, val, prefilled, prevChoices) and 'checked' or None}" value="${val}"/>
                <label class="check_label" for="${fieldId}_${val}">${val}</label>
                </div> <!--for-->
                ${drawDescription(fieldId, field)}
                ${drawHiddenReference(fieldId, field, prefilled, prevChoices)}
            </td>
        </tr>
        </table>
    </div>


    <div py:strip="True" py:def="createPackageInterview(editing, sessionHandle, factories, prevChoices, recipeContents, useOverrideRecipe)">
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
        <h2>Confirm Package Details</h2>
        <p>All information that could be obtained from the archive you uploaded
           appears below. Please review (making any necessary changes or
           additions) and click the "Create Package" button.</p>

        <form name="savePackage" method="post" action="savePackage" id="savePackage">
            <input type="hidden" name="sessionHandle" value="${sessionHandle}"/>
            <table class="singlerowhorizontal">
            <tr>
                <td style="height:24px;"><label for="factoryHandle" class="required">Archive Type:</label></td>
                <td class="expandableformgroupItems">
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
                </td>
            </tr>
            </table>
            
            <!-- The factory interview -->
            <div id="chosen_factory" />

            ${recipeEditor('package', recipeContents, useOverrideRecipe, 'savePackage')}

            <p py:if="editing" class="p-button"><button id="submitButton_savePackage" type="submit" class="img"><img src="${cfg.staticPath}apps/mint/images/save_package_button.png" alt="Submit" /></button></p>
            <p py:if="not editing" class="p-button"><button id="submitButton_savePackage" type="submit" class="img"><img src="${cfg.staticPath}apps/mint/images/create_package_button.png" alt="Submit" /></button></p>

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

    <div py:strip="True" py:def="buildPackage(sessionHandle, type='Package', helpText='')">
        <script type="text/javascript">
            <![CDATA[
var polldata = {
    sessionHandle: ${json.dumps(sessionHandle)}
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
    var req = new JsonRpcRequest('jsonrpc/', 'getPackageBuildStatus');
    req.setAuth(getCookieValue("pysid"));
    req.setCallback(processResponse);
    req.send(false, [polldata.sessionHandle]);
}

addLoadEvent(makeRequest);
            ]]>
        </script>

        <h2>Build ${type.title()}</h2>
        <p id="building" py:content="helpText"/>

        <!-- the poller -->
        ${statusArea("%s Build" % type.title())}
        <p id="build_log"><a href="getPackageBuildLogs?sessionHandle=${sessionHandle}" target="_NEW">View build log</a></p>
    </div>

    <div py:def="recipeEditor(recipeType='appliance', recipeContents='', useOverrideRecipe=False, submitFormId='')" py:strip="True">
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/jquery-ittabs.js?v=${cacheFakeoutVersion}" />
        <script type="text/javascript">
            <![CDATA[

            var wasUsingOverrideRecipe = false;
            var userConfirmed = false;
            var ourForm = jQuery('#${submitFormId}').get(0);

            function handleYes() {
                // Confirmed to remove customizations
                userConfirmed = true;
                ourForm.submit();
            }

            function handleNo() {
                // Do nothing
                return;
            }

            jQuery(document).ready(function() {
                wasUsingOverrideRecipe = jQuery('#useOverrideRecipeCheckbox')[0].checked;
                if ('${submitFormId}' != '') {
                    jQuery('#${submitFormId}').submit(function () {
                        var useOverrideRecipe = jQuery('#useOverrideRecipeCheckbox')[0].checked;
                        if (wasUsingOverrideRecipe && !useOverrideRecipe && !userConfirmed) {
                            modalYesNo(handleYes, handleNo);
                            return false;
                        }
                        return true;
                    });
                }
                jQuery('#recipeContents').EnableTabs();
                jQuery('#useOverrideRecipeCheckbox').click(function() {
                    if (this.checked) {
                        jQuery('#recipeContentsEditor').show();
                        jQuery('#recipeContents').removeAttr('disabled');
                        jQuery('#recipe_editor').show();
                    }
                    else {
                        jQuery('#recipeContentsEditor').hide();
                        jQuery('#recipeContents').attr('disabled', 'disabled');
                    }
                });
                jQuery('.expandableFormGroupTitle').click(function () {
                    toggle_display('recipe_editor');
                });
            });
            ]]>
        </script>
        <div id="modalYesNo" title="Confirmation" style="display: none;">
            You have chosen to abandon the customized recipe for this
            ${recipeType}. Are you sure that you want to do this?
        </div>
        <p>
            <input id="useOverrideRecipeCheckbox" type="checkbox" name="useOverrideRecipe" value="1"
            py:attrs="{'checked': useOverrideRecipe and 'checked' or None}" />
            <label for="useOverrideRecipeCheckbox">Use a customized recipe for this ${recipeType}</label>
        </p>
        <div class="expandableFormGroupTitle">
            <img id="recipe_editor_expander" class="noborder" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" />Custom Recipe
        </div>
        <div id="recipe_editor" py:attrs="{'style': (not useOverrideRecipe) and 'display:none;' or None}">
            <p><textarea id="recipeContents" name="recipeContents" wrap="off"
                py:attrs="{'disabled': (not useOverrideRecipe) and 'disabled' or None}"><![CDATA[${recipeContents}]]></textarea>
            </p>
        </div>
    </div>

</html>
