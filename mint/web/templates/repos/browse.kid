<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', '../project.kid'">
<?python
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved

import string
?>

    <div py:def="breadcrumb" py:strip="True">
        <a href="/">${project.getName()}</a>
        <a href="#">Repository Browser</a>
    </div>

    <head>
        <title>${formatTitle('Repository Browser: %s'% project.getName())}</title>
    </head>
    <body>
        <td id="left" class="side">
            <div class="pad">
               ${projectResourcesMenu()} 
            </div>

        </td>
        <td id="main">
            <div class="pad">
                <h2>${project.getName()}<br />repository browser</h2>

                <span py:for="l in string.uppercase">
                    <a py:if="l != char and totals[l]" href="browse?char=${l}">${l}</a>
                    <span py:if="l == char or not totals[l]">${l}</span> | 
                </span>
                <?python
                    total = 0
                    for x in string.digits:
                        total += totals[x]
                ?>
                <span>
                    <a py:if="l not in string.digits and total" href="browse?char=0" >0-9</a>
                    <span py:if="l in string.digits or not total">0-9</span>
                </span>
                
                <?python
                    if char in string.digits:
                        char = "a digit"
                    else:
                        char = "'%c'" % char
                ?>


                <table border="0" cellspacing="0" cellpadding="0" summary="layout" class="pager" py:if="0">
                    <tr>
                        <td>
                            <form>
                                Displaying troves 
                                <select name="resultsPager">
                                    <option value="" selected="selected">1-6</option>
                                </select>
                            </form>
                        </td>
                        <td>
                            <div align="right">

                                <a href="#">Previous Page</a>
                                <a href="#">Next Page</a>
                            </div>
                        </td>
                    </tr>
                </table>
                
                <table border="0" cellspacing="0" cellpadding="0" class="results">
                    <tr>

                        <th colspan="3">Trove Name</th>
                    </tr>

                    <tr py:for="i, package in enumerate(packages)">
                        <td>
                            <a href="troveInfo?t=${package}">${package}</a>
                            <a py:if="package in components" class="trove"
                               href="javascript:toggle_display('components__${i}');"><img border="0" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif"/></a>
                            <div py:if="package in components" id="components__${i}"
                                 class="trovelist" style="display: none;">
                                <ul>
                                    <li py:for="component in components[package]">
                                        <a href="troveInfo?t=${package}:${component}">
                                            ${component}
                                        </a>
                                    </li>
                                </ul>
                            </div>
                        </td>
                    </tr>
                </table>
                
                <table border="0" cellspacing="0" cellpadding="0" summary="layout" class="pager" py:if="0">
                    <tr>

                        <td>
                            <form>
                            Displaying troves
                            <select name="resultsPager">
                                <option value="" selected="selected">1-6</option>
                            </select>
                            </form>
                        </td>

                        <td>
                            <div align="right">
                                <a href="#">Previous Page</a>
                                <a href="#">Next Page</a>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
        </td>
        ${projectsPane()}
    </body>
</html>
