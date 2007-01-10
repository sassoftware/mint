<?xml version='1.0' encoding='UTF-8'?>
<?python
    import time
    from mint import searcher
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->

    <head>
        <title>${formatTitle('Search Results')}</title>
    </head>
    <body>

        <div id="layout">
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="spanleft">
                <h2>Search Results: ${searchType}</h2>

                <p class="help" py:if="limiters">
                    <div py:for="limiter in limiters">
                        Showing ${limiter['desc']} (<a href="search?type=$searchType;search=${limiter['newSearch']};modified=$modified">remove</a>)
                    </div>
                </p>

                ${navigation("search?type=%s;search=%s;modified=%d"%(searchType, terms, modified), terms, count, limit, offset)}
                <table cellspacing="0" cellpadding="0" class="results">
                    ${columnTitles(columns)}
                    ${searchResults(results)}
                </table>
                ${navigation("search?type=%s;search=%s;modified=%d"%(searchType, terms, modified), terms, count, limit, offset, True)}
            </div>
        </div>
    </body>
</html>
