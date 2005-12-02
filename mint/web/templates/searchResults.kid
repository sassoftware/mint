<?xml version='1.0' encoding='UTF-8'?>
<?python
    from mint import searcher
    import time
    from urllib import quote
    from mint.mint import timeDelta
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <?python
        columns = []
        if searchType == "Projects":
            columns = ('Project Name', 'Project Description', 'Last Commit')
        elif searchType == "Users":
            columns = ('User Name', 'Full Name', 'Contact Info', 'About', 'Last Accessed')
        elif searchType == "Packages":
            if groupTrove:
                columns = ('Package Name', 'Version', 'Project', '')
            else:
                columns = ('Package Name', 'Version', 'Project')
    ?>
    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">Search Results</a>
    </div>

    <head>
        <title>${formatTitle('Search Results')}</title>
    </head>
    <body>
        <div py:def="formatResults(resultset = [])" py:strip="True">
            <?python
                formattedresults = []
                if searchType == "Projects":
                    formattedresults = [
                        (resultset[0].getUrl(), resultset[2]),
                        resultset[3],
                        timeDelta(resultset[4])
                    ]
                elif searchType == "Users":
                    formattedresults = [
                        ('userInfo?id=%d' % resultset[0], resultset[1]),
                        resultset[2],
                        resultset[3], 
                        resultset[4],
                        timeDelta(resultset[5])
                    ]
                elif searchType == "Packages":
                    formattedresults = [
                        (resultset[2], resultset[0]),
                        resultset[1],
                        (resultset[4], resultset[3])
                    ]
                    if groupTrove and resultset[2] != groupTrove.recipeName:
                        formattedresults.append(('project/%s/addGroupTrove?id=%d;trove=%s;version=%s;referer=%s' % (groupTrove.projectName, groupTrove.getId(), quote(resultset[0]), resultset[1], quote(req.unparsed_uri)) , 'Add to %s' % groupTrove.recipeName))
            ?>
            ${resultRow(formattedresults)}
        </div>

        <td id="left" class="side">
            <div class="pad">
                ${browseMenu()}
                ${searchMenu(searchType)}
            </div>
        </td>
        <td id="main">
            <div class="pad">
                <h2>search results: ${searchType}</h2>
                ${navigation("search?type=%s;search=%s;modified=%d"%(searchType, terms, modified), terms, count, limit, offset)}
                <table cellspacing="0" cellpadding="0" class="results">
                    ${columnTitles(columns)}
                    ${searchResults(results)}
                </table>
                ${navigation("search?type=%s;search=%s;modified=%d"%(searchType, terms, modified), terms, count, limit, offset, True)}
            </div>
        </td>
        <td id="right" class="projects">
            ${projectsPane()}
            <div class="pad">
                ${groupTroveBuilder(searchType=='Packages' and 'block' or 'none')}
            </div>
        </td>
    </body>
</html>
