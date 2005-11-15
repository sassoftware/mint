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
        <title>${formatTitle('Edit Group: %s' % project.getName())}</title>
    </head>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getName()}</a>
        <a href="#">Edit Group</a>
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
                <h1>Edit Group</h1>
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
                            <div style="float:right"><a onclick="javascript:dropdown();" href="#">Edit 
                                <img id="version_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" border="0"/></a></div>
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

                <h3 style="color:#FF7001;">Step 1: Add Packages To Your Group</h3>
                <p>Now that you have a basic group, you can add additional packages to it. You can add any package from any ${cfg.productName} project.</p>

                <h3 style="color:#FF7001;">Step 2: Cook Your Group</h3>
                <p>"Cooking" the group assembles your chosen packages, resolves any library dependencies, and creates a representation of the group in
                binary form on your project's repository.</p>

                <h3 style="color:#ff7001;">Step 3: Create A Release</h3>
                <p>Once you have cooked a group successfully, create a <a href="releases"><b>New Release</b></a> and select the name of the group you just cooked.
                  Select a version, architecture, and a handful of other options, and you will have an installable ISO-9660 image in less than 5 minutes!
                </p>
            </div>
        </td>
        <td id="right" class="projects">
            ${projectsPane()}
        </td>
    </body>
</html>
