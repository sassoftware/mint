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
    <?python
        isOwner = (userLevel == userlevels.OWNER or auth.admin)
        isDeveloper = userLevel == userlevels.DEVELOPER
        memberList = project.getMembers()
    ?>

    <head>
        <title>${formatTitle("Membership Request: %s"%project.getNameForDisplay())}</title>
    </head>
    <body>
        <div id="layout">
            <form method="POST" action="processJoinRequest">
                <table>
                    <tr><td><h2>Request membership in ${project.getNameForDisplay(maxWordLen = 50)}</h2></td></tr>
                    <tr><td>Please edit any additional comments you wish to make</td></tr>
                    <tr><td><textarea name="comments" rows="10" cols="40">$comments</textarea></td></tr>
                    <tr>
                        <td>
                            <button class="img" name="keepReq" value="1" type="submit">
                                <img src="${cfg.staticPath}apps/mint/images/submit_button.png" alt="Submit" />
                            </button>
                            <button class="img" name="keepReq" value="0" type="submit">
                                <img src="${cfg.staticPath}apps/mint/images/retract_button.png" alt="Retract Request" />
                            </button>
                        </td>
                    </tr>
                </table>
            </form>
        </div>
    </body>
</html>
