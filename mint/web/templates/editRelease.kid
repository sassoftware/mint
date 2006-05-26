<?xml version='1.0' encoding='UTF-8'?>

<?python
from mint import releasetypes
from mint.releasetypes import typeNames
from mint.data import RDT_STRING, RDT_BOOL, RDT_INT, RDT_ENUM
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getNameForDisplay()}</a>
        <a href="${basePath}releases">Releases</a>
        <a href="#">${(isNewRelease and "Create New" or "Edit") + " Release"}</a>
    </div>
    <?python
        for var in ['releaseId', 'trove', 'releaseName']:
            kwargs[var] = kwargs.get(var, '')
    ?>

    <head>
        <title>${formatTitle((isNewRelease and "Create New" or "Edit") + " Release")}</title>
    </head>
    <?python
        if isNewRelease:
            jsonload = "javascript:getTroveList(" + str(project.getId()) + ");"
        else:
            jsonload = "javascript:handleReleaseTypes(\""+ arch +"\");"
    ?>
    <body py:attrs="{'onload': jsonload }">
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="right" class="side">
                ${projectsPane()}
                ${groupTroveBuilder()}
            </div>

            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
                <h2>${isNewRelease and "Create" or "Edit"} Release</h2>

                <form method="post" action="saveRelease" id="mainForm">

                    <div class="formgroupTitle">Distribution Information</div>
                    <div class="formgroup">
                        <label for="relname">Name</label>
                        <input id="relname" name="name" type="text" value="${release.getName()}" /><div class="clearleft">&nbsp;</div>

                        <label for="reldesc">Description (optional)</label>
                        <textarea id="reldesc" name="desc" type="text" py:content="release.getDesc()" /><div class="clearleft">&nbsp;</div>

                    </div>

                    <div class="formgroupTitle">Release Contents<span id="baton"></span></div>
                    <div class="formgroup">
                        <label for="trove">Distribution Group</label>
                        <div py:strip="True" py:if="isNewRelease">
                            <select py:if="isNewRelease" onchange="javascript:onTroveChange(${project.getId()});" id="trove" name="trove">
                                <option value=""></option>
                            </select>
                            <img src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" id="nameSpinner" style="float: right;"/>
                        </div>
                        <div py:strip="True" py:if="not isNewRelease">
                            <input type="text" name="troveDisplay" id="trove" value="${troveName}" disabled="disabled" />
                            <input type="hidden" name="trove" value="${troveName}=${label.asString()}" />
                            <img src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" id="nameSpinner" style="float: right;"/>
                        </div>
                        <div class="clearleft">&nbsp;</div>

                        <label for="arch">Target Architecture</label>
                        <div py:strip="True" py:if="isNewRelease">
                            <select onchange="javascript:onArchChange();" id="arch" name="arch" disabled="disabled">
                                <option value=""/>
                            </select>
                            <img src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" id="archSpinner" style="float: right;"/>
                        </div>
                        <div py:strip="True" py:if="not isNewRelease">
                            <input type="text" id="arch" name="archDisplay" value="${not isNewRelease and arch or None}" disabled="disabled" />
                            <input type="hidden" name="arch" value="${not isNewRelease and arch or None}" />
                            <img src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" id="archSpinner" style="float: right;"/>
                        </div>
                        <div class="clearleft">&nbsp;</div>

                        <label for="version">Group Version</label>
                        <div py:strip="True" py:if="isNewRelease">
                            <select onchange="javascript:onVersionChange();" id="version" name="version" disabled="disabled">
                                <option value="" />
                            </select>
                        </div>
                        <div py:strip="True" py:if="not isNewRelease">
                            <input type="text" id="version" name="versionDisp" value="${versionStr}" disabled="disabled" />
                            <input type="hidden" name="version" value="${version + ' ' + flavor}" />
                        </div>
                        <div class="clearleft">&nbsp;</div>
                    </div>

                    <div class="formgroupTitle">Image Types</div>
                    <div class="formgroup">
                        <div py:strip="True" py:for="key in self.cfg.visibleImageTypes">
                            <input class="reversed" id="imagetype_${key}" name="imagetype" value="${key}" onclick="javascript:onImageChange('formgroup_${key}');" type="radio" py:attrs="{'checked': key in imageTypes and 'checked' or None}" />
                            <label class="reversed" for="imagetype_${key}">${typeNames[key]}</label><div class="clearleft">&nbsp;</div>
                        </div>
                    </div>

                    <?python
                        templates = release.getDisplayTemplates()
                        dataDict = release.getDataDict()
                        defaultTemplate = release.imageTypes and release.imageTypes[0] or 1
                    ?>
                    <div class="formgroupTitle" style="cursor: pointer;" onclick="javascript:toggle_display('advanced_settings');"><img id="advanced_settings_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" />Advanced Options</div>
                    <div id="advanced_settings" class="formgroup" style="display: none;">
                        <div py:strip="True" py:for="key, heading, template in templates">
                            <div class="formsubgroupcontainer" id="formgroup_${key}" py:attrs="{'style' : key != defaultTemplate and 'display : none;' or None}">
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
                                        <input class="reversed" py:attrs="{'checked': 'checked' and dataValue or None, 'disabled' : key != defaultTemplate and 'disabled' or None}" type="checkbox" name="${name}" value="1" id="${name}"/>
                                        <label class="reversed" for="${name}">${dataRow[2]}</label>
                                    </div>
                                    <div py:strip="True" py:if="(dataRow[0] == RDT_INT) or (dataRow[0] == RDT_STRING)">
                                        <label for="${name}">${dataRow[2]}</label>

                                        <input type="text" name="${name}" id="${name}" value="${dataValue}" py:attrs="{'disabled' : key != defaultTemplate and 'disabled' or None}"/>
                                    </div>
                                    <div py:strip="True" py:if="(dataRow[0] == RDT_ENUM)">
                                        <label for="${name}">${dataRow[2]}</label>
                                        <select name="${name}" id="${name}" py:attrs="{'disabled' : key != defaultTemplate and 'disabled' or None}">
                                            <option py:for="prompt, val in sorted(dataRow[3].iteritems())" py:content="prompt" value="${val}" py:attrs="{'selected' : val == dataRow[1] and 'selected' or None}"/>
                                        </select>
                                    </div>
                                    <div class="clearleft">&nbsp;</div>
                                </div>
                            </div>
                            </div>
                        </div>
                    </div>

                    <p>
                        <button id="submitButton" type="submit" py:attrs="{'disabled': isNewRelease and 'disabled' or None}">${isNewRelease and "Create" or "Recreate"} Release</button>
                    </p>
                    <input type="hidden" name="releaseId" value="${release.getId()}" />
                </form>
            </div>
        </div>
    </body>
</html>
