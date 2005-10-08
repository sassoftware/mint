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
        <link rel="alternate" type="application/rss+xml"
              title="New ${cfg.productName} Projects" href="http://${cfg.siteHost}${cfg.basePath}rss?feed=newProjects" />

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
                            <div py:if="not firstTime">
                              <p>Welcome to rBuilder<sup class="tm">TM</sup>
                              Online&#8212;the site for collaborative open
                              source development.  Using rBuilder Online's
                              free services:</p>

                              <p><a
                              href="/help?page=dev-help">Developers</a> can
                              use rPath's technologies to easily create
                              highly-customized Linux distributions and
                              package software using the <a
                              href="http://wiki.conary.com/">Conary</a><sup class="tm">TM</sup>
                              system software management tool.</p>

                              <p><a href="/help?page=user-help">Users</a>
                              can browse and download ISO images of
                              Conary-based distributions and update their
                              Conary-based systems using software on the
                              repositories hosted here.</p>

                              <p><b>Want to learn more?  <a
                              href="/help?page=overview">Go here</a></b></p>

                            </div>
                            <div py:if="firstTime">

                              <p>Congratulations!  Your new rBuilder Online
                              account is active!</p>

                              <p><b>Need some help getting started?  Go
                              <a href="/help?page=new-user">here</a></b></p>

                            </div>

                            <div py:strip="True" py:if="news">
                                <h2 class="header">
                                    <a href="${cfg.newsRssFeed}">
                                        <img style="border: none; vertical-align: middle; float: right;"
                                             src="${cfg.staticPath}apps/mint/images/xml.gif" />
                                    </a>
                                    Site Announcements
                                </h2>
                                <div py:for="item in news" class="newsItem">
                                    <h3>
                                        <span class="date" style="float: right;">${time.ctime(item['pubDate'])}</span>
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
