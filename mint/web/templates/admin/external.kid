<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->

    <head>
        <title>${formatTitle('External Projects')}</title>
    </head>
    <body>
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
            <table py:if="projects" class="outboundMirrors">
                <tr style="font-weight: bold; background: #eeeeee;">
                    <td>External Projects</td>
                </tr>
                <tr py:for="project in projects">
                    <td><a href="editExternal?projectId=${project.id}">${project.name}</a></td>
                </tr>
            </table>
            <p py:if="projects">Click on the name of an external project to edit its settings.</p>
            <div py:if="not projects">
                No projects are currently external.
            </div>
            <p><a href="addExternal"><b>Add a New External Project</b></a></p>
        </div>
    </body>
</html>
