<?xml version='1.0' encoding='UTF-8'?>
<?python
import time
from mint import searcher
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <thead class="results" py:def="columnTitles(columns = [])" py:omit="False">
        <tr class="results">
            <td py:for="columnName in columns">${columnName}</td>
        </tr>
    </thead>

    <div py:def="resultRow(resultset = [])" py:omit="True">
        <td class="results"><a href="${resultset[0]}">${resultset[1]}</a></td>
        <?python
            resultset.pop(0)
            resultset.pop(0)
        ?>
        <td py:for="item in resultset" class="results">${item}</td>
    </div>

    <div py:def="navigation(urlbase, count, limit, offset)" py:omit="False" class="results">
        <?python
            plural=""
            if count != 1:
                plural = "es"
        ?>
        <span class="results">${count} match${plural} found;</span>
        <span py:if="count == 0" class="results">No results shown</span>
        <span py:if="count != 0" class="results">Showing ${offset + 1}-${min(offset+limit, count)}</span>
        <span py:if="count != 0" class="results">Page: ${offset/limit + 1}
             of ${(count+limit-1)/limit}</span>
        <span py:if="count == 0" class="results">Page: 1 of 1</span>
        
        <span py:if="offset == 0" class="resultsnav">Previous</span>
        <span py:if="offset != 0" class="resultsnav">
            <a href="${baseurl};limit=${limit};offset=${max(offset-limit, 0)}">Previous</a>
        </span>
        <span py:if="offset+limit &gt;= count" class="resultsnav">Next</span>
        <span py:if="offset+limit &lt; count" class="resultsnav">
            <a href="${baseurl};limit=${limit};offset=${offset+limit}">Next</a>
        </span>
    </div>


    <div py:def="formatResults(resultset = [])" py:omit="True">
        <?python
            ##This function must be implemented in any derived class
            raise NotImplementedError
        ?>
        $resultRow(resultset)
    </div>

    <!-- results structure:
        [('id', 'data item 1' ... 'data item n'), ]
    -->
    <tbody py:def="searchResults(results=[])" py:omit="False">
        <tr py:for="i, resultset in enumerate(results)" class="${i % 2 and 'even' or 'odd'}">
            ${formatResults(resultset)}
        </tr>
    </tbody>
</html>
