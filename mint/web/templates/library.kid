<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import searcher
from urllib import quote
from mint import userlevels
from mint import maintenance
from mint.helperfuncs import truncateForDisplay

from mint.web.templatesupport import injectVersion, dictToJS, projectText
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="formatTitle(title)" py:strip="True" py:content="'%s%s%s'%(cfg.productName, title and ' - ', title)"/>

    <thead py:def="columnTitles(columns = [])" py:strip="False">
        <tr> <th py:for="columnName in columns">${columnName}</th>
        </tr>
    </thead>

    <div py:def="resultRow(result)" py:strip="True">
        <?python firstItem = True ?>
        <tr>
            <div py:for="item in result['columns']" py:strip="True">
                <td py:if="type(item) == tuple and len(item) == 2">
                    <a py:content="item[1]" href="${item[0]}" py:attrs="{ 'class': (firstItem and 'mainSearchItem' or None) }" />
                </td>
                <td py:if="type(item) != tuple" py:content="item" />
                <?python firstItem = False ?>
            </div>
        </tr>
        <tr py:if="result.get('desc')">
            <td colspan="${len(result['columns'])}" class="mainSearchItemDesc">
                ${result['desc']}
            </td>
        </tr>
    </div>

    <div id="groupBuilder" py:def="groupTroveBuilder" py:if="groupTrove">
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/groupbuilder.js?v={cacheFakeoutVersion}"/>
        <script type="text/javascript">
            addLoadEvent(initLinkManager);
            addLoadEvent(initGroupTroveManager);
        </script>
        <img class="left" src="${cfg.staticPath}apps/mint/images/header_orange_left.png" alt="" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/header_orange_right.png" alt="" />
        <div class="boxHeader">
            <a href="${groupProject.getUrl()}closeCurrentGroup?referer=${quote(req.unparsed_uri)}" title="Close"><img id="groupbuilder_items_close" src="${cfg.staticPath}/apps/mint/images/BUTTON_close.gif" alt="X" class="noborder" /></a>
            Group Builder
        </div>

        <div id="groupBuilderItems">
            <div><a href="${groupProject.getUrl()}editGroup?id=${groupTrove.id}" title="${groupTrove.recipeName}">Current Group: ${truncateForDisplay(groupTrove.recipeName, maxWordLen = 30)}</a></div>
            <table>
              <thead>
                <tr>
                    <th colspan="2">Trove</th>
                    <th>${projectText().title()}</th>
                    <th>Del</th>
                </tr>
              </thead>
              <tbody class="group-builder" id="groupbuilder-tbody">
                <tr><td></td></tr>
                <tr py:for="item in groupTrove.listTroves()" id="groupbuilder-item-${item['groupTroveItemId']}">
                    <td py:if="item['versionLock']"><img alt="Lock" class="lockicon" id="groupbuilder-item-lockicon-${item['groupTroveItemId']}" src="${cfg.staticPath}apps/mint/images/locked.gif" title="Version is locked" /></td>
                    <td py:if="not item['versionLock']"><img alt="Lock" class="lockicon" id="groupbuilder-item-lockicon-${item['groupTroveItemId']}" src="${cfg.staticPath}apps/mint/images/unlocked.gif" title="Version is unlocked"/></td>
                    <td py:if="item['versionLock']"><a href="${item['baseUrl']}troveInfo?t=${quote(item['trvName'])};v=${quote(injectVersion(item['trvVersion']))}" title="Name: ${item['trvName']}; Version: ${item['trvVersion']}" id="groupbuilder-item-trvname-${item['groupTroveItemId']}">${item['trvName']}</a></td>
                    <td py:if="not item['versionLock']"><a href="${item['baseUrl']}troveInfo?t=${quote(item['trvName'])}" title="Name: ${item['trvName']}; Label: ${item['trvLabel']}" id="groupbuilder-item-trvname-${item['groupTroveItemId']}">${item['trvName']}</a></td>
                    <td><a href="${item['baseUrl']}browse">${item['shortHost']}</a></td>
                    <td><a href="${groupProject.getUrl()}deleteGroupTrove?id=${groupTrove.id};troveId=${item['groupTroveItemId']};referer=${quote(req.unparsed_uri)}">X</a></td>
                </tr>
                <tr id="groupbuilder-example" style="display:none">
                    <td id="groupbuilder-example versionLock"><img alt="Lock" class="lockicon" id="groupbuilder-item-lockicon-TROVEID" src="${cfg.staticPath}apps/mint/images/locked.gif" /></td>
                    <td id="groupbuilder-example name"><a href="#">Trove</a></td>
                    <td id="groupbuilder-example projectName">${projectText().title()}</td>
                    <td id="groupbuilder-example delete"><a href="${groupProject.getUrl()}deleteGroupTrove?id=${groupTrove.id};troveId=TROVEID;referer=${quote(req.unparsed_uri)}">X</a></td>
                </tr>
                </tbody>
            </table>
            <div class="groupcook" style="padding: 10px 0; text-align: center;"><a class="option" style="display: inline;" href="${groupProject.getUrl()}pickArch?id=${groupTrove.id}">Cook&nbsp;This&nbsp;Group</a></div>
        </div>
    </div>

    <div id="builderPane" py:def="builderPane">
        <div py:if="groupTrove">
            ${groupTroveBuilder()}
        </div>
    </div>

    <div py:def="recentBuildsMenu(builds, display='none')" py:strip="True">
      <div id="builds" class="palette" py:if="builds">
        <h3 onclick="javascript:toggle_display('recentBuild_items');">
            <img id="browse_items_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_${display == 'block' and 'collapse' or 'expand'}.gif" class="noborder" />
            Recently Published Builds
        </h3>
        <div id="recentBuild_items" style="display: $display">
          <ul>
            <li py:for="build in builds">
                <div class="builds_project"><a class="builds_project" href="http://${cfg.projectSiteHost}${cfg.basePath}project/${build[1]}/">${build[0]}</a></div>
                <div class="builds_build">
                    <a href="http://${cfg.projectSiteHost}${cfg.basePath}project/${build[1]}/build?id=${build[2].getId()}">${build[2].getTroveName()}=${build[2].getTroveVersion().trailingRevision().asString()} (${build[2].getArch()})</a>
                </div>
            </li>
          </ul>
        </div>
      </div>
    </div>


    <table summary="layout" class="pager" style="margin-bottom: 1em;"
           py:def="navigation(urlbase, terms, count, limit, offset, footer=False)">
        <?python
            plural=""
            if count != 1:
                plural = "es"
        ?>
        <tr>
            <td>
                <span style="float: left;" py:if="count != 0 and not footer">
                    ${count} match${plural} found<span py:if="terms" py:omit="True"> for <strong>${terms}</strong></span>;
                    Showing ${offset + 1}-${min(offset+limit, count)};
                </span>
                <span style="float: right;" py:if="count != 0">
                    Page ${limit and offset/limit+1 or 1} of ${limit and (count+limit-1)/limit or 1}

                    <a href="${urlbase};limit=${limit};offset=${max(offset-limit, 0)}" class="imageButton" py:if="offset != 0"><img src="${cfg.staticPath}/apps/mint/images/prev.gif" alt="Previous" title="Previous Page" width="11" height="11" class="noborder" /></a>
                    <img py:if="offset == 0" src="${cfg.staticPath}/apps/mint/images/prev_disabled.gif" alt="Previous" title="No previous results" width="11" height="11" class="noborder"/>
                    <a href="${urlbase};limit=${limit};offset=${offset+limit}" class="imageButton" py:if="offset+limit &lt; count"><img src="${cfg.staticPath}/apps/mint/images/next.gif" alt="Next" title="Next Page" width="11" height="11" class="noborder" /></a>
                    <img py:if="offset+limit &gt;= count" src="${cfg.staticPath}/apps/mint/images/next_disabled.gif" alt="No next page" title="No subsequent results" width="11" height="11" class="noborder"/>
                </span>
            </td>
        </tr>
    </table>

    <!-- results structure:
        [('id', 'data item 1' ... 'data item n'), ]
    -->
    <tbody py:def="searchResults(results=[])" py:strip="True">
        <div py:strip="True" py:for="i, row in enumerate(results)" class="${i % 2 and 'even' or 'odd'}">
            ${resultRow(row)}
        </div>
    </tbody>

    <a py:def="legal(page, text)" py:strip="False" href="${page}"
        py:content="text" target="_blank"/>

    <div py:def="loginPane()" id="projectsPane">
        <?python
                from urllib import quote
                secureProtocol = 'http'
                if auth.authorized:
                    loginAction = "logout"
                else:
                    loginAction = "processLogin"
                if cfg.SSL:
                    secureProtocol = "https"
            ?>
        <div class="userLogin" py:if="maintenance.getMaintenanceMode(cfg) == maintenance.NORMAL_MODE">
          <img class="left" src="${cfg.staticPath}apps/mint/images/header_orange_left.png" alt="" />
          <img class="right" src="${cfg.staticPath}apps/mint/images/header_orange_right.png" alt="" />
          <div class="boxHeader">
              <div class="boxHeaderText" style="font-size: 120%;">
                  Sign In
              </div>
          </div>
        </div>
        <div class="adminLogin" py:if="maintenance.getMaintenanceMode(cfg) != maintenance.NORMAL_MODE">
          <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" alt="" />
          <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" alt="" />
          <div class="blueBoxHeader">
              <div class="boxHeaderText" style="font-size: 120%;">
                  Admin Sign In
              </div>
          </div>
        </div>
        <div class="boxBody">
            <form py:if="not auth.authorized" method="post" action="${secureProtocol}://${cfg.secureHost}${cfg.basePath}processLogin">
                <p>Username:<br /><input type="text" name="username" /></p>
                <p>Password:<br /><input type="password" name="password" /></p>
                <p>
                    <input style="float: left; margin: 0 1em 1em 0;" type="checkbox" name="rememberMe" value="1" />
                    <span style="text-decoration: underline;">Remember me</span> on this computer
                    <br style="clear: both;" />
                </p>
                <p><button id="signInSubmit" type="submit" class="img">
                    <img alt="Sign In" src="${cfg.staticPath}apps/mint/images/sign_in_button.png" />
                </button></p>
                <input type="hidden" name="to" value="${quote(toUrl)}" />
            </form>

            <div id="noAccount">
                <p py:if="not cfg.adminNewUsers"><strong>Don't have an account?</strong><br /><a href="${cfg.basePath}register">Set one up.</a></p>
                <p><a href="${cfg.basePath}forgotPassword">Forgot your password?</a></p>
            </div>
        </div>
    </div>

    <div py:def="resourcePane()" py:strip="True">
        <div py:if="not auth.authorized" py:strip="True">
            ${loginPane()}
        </div>
        <div py:if="auth.authorized" py:strip="True">
            ${projectsPane()}
        </div>
    </div>

    <div py:def="stepContent">
    </div>

    <div py:def="stepsWidget(steps, curStep = 0)" class="palette" id="stepWidget">
        <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" alt="" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" alt="" />
        <div class="boxHeader">
            Steps to Register
        </div>

        <div class="boxBody">
            <div py:for="i, step in enumerate(steps)" class="oneStep"
                py:attrs="{'style': (i == curStep and i != len(steps)-1) and 'border-bottom: 1px solid black;' or None}">
                <h2><img py:if="i &lt; curStep" style="float: right;" src="${cfg.staticPath}/apps/mint/images/icon_accept.gif" /> ${i+1}. ${step}</h2>
                <div py:strip="True" py:if="curStep == i">${stepContent()}</div>
            </div>
        </div>
    </div>

    <div py:def="statusArea(jobType, elementId = 'statusArea')">
        <div id="statusAreaHeader">
            <div class="padded">${jobType} Status</div>
        </div>
        <div id="${elementId}" class="running">
            <img src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" style="float: right;" id="statusSpinner" alt="Job Running" />
            <div id="statusMessage" />
       </div>
    </div>

</html>
