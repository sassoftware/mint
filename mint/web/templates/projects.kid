<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2007 rPath, Inc.
# All Rights Reserved
#
from mint import projectlisting
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#" py:extends="'layout.kid'">
    <head>
        <title>${formatTitle('Browse Projects')}</title>
    </head>
    <body>
        <p py:def="sortOrderForm(sortOrder = 0)">
            <form method="get" action="projects">
                <select name="sortOrder">
                    <option py:for="key, value in projectlisting.orderhtml.items()"
                        value="${key}" py:attrs="{'selected': (key==sortOrder) and 'selected' or None}"
                        py:content="value" />
                </select>
                <button type="submit">Update</button>
            </form>
        </p>

        <div id="layout">
            <div class="pad">
                <h2>Browse Projects</h2>
                ${sortOrderForm(sortOrder)}
                ${navigation("projects?sortOrder=%d"%(sortOrder), "all projects", count, limit, offset)}
                <table cellpadding="0" cellspacing="0" class="results">
                    ${columnTitles(columns)}
                    ${searchResults(results)}
                </table>
                ${navigation("projects?sortOrder=%d"%(sortOrder), "all projects", count, limit, offset, True)}
            </div>
        </div>
    </body>
</html>
