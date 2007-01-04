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
def pluralTroves(c):
    return c == 1 and "trove" or "troves"
from mint.helperfuncs import truncateForDisplay
?>

    <span py:def="adder(package, component='')" style="float: right;"
        py:if="(groupTrove and not package.endswith(':source') and package != groupTrove.recipeName) or
               (rMakeBuild and not rMakeBuild.status and userLevel in userlevels.WRITERS and not component and not package.startswith('group-'))">
        <?python
            if component:
                package += ":" + component
            from mint.helperfuncs import truncateForDisplay
        ?>
        <a py:if="groupTrove" href="${groupProject.getUrl()}addGroupTrove?id=${groupTrove.id};trove=${quote(package)};referer=${quote(req.unparsed_uri)};projectName=${project.hostname}" title="Add to ${groupTrove.recipeName}">
            Add to ${truncateForDisplay(groupTrove.recipeName, maxWordLen = 10)}
        </a>
        <a py:if="rMakeBuild" href="${cfg.basePath}addrMakeTrove?trvName=${quote(package)};referer=${quote(req.unparsed_uri)};projectName=${project.hostname}" title="Add to ${rMakeBuild.title}">
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
                            ${adder(package)}
                            <a href="troveInfo?t=${quote(package)}" title="${package}">${truncateForDisplay(package, maxWordLen = 42)}</a>
                        </td>
                    </tr>
                </table>
            </div>
        </div>
    </body>
</html>
