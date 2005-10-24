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
        <link rel="alternate" type="application/rss+xml"
              title="New ${cfg.productName} ISO Releases" href="http://${cfg.siteHost}${cfg.basePath}rss?feed=newReleases" />
    </head>
    <body>
        <td>
            <table border="0" cellspacing="0" cellpadding="0" summary="layout" width="100%">
                <tr>
                    <td id="left" class="side">
                        <div class="pad">
                            ${browseMenu()}
                            ${searchMenu()}
                            ${recentReleasesMenu(releases)}
                            ${rPathProductsMenu()}
                        </div>
                    </td>
                    <td id="main">
                        <div class="pad">
                            <h2 class="header">Welcome to ${cfg.productName}<sup class="tm">TM</sup></h2>


                            <div py:if="not firstTime">

                              <p>You can use ${cfg.productName} to create a
                              Linux distribution that meets your specific
                              needs, or to find an existing distribution
                              that is just right for you.</p>

                            <table id="tasks">
                                <tr>
                                    <td id="tasksBlock" style="margin-right: 1em;"
                                        onclick="javascript:window.location='${cfg.basePath}help?page=dev-help';">
                                        <h3><a href="${cfg.basePath}help?page=dev-help">Create</a></h3>

                                          <p>Use ${cfg.productName}'s collaborative
                                          development environment to package open
                                          source software and produce complete
                                          distributions.</p>
                                    </td>
                                    <td id="spacer"></td>
                                    <td id="tasksBlock"
                                        onclick="javascript:window.location='${cfg.basePath}help?page=user-help';">
                                        <h3><a href="${cfg.basePath}help?page=user-help">Find</a></h3>

                                          <p>Locate and download the distribution that
                                          suits you, or find a package to add to your
                                          system&#8212;${cfg.productName} makes it
                                          easy.</p>

                                    </td>
                                </tr>
                            </table>

                            <p><b>Want to learn more? <a href="${cfg.basePath}help?page=overview">Go here</a></b></p>

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
