<?xml version='1.0' encoding='UTF-8'?>
<?python
from urllib import quote
from conary import versions
from mint.helperfuncs import truncateForDisplay
from mint.web.templatesupport import injectVersion
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Edit Group: %s' % project.getNameForDisplay())}</title>
    </head>

    <body>
        <div class="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
            </div>

            <div id="middle">
            <p py:if="message" class="message" py:content="message"/>
            <h1>Edit Group</h1>
            <form method="post" action="editGroup2?id=${curGroupTrove.id}">
                <table class="groupTroveItems">
                    <tr><td colspan="4">
                        <div style="float:left">${curGroupTrove.recipeName} version ${True and truncateForDisplay(curGroupTrove.upstreamVersion) or 'Latest'}</div>
                        <div style="float:right"><a onclick="javascript:toggle_display('editGTDropdown');" href="#">Edit
                            <img  id="editGTDropdown_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" /></a></div>
                    </td></tr>
                    <tr id="editGTDropdown" style="display:none;">
                        <td colspan="4">
                            <table style="padding: 0.75em; background: #eeeeee;">
                                <tr>
                                    <td>Version</td>
                                    <td colspan="3"><input type="text" value="${curGroupTrove.upstreamVersion}" name="version"/></td>
                                </tr>
                                <tr>
                                    <td>Description</td>
                                    <td colspan="3"><textarea rows="10" name="description" py:content="curGroupTrove.description"/></td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr style="background: #efefef;">
                        <td>Trove</td>
                        <td>Version</td>
                        <td>Lock Version</td>
                        <td>Delete</td>
                    </tr>

                    <tr py:for="t in curGroupTrove.listTroves()">
                        <td>${t['trvName']}</td>
                        <td py:if="t['versionLock']">
                            <a href="${t['baseUrl']}troveInfo?t=${quote(t['trvName'])};v=${quote(injectVersion(t['trvVersion']))}" title="${t['trvVersion']}">
                                ${versions.VersionFromString(t['trvVersion']).trailingRevision().asString()}
                            </a>
                        </td>
                        <td py:if="not t['versionLock']">
                            <a href="${t['baseUrl']}troveInfo?t=${quote(t['trvName'])}" title="${t['trvLabel']}">
                                Latest
                            </a>
                        </td>

                        <td><input type="checkbox" name="${t['groupTroveItemId']}_versionLock" py:attrs="{'checked': t['versionLock'] and 'checked' or None}"/></td>
                        <td><a href="deleteGroupTrove?id=${curGroupTrove.getId()};troveId=${t['groupTroveItemId']};referer=${quote(req.unparsed_uri)}">X</a></td>
                    </tr>
                </table>
                <p class="help">Hover your mouse over the trove version to see the fully-expanded Conary version.</p>
                <p><button class="img" type="submit">
                    <img src="${cfg.staticPath}/apps/mint/images/apply_changes_button.png" alt="Apply Changes" />
                </button></p>
            </form>

            <p>
                <button class="img" onclick="javascript:window.location='pickArch?id=${curGroupTrove.getId()}';" type="button">
                    <img src="${cfg.staticPath}/apps/mint/images/cook_this_group_button.png" alt="Cook This Group" />
                </button>
                <button class="img" onclick="javascript:window.location='deleteGroup?id=${curGroupTrove.getId()}';" type="button">
                    <img src="${cfg.staticPath}/apps/mint/images/delete_this_group_button.png" alt="Delete This Group" />
                </button>
            </p>

            <h3 style="color:#FF7001;">Step 1: Add Packages To Your Group</h3>
            <p>You have a group. Now add packages to it from any
            ${cfg.productName} project. To add a package, search or browse for
            the desired package, and click on its "Add to &lt;group-name&gt;"
            link.</p>

            <h3 style="color:#FF7001;">Step 2: Cook Your Group</h3>
            <p>"Cooking" the group assembles your chosen packages, resolves any
            library dependencies, and creates a binary representation of the group
            that is committed into your project's repository.</p>

            <h3 style="color:#ff7001;">Step 3: Create A Release</h3>
            <p>Once your group has cooked successfully, create a
            <a href="releases"><b>New Release</b></a> by selecting the name of
            the group you just cooked. Select a version, architecture, and a
            handful of other options, and you will have an installable ISO-9660
            image in minutes!
            </p>
            </div>
        </div>
    </body>
</html>
