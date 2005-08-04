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
            columns = ('User Name', 'Full Name', 'Contact Info', 'Other')
    ?>
    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">search results</a>
    </div>

    <head/>
    <body>
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

        <td id="left" class="side">
            <div class="pad">
${browseMenu()}
${searchMenu()}
            </div>
        </td>
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
                    </table>
                    <p><button>Submit</button></p>
                </form>
            </div>
        </td>
    </body>
</html>
