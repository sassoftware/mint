<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlisting
import time
from mint.mint import timeDelta
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Browse Users')}</title>
    </head>
    <body>
        <div py:def="formatResults(resultset = [])" py:strip="True">
            <?python
                formattedresults = [
                    ('userInfo?id=%s' % resultset[0], resultset[1]),
                    resultset[2],
                    resultset[3],
                    resultset[4],
                    timeDelta(resultset[5]),
                    timeDelta(resultset[6]),
                ]
            ?>
            ${resultRow(formattedresults)}
        </div>
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

        <div class="layout">
            <h2>Browse Users</h2>
            ${sortOrderForm(sortOrder)}
            ${navigation("users?sortOrder=%d"%(sortOrder), "all users", count, limit, offset)}
            <table class="results">
                ${columnTitles(('User Name', 'Full Name', 'Contact Info', 'About', 'Created', 'Last Accessed'))}
                ${searchResults(results)}
            </table>
            ${navigation("users?sortOrder=%d"%(sortOrder), "all users", count, limit, offset, True)}
        </div>
    </body>
</html>
