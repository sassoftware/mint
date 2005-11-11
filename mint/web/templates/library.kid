<?xml version='1.0' encoding='UTF-8'?>
<?python
import time
from mint import searcher
from urllib import quote
from mint import userlevels
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="formatTitle(str)" py:strip="True" py:content="'%s - %s'%(str, cfg.productName)"/>

    <div py:def="userActions()" py:strip="True">
        <?python
            isOwner = (userLevel == userlevels.OWNER or auth.admin)
            isDeveloper = userLevel == userlevels.DEVELOPER

            secureProtocol = 'http'
            if auth.authorized:
                loginAction = "logout"
            else:
                loginAction = "processLogin"
                if cfg.SSL:
                    secureProtocol = "https"
        ?>

        <form method="post" action="${secureProtocol}://${cfg.secureHost}${cfg.basePath}$loginAction">
            <input py:if="loginAction == 'processLogin'" type="hidden" name="to" value="${quote(toUrl)}" />
            <table border="0" cellspacing="0" cellpadding="0" summary="layout">
                <tr>
                    ${logo()}
                    <td id="user" py:if="not auth.authorized">
                        <div class="pad">
                            <h4>not logged in | <a href="${secureProtocol}://${cfg.secureHost}${cfg.basePath}forgotPassword">Forgot Password</a></h4>
                            <div>
                                <input type="text" name="username" size="16" tabindex="1" /> <label>username</label><br />
                                <input type="password" name="password" size="16" tabindex="2" /> <label>password</label>
                            </div>
                        </div>
                    </td>
                    <td id="user" py:if="auth.authorized">
                        <div class="pad">
                            <h3>${auth.fullName}</h3>
                            <h4>${auth.username}</h4>
                            <div><a href="${secureProtocol}://${cfg.secureHost}${cfg.basePath}userSettings" class="arrows">View &#38; Edit My Account</a></div>
                            <div><a py:if="bool([True for x in projectList if x[1] in userlevels.WRITERS])" href="http://${SITE}uploadKey" class="arrows">Upload a Package Signing Key</a></div>
                            <div py:if='auth.admin'><a href="http://${SITE}administer" class="arrows">Administer</a></div>

                        </div>
                    </td>
                </tr>
                <tr>
                    ${topnav()}
                    <td id="log">
                        <div class="pad" py:if="not auth.authorized">
                            <button type="submit" tabindex="3">Login</button> |
                            <a href="http://${SITE}register" class="arrows">New Account</a>
                        </div>
                        <div class="pad" py:if="auth.authorized">
                            <button type="submit">Logout</button>
                        </div>
                    </td>
                </tr>
            </table>
        </form>
    </div>


    <thead py:def="columnTitles(columns = [])" py:strip="False">
        <tr>
            <th py:for="columnName in columns">${columnName}</th>
        </tr>
    </thead>

    <div py:def="resultRow(resultset = [])" py:strip="True">
        <td py:for="item in resultset">
            <a py:if="type(item) == tuple"
               py:content="item[1]"
               href="${item[0]}"/>
            <div py:if="type(item) != tuple"
                 py:strip="True"
                 py:content="item"/>
        </td>
    </div>

    <div id="browse" class="palette" py:def="browseMenu(display='block')" py:strip="False">
        <h3 onclick="javascript:toggle_display('browse_items');">
            <img id="browse_items_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_${display == 'block' and 'collapse' or 'expand'}.gif" border="0" />
            Browse
        </h3>
        <div id="browse_items" style="display: $display">
          <ul>
            <li><a href="http://${SITE}projects">All Projects</a></li>
            <li><a href="http://${SITE}projects?sortOrder=9">Most Active Projects</a></li>
            <li><a href="http://${SITE}projects?sortOrder=7">Most Popular Projects</a></li>
            <li py:if="auth.admin"><a href="http://${SITE}users">All Users</a></li>
          </ul>
        </div>
    </div>

    <div id="groupbuilder" class="palette" py:def="groupTroveBuilder(display='block')" py:strip="False" py:if="groupTrove">
        <script type="text/javascript" src="${cfg.staticPath}apps/MochiKit/MochiKit.js"/>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/groupbuilder.js"/>
        <script type="text/javascript">
            var XmlRpcUrl = '${cfg.basePath}xmlrpc';
            addLoadEvent(initLinkManager);
            addLoadEvent(initGroupTroveManager);
        </script>
        <h3>
            Group Builder 
        </h3>
        <div id="group_trove_builder_items" style="display: $display">
            <h4><a href="${groupProject.getUrl()}editGroup?id=${groupTrove.id}">Group in progress: ${groupTrove.recipeName}</a></h4>
            <table>
              <thead>
                <tr>
                    <th colspan="2">Name</th>
                    <th>Label</th>
                    <th>Delete</th>
                </tr>
              </thead>
              <tbody class="group-builder" id="groupbuilder-tbody">
                <tr></tr>
                <tr py:for="item in groupTrove.listTroves()" id="groupbuilder-item-${item['groupTroveItemId']}"><td></td><td>${item['trvName']}</td>
                    <td py:if="item['versionLock']">${item['trvVersion']}</td>
                    <td py:if="not item['versionLock']">${item['trvLabel']}</td>
                    <td><a href="${groupProject.getUrl()}deleteGroupTrove?id=${groupTrove.id};troveId=${item['groupTroveItemId']};referer=${quote(req.unparsed_uri)}">X</a></td>
                </tr>
                <tr id="groupbuilder-example" style="display:none">
                    <td id="groupbuilder-example group"><img src="/conary-static/apps/mint/images/group.png" style="border: none;" /></td>
                    <td id="groupbuilder-example name">Name</td>
                    <td id="groupbuilder-example version">Version</td>
                    <td id="groupbuilder-example delete"><a href="${groupProject.getUrl()}deleteGroupTrove?id=${groupTrove.id};troveId=TROVEID;referer=${quote(req.unparsed_uri)}">X</a></td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="groupcook">
                    <td colspan="3" style="text-align: center; padding: 1em;">
                        <a class="option" style="display: inline;" href="${groupProject.getUrl()}cookGroup?id=${groupTrove.id}">Cook This Group</a>
                    </td>
                </tr>
              </tfoot>
            </table>
        </div>
    </div>



    <div id="search" class="palette" py:def="searchMenu(selectType=None, display='block')" py:strip="False">
        <?python
