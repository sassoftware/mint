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
        <title>${formatTitle('Member Settings: %s'%project.getNameForDisplay())}</title>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="middle">
                <h3><a href="http://$SITE/userInfo?id=${userId}">${username}</a>
                    requests to join: ${project.getNameForDisplay(maxWordLen = 50)}</h3>
                <form method="post" action="acceptJoinRequest">
                    <h4>Comments:</h4>
                    <blockquote>${comments}</blockquote>
                    <p>
                        <input type="submit" name="action" value="Make Owner" />
                        <input type="submit" name="action" value="Make Developer" />
                        <input type="submit" name="action" value="Reject Request" />
                        <input type="hidden" name="userId" value="${userId}"/>
                    </p>
                </form>
            </div>
        </div>
    </body>
</html>
