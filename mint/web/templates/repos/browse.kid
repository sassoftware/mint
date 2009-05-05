<?xml version='1.0' encoding='UTF-8'?>
<?python
# Copyright (c) 2005-2008 rPath, Inc.
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

    <head>
        <title>${formatTitle('Repository Browser: %s'% project.getNameForDisplay(maxWordLen = 50))}</title>
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
                    <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                    <div class="page-title">Repository Browser</div>
    
                    <div class="alpha-links">
                        <span py:for="l in string.uppercase" py:strip="True">
                          <span py:if="totals[l]">
                            <a class="pageSectionLink" href="browse?char=${l}" title="${totals[l]} ${pluralTroves(totals[l])}">${l}</a> </span>
                        </span>
                        <?python
                            total = 0
                            for x in string.digits:
                                total += totals[x]
                        ?>
                        <span>
                            <a class="pageSectionLink" py:if="l not in string.digits and total" href="browse?char=0" title="${total} ${pluralTroves(total)}">0-9</a>
                        </span>
                    </div>
                    
                    <?python
                        if char in string.digits:
                            char = "a digit"
                        else:
                            char = "'%c'" % char
                    ?>
    
                    <table class="results">
                    <tr>
                        <th colspan="3">Package Name</th>
                    </tr>
                    <tr py:for="i, package in enumerate(packages)">
                        <td class="browse-package">
                        <a href="troveInfo?t=${quote(package)}" title="${package}">${truncateForDisplay(package, maxWordLen = 42)}</a></td>
                    </tr>
                    </table>
                </div><br class="clear" />
                <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>
</html>
