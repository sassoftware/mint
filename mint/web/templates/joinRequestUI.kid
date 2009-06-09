<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layoutUI.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle("Membership Request: %s"%project.getNameForDisplay())}</title>
    </head>
    <body>
        <div id="layout">
            <form method="POST" action="processJoinRequestUI">
                <table>
                    <tr><td><h2>Request membership in ${project.getNameForDisplay(maxWordLen = 50)}</h2></td></tr>
                    <tr><td>Please edit any additional comments you wish to make</td></tr>
                    <tr><td><textarea name="comments" rows="10" cols="40">$comments</textarea></td></tr>
                    <tr>
                        <td>
                            <input type="submit" name="keepReq" value="Submit" />
                            <input type="submit" name="keepReq" value="Retract Request" />
                        </td>
                    </tr>
                </table>
            </form>
        </div>
    </body>
</html>
