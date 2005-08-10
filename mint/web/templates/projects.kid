<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (C) 2005 rpath, Inc.
# All Rights Reserved
#
import time
from mint import projectlisting
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">browse projects</a>
    </div>

    <head/>
    <body>
        <div py:def="formatResults(resultset = [])" py:strip="True">
            <?python
                formattedresults = [
                    ('http://%s' % resultset[0], resultset[1]),
                    resultset[2],
                    time.ctime(resultset[3]),
                    time.ctime(resultset[4]),
                    resultset[5]
                ]
            ?>
            ${resultRow(formattedresults)}
        </div>

        <p py:def="sortOrderForm(sortOrder = 0)">
            <form method="get" action="projects">
                <select name="sortOrder">
                    <option py:for="key, value in projectlisting.orderhtml.items()"
                        value="${key}" py:attrs="{'selected': (key==sortOrder) and 'selected' or None}"
                        py:content="value" />
                </select>
                <button type="submit">Go</button>
            </form>
        </p>

        <td id="left" class="side">
            <div class="pad">
                ${browseMenu()}
                ${searchMenu()}
            </div>
        </td>
        <td id="main" class="spanall">
            <div class="pad">
                <h2>Browse Projects</h2>
                ${sortOrderForm(sortOrder)}
                ${navigation("projects?sortOrder=%d"%(sortOrder), "all projects", count, limit, offset)}
                <table cellpadding="0" cellspacing="0" class="results">
                    ${columnTitles(('Project Name', 'Project Description', 'Time Created', 'Time Last Modified', 'Number of Developers'))}
                    ${searchResults(results)}
                </table>
            </div>
        </td>
    </body>
</html>
