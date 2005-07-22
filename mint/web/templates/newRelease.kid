<?xml version='1.0' encoding='UTF-8'?>

<?python
from mint import releasetypes
title = "Create New Release"
?>

<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
    <div py:def="breadcrumb()" class="pad">
        You are here:
        <a href="#">rpath</a>
        <a href="http://${project.getHostname()}/">${project.getName()}</a>
        <a href="#">create a release</a>
    </div>

    <head/>
    <body onload="javascript:getTroveList(${project.getId()});">
        <td id="main" class="spanleft">
            <div class="pad">
                <h2>New Distribution Release</h2>
                <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
                <form method="post" action="editRelease" id="mainForm">

                    <table cellspacing="0" cellpadding="0" border="0" class="mainformhorizontal">
                        <tr>
                            <th><em class="required">Release name:</em></th>
                            <td><input type="text" name="releaseName" id="releaseName" value="${project.getName()}"/></td>
                        </tr>
                        <tr>
                            <th><em class="required">Distribution Trove:</em></th>
                            <td>

                                <p class="help">Please select the group or fileset trove that makes up your distribution</p>
                                <select name="trove" size="15" id="trove" >
                                    <option value="" id="pleaseWait">Loading trove list, please wait</option>
                                </select>
                            </td>
                        </tr>
                    </table>
                    <p>
                        <button id="submitButton" type="button" onclick="javascript:newProfileSubmit();">Submit</button>
                        <input type="hidden" value="${releasetypes.INSTALLABLE_ISO}" name="imageType" />
                        <input type="hidden" name="releaseId" value="-1" />
                    </p>
                </form>
            </div>
        </td>
        <td id="right" class="plain">
            <div class="pad" />
        </td>
    </body>
</html>
