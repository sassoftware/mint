<?xml version='1.0' encoding='UTF-8'?>
<?python
    import time
    from mint import searcher
    from mint.buildtypes import typeNamesMarketing
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

                <form py:if="searchType == 'Projects' and buildTypes"
                      method="get" action="search">
                    <label for="buildTypeRestriction">Restrict by Build Type</label>
                    <input type="hidden" name="type" value="Projects" />
                    <select id="buildTypeRestriction" name="search">
                        <option value="${fullTerms}">--</option>
                        <option value="${fullTerms} buildtype=${bt}"
                                py:for="bt in buildTypes + [buildtypes.XEN_DOMU]"
                                py:content="typeNamesMarketing[bt]" />
                    </select>
                    <input type="submit">Go</input>
                </form>

                <p class="help" py:if="limiters">
                    <div py:for="limiter in limiters">
                        Showing ${limiter['desc']} (<a href="search?type=$searchType;search=${limiter['newSearch']};modified=$modified;removed=1">remove</a>)
                    </div>
                </p>

                <div py:strip="True" py:if="not count"><p>No results found containing <b>${terms}</b>.</p></div>
                <div py:strip="True" py:if="count">
                    ${navigation("search?type=%s;search=%s;modified=%d;removed=%d"%(searchType, fullTerms, modified, int(limitsRemoved)), terms, count, limit, offset)}
                    <table cellspacing="0" cellpadding="0" class="results">
                        ${columnTitles(columns)}
                        ${searchResults(results)}
                    </table>
                </div>
                ${navigation("search?type=%s;search=%s;modified=%d;removed=%d"%(searchType, fullTerms, modified, int(limitsRemoved)), terms, count, limit, offset, True)}
            </div>
        </div>
    </body>
</html>
