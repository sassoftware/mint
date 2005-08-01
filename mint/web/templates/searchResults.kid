<?xml version='1.0' encoding='UTF-8'?>
<?python
    from mint import searcher
    import time    
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <?python
        columns = []
        if type == "Projects":
            columns = ('Project Name', 'Project Description', 'Last Modified')
        elif type == "Users":
            columns = ('User Name', 'Full Name', 'E-mail Address', 'Other')
    ?>
    <head/>
    <body>
        <p py:def="searchSummary(type, terms, modified)">
            ${type}; keywords: ${terms}; modified within ${searcher.datehtml[modified]}
        </p>

        <div py:def="formatResults(resultset = [])" py:strip="True">
            <?python
                formattedresults = []
                if type == "Projects":
                    formattedresults = [ 'http://%s' % resultset[0],
                        resultset[1], resultset[2],
                        time.ctime(resultset[3]) ]
                elif type == "Users":
                    formattedresults = [ 'userInfo?id=%d' % resultset[0],
                        resultset[1], resultset[2], resultset[3], 
                        resultset[4] ]
            ?>
            ${resultRow(formattedresults)}
        </div>

        <td id="main" class="spanall">
            <div class="pad">
                <h2>search results</h2>
                ${searchSummary(type, terms, modified)}
                ${navigation("search?type=%s;search=%s;modified=%d"%(type, terms, modified), count, limit, offset)}
                <table cellspacing="0" cellpadding="0" class="results">
                    ${columnTitles(columns)}
                    ${searchResults(results)}
                </table>
            </div>
        </td>
    </body>
</html>
