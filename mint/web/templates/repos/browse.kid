<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<?python # foo
title="Browse Repository"
import string
?>
<!--
 Copyright (c) 2005 rpath, Inc.

 This program is distributed under the terms of the Common Public License,
 version 1.0. A copy of this license should have been distributed with this
 source file in a file called LICENSE. If it is not present, the license
 is always available at http://www.opensource.org/licenses/cpl.php.

 This program is distributed in the hope that it will be useful, but
 without any waranty; without even the implied warranty of merchantability
 or fitness for a particular purpose. See the Common Public License for
 full details.
-->
    <head/>
    <body>
        <td id="left" class="side">
            <div class="pad">
                <div id="browse" class="palette">
                    <h3>Project Resources</h3>
                    <ul>
                        <li><a href="releases">Releases</a></li>

                        <li><a href="http://${project.getHostname()}/conary/browse"><strong>Repository</strong></a></li>
                        <li><a href="members">Project Members</a></li>
                        <li><a href="#">Mailing Lists</a></li>
                        <li><a href="#">Bug Tracking</a></li>
                    </ul>
                </div>
            </div>

        </td>
        <td id="main">
            <div class="pad">
                <h2>${project.getName()}<br />repository browser</h2>
               
                <span py:for="l in string.uppercase">
                    <a py:if="l != char" href="browse?char=${l}">${l}</a>
                    <span py:if="l == char">${l}</span> | 
                </span>
                <span>
                    <a py:if="l not in string.digits" href="browse?char=0" >0-9</a>
                    <span py:if="l in string.digits">0-9</span>
                </span>
                
                <?python
                    if char in string.digits:
                        char = "a digit"
                    else:
                        char = "'%c'" % char
                ?>


                <table border="0" cellspacing="0" cellpadding="0" summary="layout" class="pager">
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

                    <tr py:for="package in packages">
                        <td>${package}</td>
                        <td><a href="troveInfo?t=${package}" class="option">info</a></td>
                        <td><a href="#" class="option">files</a></td>
                    </tr>
                </table>
                
                <table border="0" cellspacing="0" cellpadding="0" summary="layout" class="pager">
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
