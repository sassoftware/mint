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
${browseMenu()}
${searchMenu()}
                        </div>
                    </td>
                    <td id="main">
                        <div class="pad">
                            <h3>Welcome to rpath</h3>
                            <p>Welcome to rpath.org &#8212; the site for collaborative open source development.</p>
<p>Developers can create and host projects and operating systems here, while users can browse and download projects and operating system images for installation.</p>
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
