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
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Front Page')}</title>
    </head>
    <body>
        <td>
            <table border="0" cellspacing="0" cellpadding="0" summary="layout" width="100%">
                <tr>
                    <td id="left" class="side">
                        <div class="pad">
                            ${browseMenu()}
                            ${searchMenu()}
                            ${rPathProductsMenu()}
                        </div>
                    </td>
                    <td id="main">
                        <div class="pad">
                            <h2 class="header">Welcome to rBuilder Online</h2>
                            <p>Welcome to rBuilder Online&#8212;the site for collaborative open source development.</p>
<p>Developers can create and host projects and operating systems here, while users can browse and download projects and operating system images for installation.</p>
                            <p><a href="/help?page=overview"><b>Overview of rBuilder Online</b></a></p>

                            <div py:strip="True" py:if="news">
                                <h2 class="header">Site Announcements</h2>
                                <div py:for="item in news" class="newsItem">
                                    <h3>
                                        <span class="date" style="float: right;">${time.ctime(item['pubDate'])}</span>
                                        <span class="newsTitle">${item['title']}</span>
                                    </h3>
                                    <p>${item['content']} <a class="newsContinued" href="${item['link']}">read more</a></p>
                                </div>
                                <p><a href="${newsLink}">More Announcements</a></p>
                            </div>
                        </div>
                    </td>
                    ${projectsPane()}
                </tr>
            </table>
        </td>
    </body>
</html>
