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
    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">search results</a>
    </div>

    <head/>
    <body>
        <p py:def="searchSummary(type, terms, modified)">
            Results 1 - 10 of about 9,850,000 for foo
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
                <h2>search results: ${type}</h2>
                ${navigation("search?type=%s;search=%s;modified=%d"%(type, terms, modified), terms, count, limit, offset)}
                <table cellspacing="0" cellpadding="0" class="results">
                    ${columnTitles(columns)}
                    ${searchResults(results)}
                </table>
                <h3>search again </h3>
                <form action="search" method="get">
                    <table cellspacing="0" cellpadding="0" class="mainformhorizontal">
                        <tr>
                            <th width="33%">Search Type:</th>
                            <th width="33%">Keyword(s):</th>
                            <th width="33%">Last Modified:</th>
                        </tr>

                        <tr>
                            <td width="33%">
                                <select name="type" onchange="if (this.options[this.selectedIndex].value=='Users') { document.getElementById('searchModified').disabled = true; } else { document.getElementById('searchModified').disabled = false; }">
                                    <option selected="selected" value="Projects">Search projects</option>
                                    <option value="Users">Search users</option>
                                </select>
                            </td>
                            <td width="33%">
                                <input type="text" name="search" size="10" />
                            </td>
                            <td width="33%">
                                <select name="modified" id="searchModified">
                                    <option py:for="i, option in enumerate(searcher.datehtml)" value="${i}">${option}</option>
                                </select>
                            </td>
                        </tr>
                    </table>
                    <p><button>Submit</button></p>
                </form>
            </div>
        </td>
    </body>
</html>
