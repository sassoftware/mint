<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
import time
from mint import searcher
?>
<html
      xmlns:py="http://purl.org/kid/ns#"
      xmlns:html="http://www.w3.org/1999/xhtml"
      py:extends="'library.kid', 'layout.kid', 'project.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <head/>
    <body>
        <td>
            <table border="0" cellspacing="0" cellpadding="0" summary="layout" width="100%">
                <tr>
                    <td id="left" class="side">
                        <div class="pad">
                            <div id="browse" class="palette">
                                <h3>browse rpath</h3>
                                <ul>
                                    <li><a href="projects">All Projects</a></li>
                                    <li><a href="#">Most Active Projects</a></li>
                                    <li><a href="#">Most Popular Projects</a></li>
                                    <li><a href="users">All People</a></li>
                                </ul>
                            </div>
                            <div id="search" class="palette">
                                <h3>search rpath</h3>
                                <form name="search" action="search" method="get">
                                    <p>
                                        <label>search type:</label><br/>
                                        <select name="type">
                                            <option selected="selected" value="Projects">Search projects</option>
                                            <option value="Users">Search users</option>
                                        </select>
                                    </p>
                                    <p>
                                        <label>keyword(s):</label><br/>
                                        <input type="text" name="search" size="10" />
                                    </p>
                                    <p>
                                        <label>last modified:</label>
                                        <br/>
                                        <select name="modified">
                                            <option py:for="i, option in enumerate(searcher.datehtml)" value="${i}">${option}</option>
                                        </select>
                                    </p>
                                    <p><button>Submit</button><br /><a href="#">advanced search</a></p>
                                </form>
                            </div>
                        </div>
                    </td>
                    <td id="main">
                        <div class="pad">
                            <h3>Welcome to rpath</h3>
                            <p>ED FIXME: A short paragraph describing the rpath.com service.</p>
                            <p>ED FIXME: A short paragraph mentioning rpath's products.</p>
                            <p><a href="#">More about rpath</a> </p>

                            <div py:strip="True" py:if="news">
                                <?python
                                    latestNews = news.pop()
                                ?>

                                <h3>Latest News <span class="date">- ${time.ctime(latestNews['pubDate'])}</span></h3>
                                <p>${latestNews['content']}</p>
                                <p><a href="${latestNews['link']}">continued</a></p>

                                <div py:strip="True" py:if="news">
                                    <h3>More News</h3>
                                    <ul>
                                        <li py:for="item in news">
                                            <span class="date">${time.ctime(item['pubDate'])}</span><br />
                                            <a href="${item['link']}">${item['content']}</a>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </td>
                    ${projectsPane()}
                </tr>
            </table>
        </td>
    </body>
</html>
