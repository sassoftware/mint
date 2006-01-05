<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->

    <?python
        isOwner = userLevel == userlevels.OWNER or auth.admin
        memberList = project.getMembers()
    ?>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getNameForDisplay()}</a>
        <a href="${basePath}members">Members</a>
	<a href="#">View Join Request</a>
    </div>

    <head>
        <title>${formatTitle('Member Settings: %s'%project.getNameForDisplay())}</title>
    </head>
    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
            </div>

        </td>
        <td id="main">
	<div class="pad">
            <h3><a href="http://$SITE/userInfo?id=${userId}">${username}</a>
                requests to join: ${project.getNameForDisplay(maxWordLen = 50)}</h3>
            <form method="post" action="acceptJoinRequest">
            <table>
                <tr><th>Comments:</th></tr>
                <tr><td>${comments}</td></tr>
                <tr><td>
                    <button type="submit" name="makeOwner" value="1" onclick="window.parent.hide_popup('joinReqBox', true);">Owner</button>
                    <button type="submit" name="makeDevel" value="1" onclick="window.parent.hide_popup('joinReqBox', true);">Developer</button>
                    <input type="hidden" name="userId" value="${userId}"/>
                    <button type="submit" name="reject" value="1" onclick="window.parent.hide_popup('joinReqBox', false);">Reject</button>
                </td></tr>
            </table>
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
