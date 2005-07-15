<?xml version='1.0' encoding='UTF-8'?>

<?python
from mint import releasetypes
title = "Create New Release"
?>

<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
    
    <head/>
    <body onload="javascript:getTroveList(${project.getId()});">
        <td id="content">
            <form method="post" action="editRelease" id="mainForm">

                <h2>New Distribution Release</h2>
                <table cellpadding="6">
                    <tr>
                        <td>Release name:</td>
                        <td><input type="text" name="releaseName" id="releaseName" value="${project.getName()}"/></td>
                        <td><span id="nameWarning" style="color: red;"></span></td>
                    </tr>
                </table>

                <h2>Distribution Trove</h2>
                <p>Please select the group or fileset trove that makes up your distribution:</p>
                <p id="troveWarning" style="color: red;"> </p>

                <select name="trove" size="15"
                         style="width: 50%;" id="trove" >
                    <option value="" id="pleaseWait">Loading trove list, please wait</option>
                </select>

                <h2 py:if='0'>Release Type</h2>
                <ul py:if='0' style="list-style-type: none; padding-left: 10px;">
                    <li py:for="releaseType, typeKey in sorted(releasetypes.ReleaseTypes.items())">
                        <input type="radio" name="imageType" value="${releaseType}" />
                        ${releasetypes.typeNames[typeKey]}
                    </li>
                </ul>

                <p>
                    <button id="submitButton" type="button" onclick="javascript:newReleaseSubmit();">Submit</button>
                    <input type="hidden" value="${releasetypes.INSTALLABLE_ISO}" name="imageType" />
                    <input type="hidden" name="releaseId" value="-1" />
                </p>
            </form>
        </td>
    </body>
</html>
