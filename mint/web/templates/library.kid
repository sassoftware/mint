<?xml version='1.0' encoding='UTF-8'?>
<?python
import time
from mint import searcher
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <!-- define the HTML header -->
    <head py:def="html_header(title, extraScript=None, scriptArgs=None)">
        <title>${title}</title>
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}css/common.css" />
        <link rel="stylesheet" type="text/css" href="${cfg.staticUrl}apps/mint/css/style.css" />
        <script py:if="extraScript">${extraScript(*scriptArgs)}</script>
        <script language="javascript1.2" src="${cfg.staticUrl}apps/mint/javascript/library.js" /> 
        <script language="javascript1.2" src="${cfg.staticUrl}apps/mint/javascript/xmlrpc.js" />
    </head>

    <!-- define the HTML footer -->
    <div class="footer" py:def="html_footer">
        <span py:if="auth.authorized" id="logout">You are logged in as ${auth.username}. <a href="logout">Log Out</a></span>
        <span py:if="not auth.authorized" id="login"><a href="login">Log In</a></span>

        <div id="copyright">Copyright &#169; 2004-2005 <a href="http://www.rpath.com/">rpath, inc.</a></div>
    </div>

    <!-- define header image -->
    <div py:def="header_image()" py:omit="True">
        <h1 class="title">rPath</h1>
    </div>

    <!-- 
        Menu structure:

            [('menu name', 'url', highlighted), ]
    -->
    <div py:def="menu(mainMenu, subMenu=[])" py:omit="1">
        <ul class="menu">
            <li py:for="menuName, menuLink, highlight in mainMenu"
                py:attrs="{'class': highlight and 'highlighted' or False}">
                <a py:if="menuLink" href="${menuLink}">${menuName}</a>
                <span py:if="not menuLink" py:omit="True">${menuName}</span>
            </li>
        </ul>
        <ul class="menu submenu">
            <li py:for="menuName, menuLink, highlight in subMenu"
                py:attrs="{'class': highlight and 'highlighted' or False}">
                <a py:if="menuLink" href="${menuLink}">${menuName}</a>
                <span py:if="not menuLink" py:omit="True">${menuName}</span>
            </li>
        </ul>
   </div>

    <thead class="results" py:def="columnTitles(columns = [])" py:omit="False">
        <tr class="results">
            <td py:for="columnName in columns">${columnName}</td>
        </tr>
    </thead>

    <div py:def="resultRow(resultset = [])" py:omit="True">
        <td class="results"><a href="${resultset[0]}">${resultset[1]}</a></td>
        <?python
            resultset.pop(0)
            resultset.pop(0)
        ?>
        <td py:for="item in resultset" class="results">${item}</td>
    </div>

    <div py:def="navigation(urlbase, count, limit, offset)" py:omit="False" class="results">
        <?python
            plural=""
            if count != 1:
                plural = "es"
        ?>
        <span class="results">${count} match${plural} found;</span>
        <span py:if="count == 0" class="results">No results shown</span>
        <span py:if="count != 0" class="results">Showing ${offset + 1}-${min(offset+limit, count)}</span>
        <span py:if="count != 0" class="results">Page: ${offset/limit + 1}
             of ${(count+limit-1)/limit}</span>
        <span py:if="count == 0" class="results">Page: 1 of 1</span>
        <!-- Navigation stuff -->
        <span py:if="offset == 0" class="resultsnav">Previous</span>
        <span py:if="offset != 0" class="resultsnav">
            <a href="${baseurl};limit=${limit};offset=${max(offset-limit, 0)}">Previous</a>
        </span>
        <span py:if="offset+limit &gt;= count" class="resultsnav">Next</span>
        <span py:if="offset+limit &lt; count" class="resultsnav">
            <a href="${baseurl};limit=${limit};offset=${offset+limit}">Next</a>
        </span>
    </div>


    <div py:def="formatResults(resultset = [])" py:omit="True">
        <?python
            ##This function must be implemented in any derived class
            raise NotImplementedError
        ?>
        $resultRow(resultset)
    </div>

    <!-- results structure:
        [('id', 'data item 1' ... 'data item n'), ]
    -->
    <tbody py:def="searchResults(results=[])" py:omit="False">
        <tr py:for="i, resultset in enumerate(results)" class="${i % 2 and 'even' or 'odd'}">
            ${formatResults(resultset)}
        </tr>
    </tbody>
</html>
