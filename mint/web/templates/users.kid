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

        <div id="layout">
            <h2>Browse Users</h2>
            ${sortOrderForm(sortOrder)}
            ${navigation("users?sortOrder=%d"%(sortOrder), "all users", count, limit, offset)}
            <table class="results">
                ${columnTitles(columns)}
                ${searchResults(results)}
            </table>
            ${navigation("users?sortOrder=%d"%(sortOrder), "all users", count, limit, offset, True)}
        </div>
    </body>
</html>
