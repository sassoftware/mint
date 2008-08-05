<?xml version='1.0' encoding='UTF-8'?>
<?python
import simplejson
from mint.helperfuncs import truncateForDisplay

if 'message' not in locals():
    message = None

?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Appliance Creator: %s' % project.getNameForDisplay())}</title>
    </head>

    <body>
        <div id="layout">
            <div id="left" class="side">
                Next steps go here
            </div>
            <div id="right" class="side">
                ${resourcePane()}
            </div>

            <div id="middle">
            <p py:if="message" class="message" py:content="message"/>
            <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
            <h2>Appliance Creator</h2>
            <form action="selectVersion" method="post" name="selectVersion">
            <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                <tr>
                  <th>Product Version</th>
                  <td py:if="versions">
                    ${versionSelection(dict(name='versionId'), versions, False)}
                  </td>
                  <td py:if="not versions">
                    ${prodVer} (${namespace})
                    <input type="hidden" name="sessionHandle" value="${sessionHandle}"/>
                  </td>
                </tr>
            </table>
            <p><input type="submit" id="submitButton" value="Begin Appliance"/></p>
            </form>
            </div>
        </div>
    </body>
</html>
