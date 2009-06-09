<?xml version='1.0' encoding='UTF-8'?>
<?python
    import time
    from mint import searcher
    from mint import buildtypes
    from mint.web.templatesupport import projectText
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layoutUI.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->

    <head>
        <title>${formatTitle('Search Results')}</title>
    </head>
    <body>
        <div class="fullpage">
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            <div id="right" class="side">
            </div>
            <div id="leftcenter">
                <h1 class="search">Search Results: ${searchType}</h1>
    
                <form py:if="searchType in ('Projects', 'Products') and buildTypes" method="get" action="search">
                <table>
                <tr>
                    <td>
                    <label for="buildTypeRestriction">Restrict by Image Type</label>
                    <select id="buildTypeRestriction" name="search">
                        <option value="${fullTerms}">--</option>
                        <option value="${fullTerms} buildtype=${bt}" py:for="bt in buildTypes"
                            py:content="buildtypes.typeNamesMarketing[bt]" />
                    </select></td>
                    <td>
                        <button type="submit">Update</button></td>
                </tr>
                <tr>
                    <div py:if="filterNoDownloads" class="help">Showing only ${projectText().lower()}s with releases.
                        <a href="searchUI?type=$searchType;search=$terms;modified=$modified;showAll=1">Show All ${projectText().title()}s</a>
                    </div>
                </tr>
                </table>
                <input type="hidden" name="type" value="${searchType}" />
                </form>
    
                <p py:if="limiters" py:string="True">
                    <div py:for="limiter in limiters" py:strip="True"><a href="searchUI?type=$searchType;search=${limiter['newSearch']};modified=$modified;removed=1" class="imageButton"><img src="${cfg.staticPath}/apps/mint/images/x_out.gif" alt="remove" title="Remove" width="12" height="12" /></a>&nbsp;Showing <b>${limiter['desc']}</b></div></p>
    
                <div py:strip="True" py:if="not count">No results found containing "${terms}".</div>
                <div py:strip="True" py:if="count">
                    ${navigation("searchUI?type=%s;search=%s;modified=%d;removed=%d%s" % (searchType, fullTerms, modified, int(limitsRemoved), extraParams), terms, count, limit, offset)}
                    <table class="results">
                        ${columnTitles(columns)}
                        ${searchResults(results)}
                    </table>
                </div>
                ${navigation("searchUI?type=%s;search=%s;modified=%d;removed=%d%s" % (searchType, fullTerms, modified, int(limitsRemoved), extraParams), terms, count, limit, offset, True)}
            </div>
            <div class="clear"/>
            <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"></div>
        </div>
    </body>
</html>
