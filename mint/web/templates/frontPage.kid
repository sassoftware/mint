<?xml version='1.0' encoding='UTF-8'?>
<?python
import time
from mint import userlevels
from mint import searcher
from mint import buildtypes
from mint.helperfuncs import truncateForDisplay
from mint.client import upstream
from mint.web.templatesupport import projectText
?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Front Page')}</title>
        <link py:if="cfg.newsRssFeed" rel="alternate" type="application/rss+xml"
              title="${cfg.productName} Site Announcements" href="${cfg.newsRssFeed}" />
        <link rel="alternate" type="application/rss+xml"
              title="New ${cfg.productName} Projects" href="http://${cfg.siteHost}${cfg.basePath}rss?feed=newProjects" />
        <link rel="alternate" type="application/rss+xml"
              title="New ${cfg.productName} Releases" href="http://${cfg.siteHost}${cfg.basePath}rss?feed=newReleases" />
    </head>
    <body>
        <div class="fullpage">
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
        
            <div id="right" class="side">
                ${resourcePane()}
            </div>
            <div id="frontPageBlockContainer">
                <div py:if="frontPageBlock">
                    <!-- Marketing block start -->
                    ${XML(frontPageBlock)}
                    <!-- Marketing block end -->
                </div>
                <img py:if="not frontPageBlock" src="${cfg.staticPath}/apps/mint/images/default-splash.jpg" />
            </div>
            <br class="clear" />
            <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"></div>
        </div>
        <div class="spacer"></div>
        <div class="fullpage_blue">
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_blue_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_blue_topright.png" alt="" />
        
            <div py:if="selectionData or topProjects or popularProjects" id="topten">
                <div class="cssbox_body">
                    <table class="topten_table" style="width: 100%;">
                    <tr>
                        <th py:if="selectionData" class="topten_header_recommended">Recommended Appliances</th>
                        <th class="topten_header_popular">Most Popular</th>
                        <th class="topten_header_top">Top ${projectText().title()}s</th>
                        <th py:if="not selectionData" class="topten_header_recent">Recent Releases</th>
                    </tr>
                    <tr>
                        <td py:if="selectionData">
                        <ul type="none">
                            <li py:for="project in selectionData">
                            <a href="${project['link']}">${project['name']}</a> </li>
                        </ul>
                        </td>
                        
                        <td>
                        <ul type="none">
                            <li py:for="project in popularProjects">
                            <a href="http://${cfg.projectSiteHost}${cfg.basePath}project/${project['hostname']}/">
                                ${truncateForDisplay(project['name'], maxWordLen=30)}
                            </a></li>
                        </ul>
                        </td>
                        
                        <td>
                        <ul type="none">
                            <li py:for="project in topProjects">
                            <a href="http://${cfg.projectSiteHost}${cfg.basePath}project/${project['hostname']}/">
                                ${truncateForDisplay(project['name'], maxWordLen=30)}
                            </a></li>
                        </ul>
                        </td>
                        
                        <td py:if="not selectionData">
                        <p py:if="not publishedReleases">No releases have been published yet.</p>
                        <ul type="none" py:if="publishedReleases">
                            <li py:for="releaseInfo in publishedReleases">
                            <?python
                                projectName, hostname, release = releaseInfo
                                releaseName = release.name
                                shorterReleaseName = truncateForDisplay(releaseName, maxWords=8)
                            ?>
                            <a href="http://${cfg.projectSiteHost}${cfg.basePath}project/${hostname}/release?id=${release.id}" title="${releaseName}">${shorterReleaseName}<span py:if="release.version" style="font-size: smaller;"> (Version ${release.version})</span></a></li>
                         </ul>
                         </td>
                    </tr>
                    </table>
                </div>
            </div><br class="clear" />
            <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_blue_bottomleft.png" alt="" />
            <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_blue_bottomright.png" alt="" />
            <div class="bottom"></div>
        </div>
    </body>
</html>
