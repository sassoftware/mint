<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle("Membership Request Rejection: %s"%project.getNameForDisplay())}</title>
    </head>
    <body>
        <div id="layout">
            <form method="POST" action="processJoinRejection">
                <table>
                    <tr><td><h2>Reject membership application for
                                ${username} in ${project.getNameForDisplay(maxWordLen = 50)}</h2></td></tr>
                    <tr><td>Please edit any additional comments you wish to make</td></tr>
                    <tr><td><textarea name="comments" rows="10" cols="40"/></td></tr>
                    <input type="hidden" name="userId" value="${userId}"/>
                    <tr>
                        <td>
                            <button class="img" type="submit"><img src="${cfg.staticPath}apps/mint/images/submit_button.png" alt="Submit" /></button>
                        </td>
                    </tr>
                </table>
            </form>
        </div>
    </body>
</html>
