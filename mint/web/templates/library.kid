<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import constants
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
        <tr py:attrs="{ 'class': (result.get('desc') and 'item-top-row' or 'item-row') }">
            <div py:for="item in result['columns']" py:strip="True">
                <td py:if="type(item) == tuple and len(item) == 2">
                    <a py:content="item[1]" href="${item[0]}" py:attrs="{ 'class': (firstItem and 'mainSearchItem' or None) }" />
                </td>
                <td py:if="type(item) != tuple" py:content="item" />
                <?python firstItem = False ?>
            </div>
        </tr>
        <tr py:if="result.get('desc')" class="item-row">
            <td colspan="${len(result['columns'])}" class="mainSearchItemDesc">
                ${result['desc']}
            </td>
        </tr>
    </div>

    <div py:def="recentBuildsMenu(builds, display='none')" py:strip="True">
      <div id="builds" class="palette" py:if="builds">
        <h3 onclick="javascript:toggle_display('recentBuild_items');">
            <img id="browse_items_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_${display == 'block' and 'collapse' or 'expand'}.gif" class="noborder" />
            Recently Published Images
        </h3>
        <div id="recentBuild_items" style="display: $display">
          <ul>
            <li py:for="build in builds">
                <div class="builds_project"><a class="builds_project" href="${cfg.basePath}project/${build[1]}/">${build[0]}</a></div>
                <div class="builds_build">
                    <a href="${cfg.basePath}project/${build[1]}/build?id=${build[2].getId()}">${build[2].getTroveName()}=${build[2].getTroveVersion().trailingRevision().asString()} (${build[2].getArch()})</a>
                </div>
            </li>
          </ul>
        </div>
      </div>
    </div>


    <table class="pager" py:def="navigation(urlbase, terms, count, limit, offset, footer=False)">
    <?python
        plural=""
        if count != 1:
            plural = "es"
    ?>
    <tr>
        <td>
        <span class="results-summary" py:if="count != 0 and not footer">
            ${count} match${plural} found<span py:if="terms" py:omit="True"> for "${terms}"</span>
            ( ${offset + 1}-${min(offset+limit, count)} showing )
        </span>
        <span class="results-paging" py:if="count != 0">
            <a class="no-decoration" href="${urlbase};limit=${limit};offset=${max(offset-limit, 0)}" py:if="offset != 0"><img src="${cfg.staticPath}/apps/mint/images/search_prev.gif" alt="Previous" title="Previous Page" class="page-previous" /></a>
            <img py:if="offset == 0" src="${cfg.staticPath}/apps/mint/images/search_prev_disabled.gif" alt="Previous" title="No previous results" class="page-previous"/> Page ${limit and offset/limit+1 or 1} of ${limit and (count+limit-1)/limit or 1} <a href="${urlbase};limit=${limit};offset=${offset+limit}" py:if="offset+limit &lt; count"><img src="${cfg.staticPath}/apps/mint/images/search_next.gif" alt="Next" title="Next Page" class="page-next" /></a>
            <img py:if="offset+limit &gt;= count" src="${cfg.staticPath}/apps/mint/images/search_next_disabled.gif" alt="No next page" title="No subsequent results" class="page-next" />
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
          <img class="left" src="${cfg.staticPath}apps/mint/images/header_user_left.png" alt="" />
          <img class="right" src="${cfg.staticPath}apps/mint/images/header_user_right.png" alt="" />
          <div class="userBoxHeader">
              <div class="userBoxHeaderText">
                  <span class="userBoxBracket">[</span> sign in <span class="userBoxBracket">]</span>
              </div>
          </div>
        </div>
        <div class="adminLogin" py:if="maintenance.getMaintenanceMode(cfg) != maintenance.NORMAL_MODE">
          <img class="left" src="${cfg.staticPath}apps/mint/images/header_user_left.png" alt="" />
          <img class="right" src="${cfg.staticPath}apps/mint/images/header_user_right.png" alt="" />
          <div class="userBoxHeader">
              <div class="userBoxHeaderText">
                  <span class="userBoxBracket">[</span> admin sign in <span class="userBoxBracket">]</span>
              </div>
          </div>
        </div>
        <div class="boxBody">
            <a class="newuiLink" href="/ui/" target="_blank">Use the new UI</a>
            <form py:if="not auth.authorized" method="post" action="${httpsUrl}processLogin">
                <p class="signinlabel">Username:<br /><input class="signinfield" type="text" name="username" /></p>
                <p class="signinlabel">Password:<br /><input class="signinfield" type="password" name="password" /></p>
                <p class="signinremember"><input class="signincheck" type="checkbox" name="rememberMe" value="1" /> Remember me on this computer</p>
                <button id="signInSubmit" type="submit" class="img">
                    <img alt="Sign In" src="${cfg.staticPath}apps/mint/images/sign_in_button.png" />
                </button>
            </form>
            <div class="signinActions">
            <div id="newAccount" class="projectsPaneActionTop" py:if="not cfg.adminNewUsers">
                <a href="${cfg.basePath}register">Create a New Account</a>
            </div>
            <div id="forgotPassword" class="projectsPaneAction">
                <a href="${cfg.basePath}forgotPassword">Forgot My Password</a>
            </div>
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

    <div py:def="stepContent"></div>

    <div py:def="stepsWidget(steps, curStep = 0)" class="wizard-nav-palette" id="stepWidget">
        <img class="left" src="${cfg.staticPath}apps/mint/images/wiz_header_blue_left.png" alt="" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/wiz_header_blue_right.png" alt="" />
        <div class="boxHeader">
            <span class="bracket">[</span> Steps to Register <span class="bracket">]</span>
        </div>

        <ul class="wiz-navigation">
            <li py:for="i, step in enumerate(steps)"
                py:attrs="{'class': (i == curStep) and 'selectedItem' or (curStep > i) and 'completedItem' or None}">
                ${step}
                <div py:strip="True" py:if="curStep == i">${stepContent()}</div></li>
        </ul>
    </div>

    <div py:def="statusArea(jobType, elementId = 'statusArea')">
        <div class="boxPalette">
            <img class="left" src="${cfg.staticPath}apps/mint/images/block_topleft.gif" alt="" />
            <img class="right" src="${cfg.staticPath}apps/mint/images/block_topright.gif" alt="" />
            <div class="pageBoxHeader">${jobType} Status</div>
            <div id="${elementId}" class="running">
            <img src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" style="float: right;" id="statusSpinner" alt="Job Running" />
                <div id="statusMessage" />
            </div>
            <img class="left" src="${cfg.staticPath}apps/mint/images/block_bottom.gif" width="100%" height="3px" alt="" />
       </div>
    </div>
    
    <div py:def="formLabelWithHelp(helpDivId, labelTitle, tooltip='Click here for more information', required=True)">
        <div class="required-help" onclick="javascript:toggle_display('${helpDivId}');" title="${tooltip}">
            ${labelTitle}
       </div>
    </div>

    <div py:def="layoutFooter()">
        <div id="footer">
            <span id="topOfPage"><a href="#top">Top of Page</a></span>
            <div class="footerLinks">
                <span id="mintFullVersionString" style="display: none">${cfg.productName} version ${constants.fullVersion} | </span>
                <span id="mintVersionString">${cfg.productName} version ${constants.mintVersion}</span>
            </div>
            <div id="bottomText">
                <span id="copyright">Copyright &copy; rPath, Inc. All Rights Reserved.</span>
            </div>
         
        </div><br class="clear" />
        <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/page_bottomleft.gif" alt="" />
        <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/page_bottomright.gif" alt="" />
    </div>

</html>
