<?xml version='1.0' encoding='UTF-8'?>
<?python
import time
from mint import searcher
searchTypes = ['Projects', 'Users', 'Packages']
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
        <td py:for="item in resultset">
            <a py:if="type(item) == tuple"
               py:content="item[1]"
               href="${item[0]}"/>
            <div py:if="type(item) != tuple"
                 py:strip="True"
                 py:content="item"/>
        </td>
    </div>

    <div id="browse" class="palette" py:def="browseMenu()" py:strip="False">
        <h3>browse rpath</h3>
        <ul>
            <li><a href="projects">All Projects</a></li>
            <li><a href="projects?sortOrder=3">Most Active Projects</a></li>
            <li><a href="projects?sortOrder=7">Most Popular Projects</a></li>
            <li><a href="users">All People</a></li>
        </ul>
    </div>

    <div id="search" class="palette" py:def="searchMenu(selectType='Projects')" py:strip="False">
        <h3>search rpath</h3>
        <form action="search" method="get">
            <p>
                <label>search type:</label><br/>
                <select name="type" onchange="if (this.options[this.selectedIndex].value != 'Projects') {
                                                el = document.getElementById('searchModified');
                                                el.disabled = true;
                                                el.className = 'disabledInput';
                                              } else {
                                                el = document.getElementById('searchModified');
                                                el.disabled = false;
                                                el.className = '';
                                              }">
                    <option py:for="searchType in searchTypes"
                            py:attrs="{'value': searchType, 'selected': (selectType == searchType) and 'selected' or None}"
                            py:content="searchType"/>
                </select>
            </p>
            <p>
                <label>keyword(s):</label><br/>
                <input type="text" name="search" size="10" />
            </p>
            <p>
                <label>last modified:</label>
                <br/>
                <select name="modified" id="searchModified">
                    <option py:for="i, option in enumerate(searcher.datehtml)" value="${i}">${option}</option>
                </select>
            </p>
            <p><button>Submit</button><br /><a py:if="0" href="#">advanced search</a></p>
        </form>
    </div>


    <table border="0" cellspacing="0" cellpadding="0"
           summary="layout" class="pager"
           py:def="navigation(urlbase, terms, count, limit, offset)">
        <?python
            plural=""
            if count != 1:
                plural = "es"
        ?>
        <tr>
            <td>
                <form>
                    <span style="float: left;" py:if="count != 0">
                        ${count} match${plural} found for <strong>${terms}</strong>;
                        Showing ${offset + 1}-${min(offset+limit, count)};
                    </span>
                    <span style="float: right;" py:if="count != 0">
                        Showing page ${offset/limit+1} of ${(count+limit-1)/limit}

                        <a href="${urlbase};limit=${limit};offset=${max(offset-limit, 0)}" py:if="offset != 0">
                            <img src="${cfg.staticPath}/apps/mint/images/prev.gif" alt="Previous" title="Previous Page" width="11" height="11" border="0" />
                        </a>
                        <img py:if="offset == 0" src="${cfg.staticPath}/apps/mint/images/prev_disabled.gif" alt="Previous" title="No previous results" width="11" height="11" border="0"/>
                        <a href="${urlbase};limit=${limit};offset=${offset+limit}" py:if="offset+limit &lt; count">
                            <img src="${cfg.staticPath}/apps/mint/images/next.gif" alt="Next" title="Next Page" width="11" height="11" border="0" />
                        </a>
                        <img py:if="offset+limit &gt;= count" src="${cfg.staticPath}/apps/mint/images/next_disabled.gif" alt="No next page" title="No subsequent results" width="11" height="11" border="0"/>
                    </span>
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
