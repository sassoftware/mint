<?xml version='1.0' encoding='UTF-8'?>

<?python
from mint import buildtypes
from mint.buildtypes import typeNames, buildTypeExtra
from mint.web.templatesupport import shortTroveSpec
from mint.data import RDT_STRING, RDT_BOOL, RDT_INT, RDT_ENUM, RDT_TROVE

# troves that we can allow the user to select "None for this build"
allowNone = ['anaconda-custom', 'media-template']
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getNameForDisplay()}</a>
        <a href="${basePath}builds">Images</a>
        <a href="#">${(buildId and "Create New" or "Edit") + " Image"}</a>
    </div>
    <?python
        for var in ['buildId', 'buildName']:
            kwargs[var] = kwargs.get(var, '')
    ?>

    <div py:def="trovePicker(projectId, serverName, troveName, pickerId)" py:omit="True">
        <script type="text/javascript">
            addLoadEvent(function() {
                // boolean args are for "allow no groups" and "force all groups"
                picker = new TrovePicker(${projectId}, '${serverName}', '${troveName}', '${pickerId}', '${cfg.staticPath}', false, false);
                if(${buildId or 0})
                    handleBuildTypes("${arch}");
                else
                    handleBuildTypes(null);

                addPredefinedFilesystem('/', 0, 512, 'ext3');
            });
        </script>
    </div>

    <head>
        <title>${formatTitle((buildId and "Edit" or "Create New") + " Image")}</title>
        <script type="text/javascript" src="${cfg.staticPath}apps/yui/build/yahoo/yahoo-min.js" ></script>
        <script type="text/javascript" src="${cfg.staticPath}apps/yui/build/event/event-min.js" ></script>
        <script type="text/javascript" src="${cfg.staticPath}apps/yui/build/yahoo-dom-event/yahoo-dom-event.js" ></script>
        <script type="text/javascript" src="${cfg.staticPath}apps/yui/build/dragdrop/dragdrop-min.js" ></script>
        <script type="text/javascript" src="${cfg.staticPath}apps/yui/build/slider/slider.js" ></script>
        <script type="text/javascript" src="${cfg.staticPath}apps/yui/build/autocomplete/autocomplete-min.js"></script>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/trovepicker.js?v=${cacheFakeoutVersion}"/>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/filesystems.js?v=${cacheFakeoutVersion}"/>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            
            <div id="innerpage">
                <img id="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img id="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                <div id="right" class="side">
                    ${projectsPane()}
                    ${builderPane()}
                </div>

            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
                <div class="page-title">${buildId and "Edit" or "Create"} Image</div>

                <form method="post" action="saveBuild" id="mainForm">

                    <h2>Image Information</h2>
                    <div class="formgroup">
                        <table class="formgrouptable">
                        <tr>
                            <td class="form-label">Name: </td>
                            <td width="100%"><input id="relname" name="name" type="text" value="${name}" /></td>
                        </tr>
                        <tr>
                            <td class="form-label">Image&nbsp; Notes:<br/><span class="gray">(optional)</span></td>
                            <td><textarea id="reldesc" name="desc" type="text" py:content="desc" /></td>
                        </tr>
                        </table>
                    </div>

                    <h2>Image Type</h2>
                    <div class="formgroup">
                        <table class="formgrouptable">
                        <div py:strip="True" py:for="key in visibleTypes">
                            <tr>
                              <td>
                                <input id="buildtype_${key}" type="radio" name="buildtype" value="${key}" 
                                    onclick="javascript:onBuildTypeChange('formgroup_${key}');"
                                    py:attrs="{'checked': (key == buildType) and 'checked' or None}" /></td>
                              <td class="form-label-right">
                                <label for="buildtype_${key}" id="buildtype_${key}_label">${typeNames[key]}
                                    <div class="label-note" py:if="buildTypeExtra.has_key(key)">
                                    ${buildTypeExtra[key]}</div></label></td>
                            </tr>
                        </div>
                        </table>
                    </div>

                    <div class="expandableFormGroupTitle" onclick="javascript:toggle_display('advanced_settings');">
                        <img id="advanced_settings_expander" class="noborder" 
                            src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" />Advanced Options
                    </div>
                    <div id="advanced_settings" class="formgroup" style="display: none;">
                        <div py:strip="True" py:for="key, heading, template in templates">
                          <div id="formgroup_${key}" py:attrs="{'style' : key != buildType and 'display : none;' or None}">
                            <div class="formsubgroupTitle">${heading}</div>
                            <div class="formsubgroup">
                                <table class="formgrouptable">
                                <div py:strip="True" py:for="name, dataRow in sorted(template.items(), key = lambda x: x[1][0])">
                                    <?python
                                        if name in dataDict:
                                            dataValue = dataDict[name]
                                        else:
                                            dataValue = dataRow[1]
                                    ?>
                                    <div py:strip="True" py:if="(dataRow[0] == RDT_BOOL)">
                                      <tr>
                                        <td class="checkbox">
                                            <input type="checkbox" py:attrs="{'checked': 'checked' and dataValue or None,
                                                'disabled' : key != buildType and 'disabled' or None}" 
                                                name="${name}" value="1" id="${name}"/></td>
                                        <td class="form-label-right"><label for="${name}">${dataRow[2]}</label></td>
                                      </tr>
                                    </div>
                                    <div py:strip="True" py:if="(dataRow[0] == RDT_INT) or (dataRow[0] == RDT_STRING)">
                                      <tr>
                                        <td colspan="2">
                                        <span class="form-label-text">${dataRow[2]}:</span><br />
                                        <input type="text" name="${name}" id="${name}" value="${dataValue}"
                                            py:attrs="{'disabled' : key != buildType and 'disabled' or None}"/></td>
                                      </tr>
                                    </div>
                                    <div py:strip="True" py:if="(dataRow[0] == RDT_ENUM)">
                                      <tr>
                                        <td colspan="2">
                                        ${dataRow[2]}:
                                        <select name="${name}" id="${name}" py:attrs="{'disabled' : key != buildType and 'disabled' or None}">
                                            <option py:for="prompt, val in sorted(dataRow[3].iteritems())"
                                                py:content="prompt" value="${val}"
                                                py:attrs="{'selected' : val == dataValue and 'selected' or None}"/>
                                        </select></td>
                                      </tr>
                                    </div>
                                    <div py:strip="True" py:if="(dataRow[0] == RDT_TROVE)">
                                      <tr>
                                        <td colspan="2">
                                        <span class="form-label-text">Package for <span class="dark-blue">${dataRow[2]}</span> in this build:</span>
                                        <div id="${name}_${key}">
                                            <span py:if="not buildId or not dataValue">Use latest on branch</span>
                                            <span py:if="buildId and dataValue and dataValue != 'NONE'">${shortTroveSpec(dataValue)}</span>
                                            <span py:if="buildId and dataValue and dataValue == 'NONE'">No ${dataRow[2]} will be used for this build.</span>
                                            &nbsp;( <a class="dark-blue" style="cursor:pointer;" onclick="new TrovePicker(${project.id},
                                                '${project.getLabel().split('@')[0]}',
                                                '${name}', '${name}_${key}', '${cfg.staticPath}', ${int(name in allowNone)});">change )</a>
                                            <input py:if="buildId and dataValue" type="hidden" name="${name.replace('-', '_') + 'Spec'}" value="${dataValue}" />
                                        </div></td>
                                      </tr>
                                    </div>
                                </div>
                                </table>
                            </div>
                            </div>
                        </div>
                    </div>

                    <h2>Image Contents<span id="baton"></span></h2>
                    <div class="formgroup">
                        <div id="distTrove" py:if="not buildId">${trovePicker(project.id, project.getLabel().split('@')[0], '', 'distTrove')}</div>
                        <div py:if="buildId" style="margin: 4px;">
                            ${troveName}=${str(version)} [${str(flavor).replace(",", ", ")}]
                            <input type="hidden" name="distTroveSpec" value="${troveName}=${version.freeze()}[${str(flavor)}]" />
                        </div>
                    </div>


                    <?python # disable filesystem editor until RBL-1911 is resolved ?>
                    <div py:if="False" class="formgroupTitle" style="margin-top: 24px;">Filesystems</div>
                    <div py:if="False" class="formgroup" style="text-align: center;">
                        <table class="fsEditorTable" style="padding-left: 8px;" >
                            <thead><tr>
                                <td>Mount Point</td>
                                <td>Free Space (MiB)</td>
                                <td>Type</td>
                                <td></td>
                            </tr></thead>

                            <tbody id="fsEditorBody">
                            </tbody>
                        </table>
                        <button type="button" onclick="javascript:addFilesystem();">Add</button>
                    </div>

                    <p>
                        <input type="submit" id="submitButton" name="action"
                               value="${buildId and 'Recreate' or 'Create'} Image"
                               py:attrs="{'disabled': not buildId and 'disabled' or None}" />
                        <input type="submit" name="action" value="Cancel" />
                    </p>
                    <input type="hidden" name="buildId" value="${buildId and buildId or 0}" />
                </form>
            </div><br class="clear"/>
                <img id="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img id="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>
</html>
