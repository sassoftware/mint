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
        <link py:if="cfg.newsRssFeed" rel="alternate" type="application/rss+xml"
              title="${cfg.productName} Site Announcements" href="${cfg.newsRssFeed}" />
    </head>
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
                            <h2 class="header">Welcome to ${cfg.productName}</h2>
                            <div py:if="not firstTime">
                              <p>Welcome to ${cfg.productName} at ${cfg.siteDomainName}
                              </p>

                              <p>
                              Modify the file templates/frontPage.kid to change these contents.
                              </p>

                              <p><b>Want to learn more?  <a
                              href="${cfg.basePath}help?page=overview">Go here</a></b></p>

                            </div>
                            <div py:if="firstTime">

                              <p>Congratulations!  Your new ${cfg.productName}
                              account is active!</p>

                              <p><b>Need some help getting started?  Go
                              <a href="${cfg.basePath}help?page=new-user">here</a></b></p>

                            </div>

                            <div py:strip="True" py:if="news">
                                <h3 class="header">
                                    <a href="${cfg.newsRssFeed}">
                                        <img style="border: none; vertical-align: middle; float: right;"
                                             src="${cfg.staticPath}apps/mint/images/xml.gif" />
                                    </a>
                                    Site Announcements
                                </h3>
                                <div py:for="item in news" class="newsItem">
                                    <h3>
                                        <span class="date" style="float: right;">${time.strftime("%A, %B %d, %Y", time.localtime(item['pubDate']))}</span>
                                        <span class="newsTitle">${item['title']}</span>
                                    </h3>
                                    <p>${XML(item['content'])} <a class="newsContinued" href="${item['link']}">read more</a></p>
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
