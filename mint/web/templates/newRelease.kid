<?xml version='1.0' encoding='UTF-8'?>

<?python
from mint import releasetypes
title = "Create New Release"
?>

<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getName()}</a>
        <a href="${basePath}releases">Releases</a>
        <a href="#">Create a Release</a>
    </div>
    <?python
        for var in ['releaseId', 'imageType', 'trove', 'releaseName']:
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
                <h2>New Distribution Release</h2>
                <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
                <form method="post" action="editRelease" id="mainForm">

                    <table cellspacing="0" cellpadding="0" border="0" class="mainformhorizontal">
                        <tr py:if="errors"><td colspan="2">
                            <p py:if="errors" class="error">Release Creation Error${len(errors) > 1 and 's' or ''}</p>
                            <p py:for="error in errors" class="errormessage" py:content="error"/>
                        </td></tr>

                        <tr>
                            <th><em class="required">Distribution Group:</em></th>
                            <td>

                                <p class="help">Please select the group that defines your distribution</p>
                                <select name="trove" size="15" id="trove" >
                                    <option value="" id="pleaseWait">Loading group list, please wait</option>
                                </select>
                            </td>
                        </tr>
                        <tr py:if="False">
                            <th>Release Type:</th>
                            <td>
                                <select name="imageType">
                                    <option py:for="releaseType, releaseName in releasetypes.typeNames.items()"
                                            py:content="releaseName"
                                            py:attrs="{'value': releaseType}"/>
                                </select>
                            </td>
                            
                        </tr>
                    </table>
                    <p>
                        <button id="submitButton" type="submit">Submit</button>
                        <input py:if="True" type="hidden" name="imageType" value="${releasetypes.INSTALLABLE_ISO}" />
                        <input type="hidden" name="releaseName" value="${project.getName()}" />
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