if not selectType:
    selectType = session.get('searchType', 'Projects')
searchTypes = ['Projects', 'Packages']
if auth.authorized:
    searchTypes.append('Users')
        ?>
        <h3 onclick="javascript:toggle_display('search_items');">
            <img id="search_items_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_${display == 'block' and 'collapse' or 'expand'}.gif" border="0" />
            Search
        </h3>
          <div style="display: $display" id="search_items">
            <form action="http://${SITE}search" method="get">
            <p>
                <label>search type:</label><br/>
                <select name="type">
                    <option py:for="searchType in searchTypes"
                            py:attrs="{'value': searchType, 'selected': (selectType == searchType) and 'selected' or None}"
                            py:content="searchType"/>
                </select>
            </p>
            <p>
                <label>keyword(s):</label><br/>
                <input type="text" name="search" size="10" />
            </p>
            <p py:if="0">
                <label>last modified:</label>
                <br/>
                <select name="modified" id="searchModified">
                    <option py:for="i, option in enumerate(searcher.datehtml)" value="${i}">${option}</option>
                </select>
            </p>
            <p><button>Submit</button><br /><a py:if="0" href="#">Advanced Search</a></p>
            </form>
          </div>
    </div>

    <div py:def="recentReleasesMenu(releases, display='none')" py:strip="True">
      <div id="releases" class="palette" py:if="releases">
        <h3 onclick="javascript:toggle_display('recentRelease_items');">
            <img id="browse_items_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_${display == 'block' and 'collapse' or 'expand'}.gif" border="0" />
            Recently Published Releases
        </h3>
        <div id="recentRelease_items" style="display: $display">
          <ul>
            <li py:for="release in releases">
                <div class="releases_project"><a class="releases_project" href="http://${cfg.projectSiteHost}${cfg.basePath}project/${release[1]}">${release[0]}</a></div>
                <div class="releases_release">
                    <a href="http://${cfg.projectSiteHost}${cfg.basePath}project/${release[1]}/release?id=${release[2].getId()}">${release[2].getTroveName()}=${release[2].getTroveVersion().trailingRevision().asString()} (${release[2].getArch()})</a>
                </div>
            </li>
          </ul>
        </div>
      </div>
    </div>


    <table border="0" cellspacing="0" cellpadding="0"
           summary="layout" class="pager" style="margin-bottom: 1em;"
           py:def="navigation(urlbase, terms, count, limit, offset, footer=False)">
        <?python
            plural=""
            if count != 1:
                plural = "es"
        ?>
        <tr>
            <td>
                <form>
                    <span style="float: left;" py:if="count != 0 and not footer">
                        ${count} match${plural} found for <strong>${terms}</strong>;
                        Showing ${offset + 1}-${min(offset+limit, count)};
                    </span>
                    <span style="float: right;" py:if="count != 0">
                        Showing page ${offset/limit+1} of ${(count+limit-1)/limit}

                        <a href="${urlbase};limit=${limit};offset=${max(offset-limit, 0)}" py:if="offset != 0">
                            <img src="${cfg.staticPath}/apps/mint/images/prev.gif" alt="Previous" title="Previous Page" width="11" height="11" border="0" />
                        </a>
                        <img py:if="offset == 0" src="${cfg.staticPath}/apps/mint/images/prev_disabled.gif" alt="Previous" title="No previous results" width="11" height="11" border="0"/>
                        <a href="${urlbase};limit=${limit};offset=${offset+limit}" py:if="offset+limit &lt; count">
                            <img src="${cfg.staticPath}/apps/mint/images/next.gif" alt="Next" title="Next Page" width="11" height="11" border="0" />
                        </a>
                        <img py:if="offset+limit &gt;= count" src="${cfg.staticPath}/apps/mint/images/next_disabled.gif" alt="No next page" title="No subsequent results" width="11" height="11" border="0"/>
                    </span>
                </form>
            </td>
        </tr>
    </table>

    <div py:def="formatResults(resultset = [])" py:strip="True">
        <?python
            ##This function must be implemented in any derived class
            raise NotImplementedError
        ?>
        $resultRow(resultset)
    </div>

    <!-- results structure:
        [('id', 'data item 1' ... 'data item n'), ]
    -->
    <tbody py:def="searchResults(results=[])" py:strip="True">
        <tr py:for="i, resultset in enumerate(results)" class="${i % 2 and 'even' or 'odd'}">
            ${formatResults(resultset)}
        </tr>
    </tbody>

    <a py:def="legal(page, text)" py:strip="False" href="#"
        onclick="javascript:{window.open('${page}', 'legal',
         'height=500,width=500,menubar=no,scrollbars,status=no,toolbar=no', true); return false;}" 
        py:content="text"/>

</html>
