<?xml version='1.0' encoding='UTF-8'?>
<?python
import time
from mint import userlevels
from mint import searcher
from mint import releasetypes
from mint.helperfuncs import truncateForDisplay
from mint.client import upstream

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
              title="New ${cfg.productName} Releases" href="http://${cfg.siteHost}${cfg.basePath}rss?feed=newReleases" />
    </head>
    <body>
        <div id="right" class="side">
            ${resourcePane()}
        </div>
            <span py:if="not spotlightData">
                <span id="findit" onclick="javascript:window.location='${cfg.basePath}help?page=user-tutorial'">
                    Check out the software appliances others have made.
                </span>
                <span id="buildit" onclick="javascript:window.location='${cfg.basePath}help?page=dev-tutorial'">
                    Make your own software appliance in three easy steps.
                </span>
            </span>

        <div py:if="spotlightData" onclick="location.href='${spotlightData['link']}'" id="spotlight">
        <div py:if="spotlightData['logo']" id="logoBox">
            <img id="applianceLogo" src="${cfg.spotlightImagesDir}/${spotlightData['logo']}"/>
        </div>
        <div id="${spotlightData['logo'] and 'textBox' or 'textBoxWide'}">
            <div id="spotlightTitle">Virtual Appliance Spotlight</div>
            <div id="applianceTitle">${spotlightData['title']}</div>
            <div id="applianceText">${spotlightData['text']}</div>
            <div id="applianceInfo">Click for more information.</div>
            <div py:if="int(spotlightData['showArchive'])" onclick="getElementById('spotlight').onclick=null; location.href='${cfg.basePath}applianceSpotlight';" class="archiveLink">Spotlight Archive</div>
        </div>
        </div>
        <div id="steps"> 
            <div id="threeEasySteps">
                <a href="${cfg.basePath}help?page=dev-tutorial">
                    <img id="getStarted" src="${cfg.staticPath}apps/mint/images/getting_started.png" width="147" height="37" alt="Get Started" />
                </a>
                <img src="${cfg.staticPath}apps/mint/images/three_easy_steps.png" width="239" height="23" alt="It's Just 3 Easy Steps" />
                <div id="stepsText">There's nothing to download. All you need is your web browser.</div>
                <img style="clear: left;" src="${cfg.staticPath}apps/mint/images/steps.jpg" alt="three steps to use rBuilder Online" />
            </div>
        </div>

        <div py:if="selectionData or activeProjects or popularProjects" id="topten">
            <div class="cssbox">
            <div class="cssbox_head"><h2>&nbsp;</h2></div>
            <div class="cssbox_body">
                <table style="width: 100%;">
                    <tr>
                        <th class="topten_header">Recommended Appliances</th>
                        <th class="topten_header">Most Popular</th>
                        <th class="topten_header">Most Active</th>
                    </tr>
                    <tr>
                        <td>
                            <ol>
                                <li py:for="project in selectionData">
                                    <a href="${project['link']}">${project['name']}</a>
                                </li>
                            </ol>
                        </td>
                        <td>
                            <ol>
                                <li py:for="project in popularProjects">
                                    <a href="http://${cfg.projectSiteHost}${cfg.basePath}project/${project[1]}/">${truncateForDisplay(project[2], maxWordLen=30)}</a>
                                </li>
                            </ol>
                        </td>
                        <td>
                            <ol>
                                <li py:for="project in activeProjects">
                                    <a href="http://${cfg.projectSiteHost}${cfg.basePath}project/${project[1]}/">${truncateForDisplay(project[2], maxWordLen=30)}</a>
                                </li>
                            </ol>
                        </td>
                    </tr>
                </table>
            </div>
        </div>
        </div>
    </body>
</html>
