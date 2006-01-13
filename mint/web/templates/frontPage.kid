<?xml version='1.0' encoding='UTF-8'?>
<?python
import time
from mint import userlevels
from mint import searcher
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Front Page')}</title>
        <link py:if="cfg.newsRssFeed" rel="alternate" type="application/rss+xml"
              title="${cfg.productName} Site Announcements" href="${cfg.newsRssFeed}" />
        <link rel="alternate" type="application/rss+xml"
              title="New ${cfg.productName} Projects" href="http://${cfg.siteHost}${cfg.basePath}rss?feed=newProjects" />
        <link rel="alternate" type="application/rss+xml"
              title="New ${cfg.productName} ISO Releases" href="http://${cfg.siteHost}${cfg.basePath}rss?feed=newReleases" />
    </head>
    <body>
        <td id="left" class="side">
            <div class="pad">
                ${browseMenu()}
                ${searchMenu()}
                ${recentReleasesMenu(releases, display="block")}
                ${rPathProductsMenu()}
            </div>
        </td>
        <td id="main">
            <div class="pad">
                <h2 class="header">Welcome to ${cfg.productName}<sup class="tm">TM</sup></h2>


                <div>

                    <p py:if="firstTime">Congratulations!  Your new ${cfg.productName}
                      account is active!</p>

                    <p>You can use ${cfg.productName} to create a
                      Linux distribution that meets your specific
                      needs, or to find an existing distribution
                      that is just right for you.</p>

                  <h3 style="color:#FF7001;">Start using ${cfg.productName}. Select an option below:</h3>
                    <table id="tasks">
                        <tr>
                            <td class="tasksBlock" style="margin-right: 1em;"
                                onclick="javascript:window.location='${cfg.basePath}help?page=dev-tutorial';">
                                <h3><a href="${cfg.basePath}help?page=dev-tutorial">Create</a></h3>

                                  <p>Use ${cfg.productName}'s collaborative
                                  development environment to package open
                                  source software and produce complete
                                  distributions.</p>
                            </td>
                            <td id="spacer"></td>
                            <td class="tasksBlock"
                                onclick="javascript:window.location='${cfg.basePath}help?page=user-tutorial';">
                                <h3><a href="${cfg.basePath}help?page=user-tutorial">Find</a></h3>

                                  <p>Locate and download the distribution that
                                  suits you, or find a package to add to your
                                  system&#8212;${cfg.productName} makes it
                                  easy.</p>

                            </td>
                        </tr>
                    </table>

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
        <td id="right" class="projects">
            ${projectsPane()}
            <div class="pad">
                ${groupTroveBuilder()}
            </div>
        </td>
    </body>
</html>
