<?xml version='1.0' encoding='UTF-8'?>

<?python
from mint import releasetypes
from mint.releasetypes import typeNames
from mint.data import RDT_STRING, RDT_BOOL, RDT_INT
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getNameForDisplay()}</a>
        <a href="${basePath}releases">Releases</a>
        <a href="#">${(isNewRelease and "Create New" or "Edit") + "Release"}</a>
    </div>
    <?python
        for var in ['releaseId', 'trove', 'releaseName']:
            kwargs[var] = kwargs.get(var, '')
    ?>

    <head>
        <title>${formatTitle((isNewRelease and "Create New" or "Edit") + "Release")}</title>
    </head>
    <?python jsonload = "javascript:getTroveList(" + str(project.getId()) + ")" ?>
    <body py:attrs="{'onload': isNewRelease and jsonload or None}">
        <div class="layout">
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
                        <input id="relname" name="name" type="text" value="${release.getName()}" /><br />

                        <label for="reldesc">Description (optional)</label>
                        <textarea id="reldesc" name="desc" type="text" py:content="release.getDesc()" /><br />

                    </div>

                    <div class="formgroupTitle">Release Contents<span id="baton"></span></div>
                    <div class="formgroup">
                        <label for="trove">Distribution Group</label>
                        <div py:strip="True" py:if="isNewRelease">
                            <select py:if="isNewRelease" onchange="javascript:onTroveChange(${project.getId()});" id="trove" name="trove">
                                <option value=""></option>
                            </select>
                        </div>
                        <div py:strip="True" py:if="not isNewRelease">
                            <span py:if="not isNewRelease" style="font-weight: bold;" id="trove" py:content="troveName" />
                            <input type="hidden" name="trove" value="${troveName}=${label.asString()}" />
                        </div>
                        <br />

                        <label for="arch">Target Architecture</label>
                        <div py:strip="True" py:if="isNewRelease">
                            <select onchange="javascript:onArchChange();" id="arch" name="arch" disabled="disabled">
                                <option value=""/>
                            </select>
                        </div>
                        <div py:strip="True" py:if="not isNewRelease">
                            <span style="font-weight: bold;" id="arch" py:content="not isNewRelease and arch or None" />
                            <input type="hidden" name="arch" value="${not isNewRelease and arch or None}" />
                        </div>
                        <br />

                        <label for="version">Group Version</label>
                        <div py:strip="True" py:if="isNewRelease">
                            <select onchange="javascript:onVersionChange();" id="version" name="version" disabled="disabled">
                                <option value="" />
                            </select>
                        </div>
                        <div py:strip="True" py:if="not isNewRelease">
                            <span py:if="not isNewRelease" style="font-weight: bold;" id="version" py:content="versionStr" />
                            <input type="hidden" name="version" value="${version + ' ' + flavor}" />
                        </div>
                        <br />
                    </div>

                    <?python
                        if isNewRelease:
                            imageTypes = [ releasetypes.INSTALLABLE_ISO ]
                    ?>
                    <div class="formgroupTitle">Image Types</div>
                    <div class="formgroup">
                        <div py:strip="True" py:for="key in self.cfg.visibleImageTypes">
                            <input class="reversed" id="imagetype_${key}" name="imagetype_${key}" value="${key}" type="checkbox" py:attrs="{'checked': key in imageTypes and 'checked' or None}" />
                            <label class="reversed" for="imagetype_${key}">${typeNames[key]}</label><br />
                        </div>
                    </div>

                    <?python
                        templates = release.getDisplayTemplates()
                        dataDict = release.getDataDict()
                    ?>
                    <div class="formgroupTitle" style="cursor: pointer;" onclick="javascript:toggle_display('advanced_settings');"><img id="advanced_settings_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" />Advanced Options</div>
                    <div id="advanced_settings" class="formgroup" style="display: none;">
                        <div py:strip="True" py:for="heading, template in templates">
                            <div class="formsubgroupTitle">${heading}</div>
                            <div class="formsubgroup">
                                <div py:strip="True" py:for="name, dataRow in sorted(template.items(), key = lambda x: x[1][0])">
                                    <div py:strip="True" py:if="(dataRow[0] == RDT_BOOL)">
                                        <input class="reversed" py:attrs="{'checked': 'checked' and dataDict[name] or None}" type="checkbox" id="${name}" name="${name}" value="1" />
                                        <label class="reversed" for="${name}">${dataRow[2]}</label>
                                    </div>
                                    <div py:strip="True" py:if="(dataRow[0] == RDT_INT) or (dataRow[0] == RDT_STRING)">
                                        <label for="${name}">${dataRow[2]}</label>
                                        <input type="text" name="${name}" id="${name}" value="${dataDict[name]}"/>
                                    </div>
                                    <br />
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
