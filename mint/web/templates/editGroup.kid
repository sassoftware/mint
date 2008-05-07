<?xml version='1.0' encoding='UTF-8'?>
<?python
from urllib import quote
from conary import versions
from mint.helperfuncs import truncateForDisplay
from mint.web.templatesupport import injectVersion, projectText
from mint.grouptrove import KNOWN_COMPONENTS
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Edit Group: %s' % project.getNameForDisplay())}</title>
    </head>

    <body>
        <div id="layout">
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
                    <tr class="editGroupHeader">
                        <td colspan="4">
                            <div style="float:left">${curGroupTrove.recipeName} version ${curGroupTrove.upstreamVersion}</div>
                        </td>
                    </tr>
                    <tr id="editGTDropdown">
                        <td colspan="4">
                            <table>
                                <tr>
                                    <td>Version</td>
                                    <td colspan="3"><input type="text" value="${curGroupTrove.upstreamVersion}" name="version" style="width: 100%;" /></td>
                                </tr>
                                <tr>
                                    <td>Description</td>
                                    <td colspan="3"><textarea style="width: 100%;" rows="4" name="description" py:content="curGroupTrove.description"/></td>
                                </tr>
                                <tr style="margin-bottom: 6px;">
                                    <td colspan="4">
                                        <div style="float:right">
                                            <a onclick="javascript:toggle_display('componentGTDropdown');" href="#">Manage Components
                                                <img  id="componentGTDropdown_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" />
                                            </a>
                                        </div>
                                    </td>
                                </tr>
                                <tr id="componentGTDropdown" style="display:none;">
                                    <td colspan="2">
                                        <table style="padding: 0.75em; background: #eeeeee;">
                                            <tr>
                                                <td colspan="2">
                                                    Remove the following components
                                                </td>
                                            </tr>
                                            <?python
                                                removedComponents = curGroupTrove.listRemovedComponents()
                                            ?>

                                            <tr py:for="component, desc in sorted(KNOWN_COMPONENTS.iteritems())">
                                                <td>
                                                    <input type="checkbox" class="check" name="components" value="${component}" id="component_${component}"
                                                        py:attrs="{'checked': component in removedComponents and 'checked' or None}"
                                                        py:content="component" />
                                                </td>
                                                <td><label for="component_${component}">${desc}</label></td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr class="formgroupTitle" style="font-size: smaller;">
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

                <input name="action" type="submit" value="Save and Cook" style="font-weight: bold;" />
                <input name="action" type="submit" value="Save Changes Only" />
                <input name="action" type="submit" value="Delete This Group" />
            </form>

            <h3 style="color:#FF7001;">Step 1: Add Packages To Your Group</h3>
            <p>You have a group. Now add packages to it from any
            ${cfg.productName} ${projectText().lower()}. To add a package, search or browse for
            the desired package, and click on its "Add to ${curGroupTrove.recipeName}"
            link.</p>

            <h3 style="color:#FF7001;">Step 2: Cook Your Group</h3>
            <p>"Cooking" the group assembles your chosen packages, resolves any
            library dependencies, and creates a binary representation of the group
            that is committed into your ${projectText().lower()}'s repository.</p>

            <h3 style="color:#ff7001;">Step 3: Create An Image</h3>
            <p>Once your group has cooked successfully, create a
            <a href="builds"><b>New Image</b></a> by selecting the name of
            the group you just cooked. Select a version, architecture, and a
            handful of other options, and you will have an installable
            CD/DVD image in minutes!
            </p>
            </div>
        </div>
    </body>
</html>
