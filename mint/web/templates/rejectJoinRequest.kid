<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved 
-->
    <?python
        isOwner = (userLevel == userlevels.OWNER or auth.admin)
        isDeveloper = userLevel == userlevels.DEVELOPER
        memberList = project.getMembers()
    ?>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getNameForDisplay()}</a>
        <a href="${basePath}members">Members</a>
	<a href="${basePath}viewJoinRequest?userId=${userId}">View Join Request</a>
	<a href="#">Reject</a>
    </div>

    <head>
        <title>${formatTitle("Membership Request Rejection: %s"%project.getNameForDisplay())}</title>
    </head>
    <body>
        <td id="content">
            <table border="0" cellspacing="0" cellpadding="0" summary="layout" width="100%">
                <tr>
                    <td id="main">
                        <div class="pad">
			<form method="POST" action="processJoinRejection">
			<table border="0">
                            <tr><td><h2>Reject membership application for
                                        ${username} in ${project.getNameForDisplay(maxWordLen = 50)}</h2></td></tr>
                            <tr><td>Please edit any additional comments you wish to make</td></tr>
			    <tr><td><textarea name="comments" rows="10" cols="40"/></td></tr>
                            <input type="hidden" name="userId" value="${userId}"/>
                            <tr>
                                <td>
                                    <button type="submit">Submit</button>
                                </td>
                            </tr>
			</table>
			</form>
                        </div>
                    </td>
                </tr>
            </table>
            
        </td>
    </body>
</html>
