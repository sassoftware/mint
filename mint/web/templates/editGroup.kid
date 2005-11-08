<?xml version='1.0' encoding='UTF-8'?>
<?python
from urllib import quote
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid', 'project.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Edit Group Trove: %s' % project.getName())}</title>
    </head>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getName()}</a>
        <a href="#">Edit Group Trove</a>
    </div>

    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
                ${browseMenu(display='none')}
                ${searchMenu(display='none')}
            </div>
        </td>
        <td id="main">
            <div class="pad">
                <h1>Edit Group Trove</h1>

                <form method="post" action="editGroup2">
                    <table id="groupTroveItems">
                        <tr><td colspan="4">
                            ${curGroupTrove.recipeName} version ${curGroupTrove.upstreamVersion}
                        </td></tr>

                        <tr style="background: #efefef;">
                            <td>Trove</td>
                            <td>Version</td>
                            <td>Lock Version</td>
                            <td>Delete</td>
                        </tr>

                        <tr py:for="t in curGroupTrove.listTroves()">
                            <td>${t['trvName']}</td>
                            <td>${t['trvVersion']}</td>
                            <td><input type="checkbox" name="${t['groupTroveItemId']}_locked" /></td>
                            <td><a href="deleteGroupTrove?id=${curGroupTrove.getId()};troveId=${t['groupTroveItemId']};referer=${quote(req.unparsed_uri)}">X</a></td>
                        </tr>
                    </table>
                    <br/>
                    <button type="submit">Apply Changes</button>
                    <button type="submit">Cook This Group</button>
                </form>
            </div>
        </td>
        <td id="right" class="projects">
            ${projectsPane()}
        </td>
    </body>
</html>
