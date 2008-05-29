<?xml version='1.0' encoding='UTF-8'?>
<?python
from urllib import quote
from conary import versions
import simplejson
from mint.helperfuncs import truncateForDisplay
from mint.web.templatesupport import injectVersion, projectText
from mint.grouptrove import KNOWN_COMPONENTS
from mint.packagecreator import drawField, isSelected, workingValue
lang = None;

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
        function changeFactory(){
            var sel = $('factoryHandle');

            //See that the only child of "chosen_factory" isn't the one we're looking for
            var chosen = $('chosen_factory');
            for (var child=0; child < chosen.childNodes.length; child++)
            {
                var elem = chosen.childNodes[child];
                if (! (elem instanceof Text))
                {
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
            }

            //Grab the selected factory and move it into "chosen_factory"
            var elem = $(sel.value);
            swapDOM(elem, null);
            appendChildNodes('chosen_factory', elem);
        }

        function shrinkToTextInput(e)
        {
            swapDOM(e, INPUT({name: e.name, id: e.id, value: e.value}, null));
            img = document.getElementById(e.id + "_expander");
            if(img != null)
            {
                img.src = img.src.replace('collapse', 'expand');
            }
        }

        function expandToTextArea(e)
        {
            swapDOM(e, TEXTAREA({name: e.name, id: e.id, rows: 5}, e.value));
            img = document.getElementById(e.id + "_expander");
            if(img != null)
            {
                img.src = img.src.replace('expand', 'collapse');
            }
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
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
            </div>

            <div id="middle">
            <p py:if="message" class="message" py:content="message"/>
            <h1>Package Creator - Confirm Package Details</h1>
            <h3>Step 2 of 3</h3>
            <form name="savePackage" method="post" action="savePackage" id="savePackage">
                <input type="hidden" name="sessionHandle" value="${sessionHandle}"/>
                <div class="formgroupTitle">Package Details</div>
                <div class="formgroup">
                  <label for="factoryHandle">Package Type</label>
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
                  <div class="clearleft">&nbsp;</div>
                  <!-- The factory interview -->
        <div py:def="drawLabel(fieldId, field)" py:strip="True">
          <label for="${fieldId}" id="${fieldId}_label">${field.descriptions[lang]}</label>
        </div>
        <div py:def="drawTextField(fieldId, field, possibles, prefilled)" py:strip="True">
${drawLabel(fieldId, field)}
          <?python
            value = workingValue(field, prefilled)
          ?>
          <div py:if="value is None or '\n' not in value" py:strip="True">
          <input type="text" id="${fieldId}" name="${field.name}"
              value="${workingValue(field, prefilled)}"/>
          <div style="cursor: pointer;" onclick="javascript:toggle_textarea(${simplejson.dumps(fieldId)})">
            <img id="${fieldId}_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" />
          </div>
          </div>
          <textarea py:if="value is not None and '\n' in workingValue(field, prefilled)" id="${fieldId}" name="${field.name}" rows="5">${workingValue(field, prefilled)}</textarea>
        </div>

        <div py:def="drawSelectField(fieldId, field, possibles, prefilled)" py:strip="True">
${drawLabel(fieldId, field)}
          <select name="${field.name}" id="${fieldId}" py:attrs="{'multiple': field.multiple and 'multiple' or None}">
            <option py:for="val in sorted(possibles)" id="${fieldId}_${val}" value="${val}" py:attrs="{'selected': isSelected(field, val, prefilled) and 'selected' or None}" py:content="val"/>
          </select>
        </div>

        <div py:def="drawCheckBoxes(fieldId, field, possibles, prefilled)" py:strip="True">
        <div class="fieldgroup">
         <div class="fieldgroup_row">
${drawLabel(fieldId, field)}
          <div class="formgroupItems">
          <div py:for="val in sorted(possibles)">
            <input id="${fieldId}_${val}" name="${field.name}" class="check fieldgroup_check" py:attrs="{'type': field.multiple and 'checkbox' or 'radio', 'checked': isSelected(field, val, prefilled) and 'checked' or None}" value="${val}"/>
            <label class="check_label" for="${fieldId}_${val}">${val}</label>
          </div>
          </div>
         </div>
         <div class="formgroupSeparator"/>
        </div>
        </div>

            <div id="chosen_factory" />

                  <!-- End factory interview -->
                </div>
                <p><input type="submit" id="submitButton_savePackage" value="Save Package" /></p>
            </form>

            <div style="display: none" id="factory_dumping_ground">
        <div py:for="(factoryIndex, (factoryHandle, factoryDef, values)) in enumerate(factories)" id="${factoryHandle}">
          <div py:for="field in factoryDef.getDataFields()" py:strip="True">
${drawField(factoryIndex, field, values, dict(unconstrained = drawTextField, medium_enumeration=drawSelectField, small_enumeration=drawCheckBoxes, large_enumeration=drawTextField))}
            <div class="clearleft">&nbsp;</div>
          </div>
        </div>
            </div>

            <h3 style="color:#FF7001;">Step 2: Confirm package details</h3>
            <p>The package creator has selected a list of possibile factories to use with the file that you uploaded, and has gathered as much information from it as possible.  Please choose the correct factory, and verify the information displayed.</p>

            </div>
        </div>
    </body>
</html>
