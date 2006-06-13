<?xml version='1.0' encoding='UTF-8'?>
<?python
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved

import string
from urllib import quote
from mint import userlevels
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<?python
isOwner = (userLevel == userlevels.OWNER or auth.admin)
def pluralTroves(c):
    return c == 1 and "trove" or "troves"
from mint.helperfuncs import truncateForDisplay
?>

    <span py:def="adder(package, component='')" style="float: right;"
        py:if="(groupTrove and not groupTrove.troveInGroup(package) and not package.endswith(':source')) or
               (rMakeBuild and not rMakeBuild.status and userLevel in userlevels.WRITERS and not component)">
        <?python
            if component:
                package += ":" + component
            from mint.helperfuncs import truncateForDisplay
        ?>
        <a py:if="groupTrove and not groupTrove.troveInGroup(package) and not package.endswith(':source')" href="${groupProject.getUrl()}addGroupTrove?id=${groupTrove.id};trove=${quote(package)};referer=${quote(req.unparsed_uri)};projectName=${project.hostname}" title="Add to ${groupTrove.recipeName}">
            Add to ${truncateForDisplay(groupTrove.recipeName, maxWordLen = 10)}
        </a>
        <a py:if="rMakeBuild and not rMakeBuild.status and userLevel in userlevels.WRITERS and not component" 
           href="${cfg.basePath}addrMakeTrove?trvName=${quote(package.split(':source')[0])};referer=${quote(req.unparsed_uri)};projectName=${project.hostname}" title="Add to ${rMakeBuild.title}">
            Add to ${truncateForDisplay(rMakeBuild.title, maxWordLen = 10)}
        </a>
    </span>

    <head>
        <title>${formatTitle('Repository Browser: %s'% project.getNameForDisplay(maxWordLen = 50))}</title>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                ${releasesMenu(project.getReleases(), isOwner)}
                ${commitsMenu(project.getCommits())}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>

            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                <h2>Repository Browser</h2>

                <span py:for="l in string.uppercase" py:strip="True">
                    <span py:if="totals[l]"><a href="browse?char=${l}" title="${totals[l]} ${pluralTroves(totals[l])}">${l}</a> |</span>
                </span>
                <?python
                    total = 0
                    for x in string.digits:
                        total += totals[x]
                ?>
                <span>
                    <a py:if="l not in string.digits and total" href="browse?char=0" title="${total} ${pluralTroves(total)}">0-9</a>
                </span>

                <?python
                    if char in string.digits:
                        char = "a digit"
                    else:
                        char = "'%c'" % char
                ?>

                <table border="0" cellspacing="0" cellpadding="0" class="results">
                    <tr>

                        <th colspan="3">Package Name</th>
                    </tr>

                    <tr py:for="i, package in enumerate(packages)">
                        <td>
                            <div>
                              ${adder(package)}
                              <span>
                                <a href="troveInfo?t=${quote(package)}" title="${package}">${truncateForDisplay(package, maxWordLen = 42)}</a>
                                <a py:if="package in components" class="trove"
                                   href="javascript:toggle_display('components__${i}');"><img class="noborder" id="components__${i}_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif"/></a>
                              </span>
                            </div>
                            <div py:if="package in components" id="components__${i}"
                                 class="trovelist" style="display: none;">
                                <ul>
                                    <li py:for="component in components[package]">
                                      <span py:if="component != 'source'" py:strip="True">
                                        ${adder(package, component)}
                                      </span>
                                      <span>
                                        <a href="troveInfo?t=${quote(package)}:${quote(component)}">
                                            ${component}
                                        </a>
                                      </span>
                                    </li>
                                </ul>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
        </div>
    </body>
</html>
