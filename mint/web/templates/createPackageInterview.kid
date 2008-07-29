<?xml version='1.0' encoding='UTF-8'?>
<?python
from urllib import quote
from conary import versions
import simplejson
from mint.helperfuncs import truncateForDisplay
from mint.web.templatesupport import injectVersion, projectText
from mint.grouptrove import KNOWN_COMPONENTS
from mint.packagecreator import drawField, isChecked, isSelected, effectiveValue, expandme
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
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu(readOnlyVersion=True)}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
            </div>

            <div id="middle">
            <p py:if="message" class="message" py:content="message"/>
            <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
            <h2>Package Creator - Confirm Package Details</h2>
            <h3>Step 2 of 3</h3>
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

            <h3 style="color:#FF7001;">Step 2: Confirm Package Details</h3>
            <p>Package Creator has selected a list of possible package type(s) to use with the archive that you uploaded, and has gathered as much information from it as possible.  Please confirm the correct package type, and verify the information displayed.</p>

            </div>
        </div>
    </body>
</html>
