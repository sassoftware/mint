<?xml version='1.0' encoding='UTF-8'?>
<?python
    import time
    from urllib import quote
    from mint import searcher
    from mint.client import timeDelta
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <?python
        columns = []
        if searchType == "Projects":
            columns = ('Project', 'Last Commit')
        elif searchType == "Users":
            if auth.admin:
                columns = ('User Name', 'Full Name', 'Account Created', 'Last Accessed', 'Status')
            else:
                columns = ('User Name', 'Full Name', 'Account Created', 'Last Accessed')
        elif searchType == "Packages":
            if groupTrove:
                columns = ('Package', 'Project', '')
            else:
                columns = ('Package', 'Project')
    ?>

    <head>
        <title>${formatTitle('Search Results')}</title>
    </head>
    <body>
        <div py:def="formatResults(resultset = [])" py:strip="True">
            <?python
                formattedresults = []
                if searchType == "Projects":
                    formattedresults = [
                        (resultset[0].getUrl(),
                        resultset[0].getNameForDisplay()),
                        timeDelta(resultset[4])
                    ]
                    resultsetdesc = resultset[0].getDescForDisplay()
                elif searchType == "Users":
                    formattedresults = [
                        (self.cfg.basePath + 'userInfo?id=%d' % resultset[0], resultset[1]),
                        resultset[2],
                        timeDelta(resultset[5]),
                        timeDelta(resultset[6])
                    ]
                    if auth.admin:
                        formattedresults.append(resultset[7] and "Active" or "Inactive")
                    resultsetdesc = resultset[4]
                elif searchType == "Packages":
                    formattedresults = [
                        (resultset[2], resultset[0]),
                        (resultset[4], resultset[3])
                    ]
                    resultsetdesc = resultset[1]
                    if groupTrove and not groupTrove.troveInGroup(resultset[0]):
                        formattedresults.append((self.cfg.basePath + 'project/%s/addGroupTrove?id=%d;trove=%s;version=%s;referer=%s' % (groupTrove.projectName, groupTrove.getId(), quote(resultset[0]), resultset[1], quote(req.unparsed_uri)) , 'Add to %s' % groupTrove.recipeName))
            ?>
            ${resultRow(formattedresults, resultsetdesc)}
        </div>

        <div id="layout">
            <div id="right" class="side">
                ${resourcePane()}
                ${groupTroveBuilder()}
            </div>
            <div id="spanleft">
                <h2>Search Results: ${searchType}</h2>
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
