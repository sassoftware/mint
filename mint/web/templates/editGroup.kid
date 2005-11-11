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
            <p py:if="message" class="message" py:content="message"/>
            <div class="pad">
                <h1>Edit Group Trove</h1>
                <script type="text/javascript">
                  function dropdown()
                  {
                    var verelem = document.getElementById('version');
                    var state = verelem.style.display;
                    var newstate = null;
                    var img = document.getElementById('version_expander');
                    if (state == 'none') {
                        newstate = null;
                        img.src = img.src.replace('expand', 'collapse');
                    }
                    else {
                        newstate = 'none';
                        img.src = img.src.replace('collapse', 'expand');
                    }
                    verelem.style.display = newstate;
                    document.getElementById('description').style.display = newstate;
                    return false;
                  }
                </script>

                <form method="post" action="editGroup2?id=${curGroupTrove.id}">
                    <table id="groupTroveItems">
                        <tr><td colspan="4">
                            <div style="float:left">${curGroupTrove.recipeName} version ${curGroupTrove.upstreamVersion}</div>
                            <div style="float:right"><a onclick="javascript:dropdown();" href="#">Edit <img id="version_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" border="0"/></a></div>
                        </td></tr>
                        <tr style="display:none" id="version">
                            <td>Version</td>
                            <td colspan="3"><input type="text" value="${curGroupTrove.upstreamVersion}" name="version"/></td>
                        </tr>
                        <tr style="display:none" id="description">
                            <td>Description</td>
                            <td colspan="3"><textarea rows="10" cols="70" name="description" py:content="curGroupTrove.description"/></td>
                        </tr>

                        <tr style="background: #efefef;">
                            <td>Trove</td>
                            <td>Version</td>
                            <td>Lock Version</td>
                            <td>Delete</td>
                        </tr>

                        <tr py:for="t in curGroupTrove.listTroves()">
                            <td>${t['trvName']}</td>
                            <td>${t['trvVersion']}</td>
                            <td><input type="checkbox" name="${t['groupTroveItemId']}_versionLock" py:attrs="{'checked': t['versionLock'] and 'checked' or None}"/></td>
                            <td><a href="deleteGroupTrove?id=${curGroupTrove.getId()};troveId=${t['groupTroveItemId']};referer=${quote(req.unparsed_uri)}">X</a></td>
                        </tr>
                    </table>
                    <br/>
                    <button type="submit">Apply Changes</button>
                </form>
                <p><button onclick="javascript:window.location='cookGroup?id=${curGroupTrove.getId()}';">Cook This Group</button><br/>
                <button onclick="javascript:window.location='deleteGroup?id=${curGroupTrove.getId()}';">Delete This Group</button></p>
                <p><i>[FIXME: improve wording and instructions here]</i> To add items to this group trove, use the repository browser
                    for any project on the site.</p>
            </div>
        </td>
        <td id="right" class="projects">
            ${projectsPane()}
        </td>
    </body>
</html>
