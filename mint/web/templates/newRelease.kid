<?xml version='1.0' encoding='UTF-8'?>

<?python
from mint import releasetypes
from mint.releasetypes import visibleImageTypes, typeNames
title = "Create New Release"
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getNameForDisplay()}</a>
        <a href="${basePath}releases">Releases</a>
        <a href="#">Create a Release</a>
    </div>
    <?python
        for var in ['releaseId', 'trove', 'releaseName']:
            kwargs[var] = kwargs.get(var, '')
    ?>

    <head>
        <title>${formatTitle('Create a Release')}</title>
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

                <div py:if="errors" class="error">
                    <p>Release Creation Error${len(errors) > 1 and 's' or ''}</p>
                    <p py:for="error in errors" class="errormessage" py:content="error"/>
                </div>

                <form method="post" action="editRelease" id="mainForm">

                    <div class="formgroup">
                        <div class="formgroupTitle">Distribution Information</div>
                        <label for="relname">Name</label>
                        <!-- XXX: fix for edit pass -->
                        <input id="relname" name="relname" type="text" value="${isNewRelease and project.getName() or None}" /><br />

                        <!-- XXX: fix for edit pass -->
                        <label for="reldesc">Description (optional)</label>
                        <textarea id="reldesc" name="relname" type="text" py:content="isNewRelease and project.getName() + ' description here.' or None" /><br />

                    </div>

                    <div class="formgroup">
                    <div class="formgroupTitle">Choose your distribution group</div>
                        <label for="trove">Distribution Group</label>
                        <select id="trove" name="trove">
                            <option value="" id="pleaseWait">Please wait, loading troves...</option>
                        </select><br />

                        <label for="arch">Target Architecture</label>
                        <select id="arch" name="arch">
                            <option>TBD</option>
                        </select><br />

                        <label for="version">Group Version</label>
                        <select id="version" name="version">
                            <option>TBD</option>
                        </select><br />
                    </div>

                    <div class="formgroup">
                        <div class="formgroupTitle">Image Types</div>
                        <div py:strip="True" py:for="key in visibleImageTypes">
                            <input class="reversed" id="imagetype_${key}" name="imagetype_1" value="${key}" type="checkbox" py:attrs="{'checked': key in imageTypes and 'checked' or None}" />
                            <label class="reversed" for="imagetype_${key}">${typeNames[key]}</label><br />
                        </div>
                    </div>

                    <p>
                        <button id="submitButton" type="submit">${isNewRelease and "Create" or "Recreate"} Release</button>
                        <input type="hidden" name="releaseName" value="${project.getName()}" />
                        <!-- XXX: this needs to be different for edit pass -->
                        <input type="hidden" name="releaseId" value="-1" />
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
