<?xml version='1.0' encoding='UTF-8'?>
<?python
import time
from mint import userlevels
from mint import searcher
from mint import releasetypes
from mint.helperfuncs import truncateForDisplay

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
        <div id="steps">
            <span>
                <span id="findit" onclick="javascript:window.location='help?page=user-tutorial'">
                    Check out the software appliances others have made.
                </span>
                <span id="buildit" onclick="javascript:window.location='help?page=dev-tutorial'">
                    Make your own software appliance in three easy steps.
                </span>
            </span>

            <div id="threeEasySteps">
                <a href="/help?page=dev-tutorial">
                    <img id="getStarted" src="${cfg.staticPath}apps/mint/images/getting_started.png" width="147" height="37" alt="Get Started" />
                </a>
                <img src="${cfg.staticPath}apps/mint/images/three_easy_steps.png" width="239" height="23" alt="It's Just 3 Easy Steps" />
                <div id="stepsText">There's nothing to download. All you need is your web browser.</div>
                <img style="clear: left;" src="${cfg.staticPath}apps/mint/images/steps.jpg" alt="three steps to use rBuilder Online" />
            </div>
        </div>

        <div id="topten">
            <table style="width: 100%;">
                <tr>
                    <td><span class="topten_header">Most Popular</span>
                        <ol>
                            <li py:for="project in popularProjects">
                                <a href="http://${cfg.projectSiteHost}${cfg.basePath}project/${project[1]}/">${truncateForDisplay(project[2], maxWordLen=30)}</a>
                            </li>
                        </ol>
                    </td>
                    <td><span class="topten_header">Most Active</span>
                        <ol>
                            <li py:for="project in activeProjects">
                                <a href="http://${cfg.projectSiteHost}${cfg.basePath}project/${project[1]}/">${truncateForDisplay(project[2], maxWordLen=30)}</a>
                            </li>
                        </ol>
                    </td>
                    <td><span class="topten_header">Recent Releases&nbsp;<a href="${basePath}rss?feed=newReleases"><img src="${cfg.staticPath}apps/mint/images/rss-inline.gif" alt="RSS" /></a></span>
                        <ol py:if="releases">

                            <li py:for="release in releases">
                                <?python
                                    projectName = release[0]
                                    if projectName != release[2].getName():
                                        releaseName = truncateForDisplay(release[2].getName(), maxWords=5)
                                    else:
                                        releaseName = release[2].getTroveVersion().trailingRevision().asString()
                                    projectName = truncateForDisplay(projectName, maxWords=5)
                                ?>
                                <a href="http://${cfg.projectSiteHost}${cfg.basePath}project/${release[1]}/release?id=${release[2].getId()}">${projectName} <span style="font-size: smaller">${releaseName} (${release[2].getArch()} ${releasetypes.typeNamesShort[release[2].imageTypes[0]]})</span></a>
                            </li>
                        </ol>
                    </td>
                </tr>
            </table>
        </div>
    </body>
</html>
