<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlisting
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Browse Users')}</title>
    </head>
    <body>
        <div py:def="sortOrderForm(sortOrder = 0)" py:strip="True">
            <form method="get" action="users">
                <select name="sortOrder">
                    <option py:for="key, value in userlisting.orderhtml.items()"
                        value="${key}" py:attrs="{'selected': (key==sortOrder) and 'selected' or None}"
                        py:content="value" />
                </select>
                <button type="submit">Go</button>
            </form>
        </div>

        <div class="fullpage">
            <img id="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img id="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="leftcenter">
                <h1 class="search">Browse Users</h1>
                ${sortOrderForm(sortOrder)}
                ${navigation("users?sortOrder=%d"%(sortOrder), "all users", count, limit, offset)}
                <table class="results">
                    ${columnTitles(columns)}
                    ${searchResults(results)}
                </table>
                ${navigation("users?sortOrder=%d"%(sortOrder), "all users", count, limit, offset, True)} <br class="clear" />
            </div><br class="clear"/>
            <img id="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img id="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"></div>
        </div>

    </body>
</html>
