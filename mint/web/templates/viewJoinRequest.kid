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
        isOwner = userLevel == userlevels.OWNER or auth.admin
        memberList = project.getMembers()
    ?>

    <head>
        <title>${formatTitle('Member Settings: %s'%project.getNameForDisplay())}</title>
    </head>
    <body>
        <div class="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${groupTroveBuilder()}
            </div>
            <div id="middle">
                <h3><a href="http://$SITE/userInfo?id=${userId}">${username}</a>
                    requests to join: ${project.getNameForDisplay(maxWordLen = 50)}</h3>
                <form method="post" action="acceptJoinRequest">
                    <h4>Comments:</h4>
                    <blockquote>${comments}</blockquote>
                    <p>
                        <button class="img" id="makeOwner" type="submit" name="makeOwner" value="1"><img src="${cfg.staticPath}/apps/mint/images/make_owner_button.png" alt="Make Owner" /></button>
                        <button class="img" id="makeDevel" type="submit" name="makeDevel" value="1"><img src="${cfg.staticPath}/apps/mint/images/make_devel_button.png" alt="Make Developer" /></button>
                        <input type="hidden" name="userId" value="${userId}"/>
                        <button class="img" id="rejectRequest" type="submit" name="reject" value="1"><img src="${cfg.staticPath}/apps/mint/images/reject_request_button.png" alt="Reject Request" /></button>
                    </p>
                </form>
            </div>
        </div>
    </body>
</html>
