<?xml version='1.0' encoding='UTF-8'?>
<?python
    import time
    from mint import searcher
    from mint import buildtypes
    from mint.web.templatesupport import projectText
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
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
                                <button type="submit">Update</button>
                            </td>
                        </tr>
                        <tr>
                            <div py:if="filterNoDownloads" class="help">Showing only ${projectText().lower()}s with releases.
                                <a href="search?type=$searchType;search=$terms;modified=$modified;showAll=1">Show All ${projectText().title()}s</a>
                            </div>
                        </tr>
                    </table>
                    <input type="hidden" name="type" value="Projects" />
                </form>

                <p py:if="limiters">
                    <div py:for="limiter in limiters"><a href="search?type=$searchType;search=${limiter['newSearch']};modified=$modified;removed=1" class="imageButton"><img src="${cfg.staticPath}/apps/mint/images/x_out.gif" alt="remove" title="Remove" width="12" height="12" /></a>&nbsp;Showing <b>${limiter['desc']}</b></div>
                </p>

                <div py:strip="True" py:if="not count"><p>No results found containing <b>${terms}</b>.</p></div>
                <div py:strip="True" py:if="count">
                    ${navigation("search?type=%s;search=%s;modified=%d;removed=%d%s" % (searchType, fullTerms, modified, int(limitsRemoved), extraParams), terms, count, limit, offset)}
                    <table cellspacing="0" cellpadding="0" class="results">
                        ${columnTitles(columns)}
                        ${searchResults(results)}
                    </table>
                </div>
                ${navigation("search?type=%s;search=%s;modified=%d;removed=%d%s" % (searchType, fullTerms, modified, int(limitsRemoved), extraParams), terms, count, limit, offset, True)}
            </div>
        </div>
    </body>
</html>
