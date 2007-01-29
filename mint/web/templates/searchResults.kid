<?xml version='1.0' encoding='UTF-8'?>
<?python
    import time
    from mint import searcher
    from mint import buildtypes
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

                <?python xtraParams = "" ?>
                <form py:if="searchType == 'Projects' and buildTypes"
                      method="get" action="search">
                      <?python xtraParams = ";byPopularity=%d" % int(byPopularity) ?>
                    <table>
                        <tr>
                            <td>
                                <label for="buildTypeRestriction">Restrict by Build Type</label>
                                <select id="buildTypeRestriction" name="search">
                                    <option value="${fullTerms}">--</option>
                                    <option value="${fullTerms} buildtype=${bt}"
                                            py:for="bt in buildTypes"
                                            py:content="buildtypes.typeNamesMarketing[bt]" />
                                </select>
                            </td>
                            <td>
                                <input type="checkbox" py:attrs="{'checked': byPopularity and 'checked' or None}" name="byPopularity" value="1" />
                                <label for="byPopularity">Rank by Popularity</label>
                            </td>
                            <td>
                                <button type="submit">Update</button>
                            </td>
                        </tr>
                    </table>
                    <input type="hidden" name="type" value="Projects" />
                </form>

                <p py:if="limiters">
                    <div py:for="limiter in limiters">
                        <a href="search?type=$searchType;search=${limiter['newSearch']};modified=$modified;removed=1${xtraParams}" style="background-color: transparent; color: transparent;"><img src="${cfg.staticPath}/apps/mint/images/x_out.gif" alt="remove" title="Remove" width="12" height="12" /></a>&nbsp;Showing <b>${limiter['desc']}</b>
                    </div>
                </p>

                <div py:strip="True" py:if="not count"><p>No results found containing <b>${terms}</b>.</p></div>
                <div py:strip="True" py:if="count">
                    ${navigation("search?type=%s;search=%s;modified=%d;removed=%d%s"%(searchType, fullTerms, modified, int(limitsRemoved), xtraParams), terms, count, limit, offset)}
                    <table cellspacing="0" cellpadding="0" class="results">
                        ${columnTitles(columns)}
                        ${searchResults(results)}
                    </table>
                </div>
                ${navigation("search?type=%s;search=%s;modified=%d;removed=%d%s"%(searchType, fullTerms, modified, int(limitsRemoved), xtraParams), terms, count, limit, offset, True)}
            </div>
        </div>
    </body>
</html>
