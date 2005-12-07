<?xml version='1.0' encoding='UTF-8'?>
<?python
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved

import string
from urllib import quote
from mint import userlevels

?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<?python
isOwner = (userLevel == userlevels.OWNER or auth.admin)
def pluralTroves(c):
    return c == 1 and "trove" or "troves"
?>


    <div py:def="breadcrumb" py:strip="True">
        <a href="${cfg.basePath}project/${project.getHostname()}/">${project.getName()}</a>
        <a href="#">Repository Browser</a>
    </div>

    <span py:def="adder(package, component='')" style="float: right;" py:if="groupTrove and package != groupTrove.recipeName">
        <?python
            if component:
                package += ":" + component
        ?>
        <a href="${groupProject.getUrl()}addGroupTrove?id=${groupTrove.id};trove=${quote(package)};referer=${quote(req.unparsed_uri)};projectName=${project.hostname}">
            Add to ${groupTrove.recipeName} <img style="border: none;" src="${cfg.staticPath}apps/mint/images/group.png" />
        </a>
    </span>

    <head>
        <title>${formatTitle('Repository Browser: %s'% project.getName())}</title>
    </head>
    <body>

        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()} 
                ${releasesMenu(project.getReleases(), isOwner, display="none")}
                ${commitsMenu(project.getCommits(), display="none")}
                ${browseMenu(display='none')}
                ${searchMenu(display='none')}
            </div>

        </td>
        <td id="main">
            <div class="pad">
                <h2>${project.getName()}<br />Repository Browser</h2>

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
                                <a href="troveInfo?t=${quote(package)}">${package}</a>
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
        </td>
        <td id="right" class="projects">
            ${projectsPane()}
            <div class="pad">
                ${groupTroveBuilder('block')}
            </div>
        </td>
    </body>
</html>
