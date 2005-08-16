<?xml version='1.0' encoding='UTF-8'?>
<?python
    from mint import userlisting
    import time
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">browse users</a>
    </div>

    <head>
        <title>${formatTitle('Browse Users')}</title>
    </head>
    <body>
        <div py:def="formatResults(resultset = [])" py:strip="True">
            <?python
                formattedresults = [
                    ('userInfo?id=%s' % resultset[0], resultset[1]),
                    resultset[2],
                    time.ctime(resultset[3]),
                    time.ctime(resultset[4]),
                    resultset[5]
                ]
            ?>
            ${resultRow(formattedresults)}
        </div>
        <td id="left" class="side">
            <div class="pad">
                ${browseMenu()}
                ${searchMenu()}
            </div>
        </td>

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

        <td id="main" class="spanall">
            <div class="pad">
                <h2>Browse Users</h2>
                ${sortOrderForm(sortOrder)}
                ${navigation("users?sortOrder=%d"%(sortOrder), "all users", count, limit, offset)}
                <table cellpadding="0" cellspacing="0" class="results">
                    ${columnTitles(('User Name', 'Name', 'Time Created', 'Time Last Accessed', 'About'))}
                    ${searchResults(results)}
                </table>
            </div>
        </td>
    </body>
</html>
