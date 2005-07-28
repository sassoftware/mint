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
        <div py:def="searchSummary(type, terms, modified)" py:strip="True">
            ${type}; keywords: ${terms}; modified within ${searcher.datehtml[modified]}
        </div>

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

        <div id="content">
            <h2 class="results">> rpath > ${type} Search Results</h2>
${searchSummary(type, terms, modified)}
${navigation("search?type=%s;search=%s;modified=%d"%(type, terms, modified), count, limit, offset)}
            <table class="results" border="2">
${columnTitles(columns)}
${searchResults(results)}

            </table>
        </div>
    </body>
</html>
