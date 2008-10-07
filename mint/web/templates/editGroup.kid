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
            
            <div id="innerpage">
                <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                
                <div id="right" class="side">
                    ${resourcePane()}
                </div>

                <div id="middle">
                    <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
                    <div class="page-title">Edit Group</div>
                    <p py:if="message" class="message" py:content="message"/>
                  
                    <h2>Group Details</h2>
                    <form method="post" action="editGroup2?id=${curGroupTrove.id}">
                    <table>
                    <tr id="editGTDropdown">
                        <td colspan="4">
                            <table class="mainformhorizontal">
                            <tr>
                                <td class="form-label">Name:</td>
                                <td class="form-label" width="100%">${curGroupTrove.recipeName}</td>
                            </tr>
                            <tr>
                                <td class="form-label">Version:</td>
                                <td><input type="text" value="${curGroupTrove.upstreamVersion}" name="version" /></td>
                            </tr>
                            <tr>
                                <td class="form-label">Description:</td>
                                <td><textarea rows="4" name="description" py:content="curGroupTrove.description"/></td>
                            </tr>
                            <tr>
                                <td colspan="2">
                                <div>
                                    <a onclick="javascript:toggle_display('componentGTDropdown');" href="#">Manage Components
                                        <img  id="componentGTDropdown_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" />
                                    </a>
                                </div>
                                </td>
                            </tr>
                            <tr id="componentGTDropdown" style="display:none;">
                                <td colspan="2">
                                    <table class="table-image-components">
                                    <tr>
                                        <td colspan="3">
                                            Remove the following components:<br/>
                                        </td>
                                    </tr>
                                    <?python
                                        removedComponents = curGroupTrove.listRemovedComponents()
                                    ?>
    
                                    <tr py:for="component, desc in sorted(KNOWN_COMPONENTS.iteritems())">
                                        <td>
                                            <input type="checkbox" class="check" name="components" value="${component}" 
                                                id="component_${component}" 
                                                py:attrs="{'checked': component in removedComponents and 'checked' or None}" /></td>
                                        <td class="label-offset">${component}</td>
                                        <td class="label-offset-wide"><label for="component_${component}">${desc}</label></td>
                                    </tr>
                                    </table>
                                </td>
                            </tr>
                            </table>
                        </td>
                    </tr>
                    <tr class="table-header-row">
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
    
                    <input class="button" name="action" type="submit" value="Save and Cook" style="font-weight: bold;" />
                    <input class="button" name="action" type="submit" value="Save Changes Only" />
                    <input class="button" name="action" type="submit" value="Delete This Group" />
                </form>
                    <p></p>
                    <h2>Step 1: Add Packages To Your Group</h2>
                    <p>You have a group. Now add packages to it from any
                    ${cfg.productName} ${projectText().lower()}. To add a package, search or browse for
                    the desired package, and click on its "Add to ${curGroupTrove.recipeName}"
                    link.</p>
        
                    <h2>Step 2: Cook Your Group</h2>
                    <p>"Cooking" the group assembles your chosen packages, resolves any
                    library dependencies, and creates a binary representation of the group
                    that is committed into your ${projectText().lower()}'s repository.</p>
        
                    <h2>Step 3: Create An Image</h2>
                    <p>Once your group has cooked successfully, create a
                    <a href="builds"><b>New Image</b></a> by selecting the name of
                    the group you just cooked. Select a version, architecture, and a
                    handful of other options, and you will have an installable
                    CD/DVD image in minutes!
                    </p>
                
                    
                </div><br class="clear" />
                <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>
</html>
