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
                ${projectResourcesMenu(readOnlyVersion=True)}
            </div>
            <div id="right" class="side">
                ${projectsPane()}
                ${builderPane()}
            </div>

            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
                <h2>${buildId and "Edit" or "Create"} Image</h2>

                <form method="post" action="saveBuild" id="mainForm">

                    <div class="formgroupTitle">Image Information</div>
                    <div class="formgroup">
                        <label for="relname">Name</label>
                        <input id="relname" name="name" type="text" value="${name}" /><div class="clearleft">&nbsp;</div>

                        <label for="reldesc">Image Notes (optional)</label>
                        <textarea id="reldesc" name="desc" type="text" py:content="desc" /><div class="clearleft">&nbsp;</div>

                    </div>

                    <div class="formgroupTitle">Image Type</div>
                    <div class="formgroup">
                        <div py:strip="True" py:for="key in visibleTypes">
                            <input class="reversed" id="buildtype_${key}"
                                name="buildtype" value="${key}" 
                                onclick="javascript:onBuildTypeChange('formgroup_${key}');"
                                type="radio" py:attrs="{'checked': (key == buildType) and 'checked' or None}" />
                            <label class="reversed" for="buildtype_${key}" id="buildtype_${key}_label">${typeNames[key]}
                                <span py:if="buildTypeExtra.has_key(key)" class="clearleft" style="font-size: smaller;"><br />${buildTypeExtra[key]}</span></label>
                            <div class="clearleft">&nbsp;</div>
                        </div>
                    </div>

                    <div class="formgroupTitle" style="cursor: pointer;" onclick="javascript:toggle_display('advanced_settings');">
                        <img id="advanced_settings_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" />Advanced Options
                    </div>
                    <div id="advanced_settings" class="formgroup" style="display: none;">
                        <div py:strip="True" py:for="key, heading, template in templates">
                            <div class="formsubgroupcontainer" id="formgroup_${key}" py:attrs="{'style' : key != buildType and 'display : none;' or None}">
                            <div class="formsubgroupTitle">${heading}</div>
                            <div class="formsubgroup">
                                <div py:strip="True" py:for="name, dataRow in sorted(template.items(), key = lambda x: x[1][0])">
                                    <?python
                                        if name in dataDict:
                                            dataValue = dataDict[name]
                                        else:
                                            dataValue = dataRow[1]
                                    ?>
                                    <div py:strip="True" py:if="(dataRow[0] == RDT_BOOL)">
                                        <input class="reversed" py:attrs="{'checked': 'checked' and dataValue or None,
                                                                           'disabled' : key != buildType and 'disabled' or None}" 
                                            type="checkbox" name="${name}" value="1" id="${name}"/>
                                        <label class="reversed" for="${name}">${dataRow[2]}</label>
                                    </div>
                                    <div py:strip="True" py:if="(dataRow[0] == RDT_INT) or (dataRow[0] == RDT_STRING)">
                                        <label for="${name}">${dataRow[2]}</label>
                                        <input type="text" name="${name}" id="${name}" value="${dataValue}"
                                            py:attrs="{'disabled' : key != buildType and 'disabled' or None}"/>
                                    </div>
                                    <div py:strip="True" py:if="(dataRow[0] == RDT_ENUM)">
                                        <label for="${name}">${dataRow[2]}</label>
                                        <select name="${name}" id="${name}" py:attrs="{'disabled' : key != buildType and 'disabled' or None}">
                                            <option py:for="prompt, val in sorted(dataRow[3].iteritems())"
                                                py:content="prompt" value="${val}"
                                                py:attrs="{'selected' : val == dataValue and 'selected' or None}"/>
                                        </select>
                                    </div>
                                    <div py:strip="True" py:if="(dataRow[0] == RDT_TROVE)">
                                        <label for="${name}_${key}">${dataRow[2]}</label>
                                        <div id="${name}_${key}">
                                            <span py:if="not buildId or not dataValue">Defaults to latest on branch</span>
                                            <span py:if="buildId and dataValue">${shortTroveSpec(dataValue)}</span>
                                            (<a onclick="new TrovePicker(${project.id},
                                                '${project.getLabel().split('@')[0]}',
                                                '${name}', '${name}_${key}', '${cfg.staticPath}', ${int(name in allowNone)});">change)</a>
                                            <input py:if="buildId and dataValue" type="hidden" name="${name.replace('-', '_') + 'Spec'}" value="${dataValue}" />
                                        </div>
                                    </div>
                                    <div class="clearleft">&nbsp;</div>
                                </div>
                            </div>
                            </div>
                        </div>
                    </div>
                    <br/>

                    <div class="formgroupTitle">Image Contents<span id="baton"></span></div>
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
            </div>
        </div>
    </body>
</html>
