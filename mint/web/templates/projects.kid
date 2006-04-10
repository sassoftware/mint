<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#
import time
from mint import projectlisting
from mint.mint import timeDelta
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#" py:extends="'layout.kid'">
    <head>
        <title>${formatTitle('Browse Projects')}</title>
    </head>
    <body>
        <div py:def="formatResults(resultset = [])" py:strip="True">
            <?python
                formattedresults = [
                    (resultset[0].getUrl(), resultset[0].getNameForDisplay()),
                    timeDelta(resultset[4]),
                ]
                resultsetdesc = resultset[0].getDescForDisplay()
            ?>
            ${resultRow(formattedresults, resultsetdesc)}
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

        <div class="layout">
            <div class="pad">
                <h2>Browse Projects</h2>
                ${sortOrderForm(sortOrder)}
                ${navigation("projects?sortOrder=%d"%(sortOrder), "all projects", count, limit, offset)}
                <table cellpadding="0" cellspacing="0" class="results">
                    ${columnTitles(('Project', 'Last Commit'))}
                    ${searchResults(results)}
                </table>
                ${navigation("projects?sortOrder=%d"%(sortOrder), "all projects", count, limit, offset, True)}
            </div>
        </div>
    </body>
</html>
