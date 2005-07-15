<?xml version='1.0' encoding='UTF-8'?>
<?python
import time
from mint import searcher
?>
<html xmlns:py="http://purl.org/kid/ns#" xmlns="http://www.w3.org/1999/xhtml"
>
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <div py:def="columnTitles(columns = [])" py:omit="1">
            <thead class="results">
                <tr class="results">
                    <td py:for="columnName in columns">${columnName}</td>
                </tr>
            </thead>
    </div>
    <div py:def="resultRow(resultset = [])" py:omit="1">
                    <td class="results"><a href="${resultset[0]}">${resultset[1]}</a></td>
                    <?python
                        resultset.pop(0)
                        resultset.pop(0)
                    ?>
                    <td py:for="item in resultset" class="results">${item}</td>
    </div>
    <!-- results structure:
        [('id', 'data item 1' ... 'data item n'), ]
        XXX: add next/prev/skip links
    -->
    <div py:def="searchResults(type, title, count, results=[], modified=0, limit=10, offset=0)" py:omit="1">
        <?python
            columns = []
            if type == "Projects":
                columns = ('Project Name', 'Project Description', 'Last Modified')
            elif type == "Users":
                columns = ('User Name', 'Full Name', 'E-mail Address', 'Other')
            plural=""
            if count != 1:
                plural = "es"
        ?>
        <h2 class="results">> rpath > ${title}</h2>
        <div>${type}; keywords: ${terms}; modified within ${searcher.datehtml[modified]}</div>
        <div class="results">
            <span class="results">${count} match${plural} found;</span>
            <span py:if="count == 0" class="results">No results shown</span>
            <span py:if="count != 0" class="results">Showing ${offset + 1}-${min(offset+limit, count)}</span>
            <span py:if="count != 0" class="results">Page: ${offset/limit + 1}
                 of ${(count+limit-1)/limit}</span>
            <span py:if="count == 0" class="results">Page: 1 of 1</span>
            <!-- Navigation stuff -->
            <span py:if="offset == 0" class="resultsnav">Previous</span>
            <span py:if="offset != 0" class="resultsnav">
                <a href="search?type=${type};search=${terms};modified=${modified};limit=${limit};offset=${max(offset-limit, 0)}">Previous</a>
            </span>
            <span py:if="offset+limit &gt;= count" class="resultsnav">Next</span>
            <span py:if="offset+limit &lt; count" class="resultsnav">
                <a href="search?type=${type};search=${terms};modified=${modified};limit=${limit};offset=${offset+limit}">Next</a>
            </span>
        </div>
        <table class="results" width="100%">
            ${columnTitles(columns)}
            <tbody class="results">
                <tr py:for="i, result in enumerate(results)" class="${i % 2 and 'even' or 'odd'}">
                    <?python
                        formattedresults = []
                        if type == "Projects":
                            formattedresults = [ 'http://%s' % result[0],
                                result[1], result[2], time.ctime(result[3]) ]
                        elif type == "Users":
                            formattedresults = [ 'userInfo?id=%d' % result[0],
                                result[1], result[2], result[3], result[4] ]
                    ?>
                    ${resultRow(formattedresults)}
                </tr>
            </tbody>
        </table>
    </div>
</html>
