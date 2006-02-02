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
    <body onload="javascript:getTroveList(${project.getId()});">
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
            </div>
        </td>
        <td id="main">
            <div class="pad">
                <h2>${isNewRelease and "Create" or "Edit"} Release</h2>

                <form method="post" action="saveRelease" id="mainForm">

                    <div class="formgroupTitle">Distribution Information</div>
                    <div class="formgroup">
                        <label for="relname">Name</label>
                        <input id="relname" name="relname" type="text" value="${release.getName()}" /><br />

                        <label for="reldesc">Description (optional)</label>
                        <textarea id="reldesc" name="relname" type="text" py:content="release.getDesc()" /><br />

                    </div>

                    <div class="formgroupTitle">Choose your distribution group</div>
                    <div class="formgroup">
                        <label for="trove">Distribution Group</label>
                        <div py:strip="True" py:if="isNewRelease">
                            <select onchange="javascript:onTroveChange(${project.getId()});" id="trove" name="trove">
                                <option value="" id="pleaseWait">Please wait, loading troves...</option>
                            </select>
                        </div>
                        <div py:strip="True" py:if="not isNewRelease">
                            <span>${trove}</span>
                        </div>
                        <br />

                        <label for="arch">Target Architecture</label>
                        <select id="arch" name="arch" disabled="disabled">
                            <option value=""/>
                        </select><br />

                        <label for="version">Group Version</label>
                        <select id="version" name="version" disabled="disabled">
                            <option value="" />
                        </select><br />
                    </div>

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
                                        <input class="reversed" py:attr="{'checked': 'checked' and dataDict[name] or None}" type="checkbox" id="${name}" name="${name}" value="1" />
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
                </form>
            </div>
        </td>
        <td id="right" class="projects">
            ${projectsPane()}
            <div class="pad">
                ${groupTroveBuilder()}
            </div>
        </td>
    </body>
</html>
