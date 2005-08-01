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
    <thead py:def="columnTitles(columns = [])" py:strip="False">
        <tr>
            <th py:for="columnName in columns">${columnName}</th>
        </tr>
    </thead>

    <div py:def="resultRow(resultset = [])" py:strip="True">
        <td><a href="${resultset[0]}">${resultset[1]}</a></td>
        <?python
            resultset.pop(0)
            resultset.pop(0)
        ?>
        <td py:for="item in resultset">${item}</td>
    </div>


    <table border="0" cellspacing="0" cellpadding="0"
           summary="layout" class="pager"
           py:def="navigation(urlbase, count, limit, offset)">
        <?python
            plural=""
            if count != 1:
                plural = "es"
        ?>
        <tr>
            <td>
                <form>
                    ${count} match${plural} found;
                    <span py:if="count == 0">No results shown</span>
                    <span py:if="count != 0">Showing ${offset + 1}-${min(offset+limit, count)}</span>
                    <span py:if="count != 0">Page: ${offset/limit + 1}
                         of ${(count+limit-1)/limit}</span>
                    <span py:if="count == 0">Page: 1 of 1</span>
             
                    <a href="${baseurl};limit=${limit};offset=${max(offset-limit, 0)}" py:if="offset != 0">
                        <img src="${cfg.staticPath}/apps/mint/images/prev.gif" alt="Previous Page" width="11" height="11" border="0" />
                    </a>
                    <a href="${baseurl};limit=${limit};offset=${offset+limit}" py:if="offset+limit &lt; count">
                        <img src="${cfg.staticPath}/apps/mint/images/next.gif" alt="Next Page" width="11" height="11" border="0" />
                    </a>
                </form>
            </td>
        </tr>
    </table>

    <div py:def="formatResults(resultset = [])" py:strip="True">
        <?python
            ##This function must be implemented in any derived class
            raise NotImplementedError
        ?>
        $resultRow(resultset)
    </div>

    <!-- results structure:
        [('id', 'data item 1' ... 'data item n'), ]
    -->
    <tbody py:def="searchResults(results=[])" py:strip="True">
        <tr py:for="i, resultset in enumerate(results)" class="${i % 2 and 'even' or 'odd'}">
            ${formatResults(resultset)}
        </tr>
    </tbody>
</html>
