<?xml version='1.0' encoding='UTF-8'?>
<?python
import time
from mint import userlevels
from mint import searcher
from mint import releasetypes
from mint.helperfuncs import truncateForDisplay
from mint.client import upstream

?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
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
    <body onload="hideElement('steps');">
        <div id="right" class="side">
            ${resourcePane()}
        </div>
        <div py:if="spotlightData" onclick="location.href='${spotlightData['link']}'" id="spotlight">
        <div class="cssbox2">
        <div class="cssbox_head2">
            <div id="spotlightTitle" style="padding-left: ${spotlightData['logo'] and '134px' or ''};">Virtual Appliance Spotlight</div>
        </div>
        <div class="cssbox_body2">
        <table>
        <tr>
        <td style="vertical-align: middle;">
            <img id="applianceImg" src="${cfg.spotlightImagesDir}/${spotlightData['logo']}"/>
        </td>
        <td>
            <div id="applianceTitle">${spotlightData['title']}</div>
            <div id="applianceText">${spotlightData['text']}</div>
            <div py:if="int(spotlightData['showArchive'])" onclick="getElementById('spotlight').onclick=null; location.href='${cfg.basePath}applianceSpotlight';" class="archiveLink">Spotlight Archive</div>
            <div id="applianceInfo">Click for more information.</div>
        </td>
        </tr>
        </table>
        </div>
        </div>
        </div>

        <br/><br/><br/>
                <div id="inactiveRight" onmouseover="underlineTitle();" onmouseout="normalTitle();" onclick="buildIt();">
                    <div id="inactiveOrangeTitle">Build it.</div>
                        Make your own software appliance in three easy steps.
                </div>
                <div id="activeLeft" >
                    <div id="orangeTitle">Use It.</div>
                    Check out the software appliances others have made.
                </div>

        <div id="applianceLogos">
           <div id="applianceLogo">
                <img id="applianceImg" src="${cfg.staticPath}apps/mint/images/img1.png"/>
            </div>
            <div id="applianceLogo">
                <img id="applianceImg" src="${cfg.staticPath}apps/mint/images/img2.png"/>
            </div>
            <div id="applianceLogo">
                <img id="applianceImg" src="${cfg.staticPath}apps/mint/images/img3.png"/>
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
                        <th py:if="selectionData" class="topten_header">Recommended Appliances</th>
                        <th class="topten_header">Most Popular</th>
                        <th class="topten_header">Most Active</th>
                        <th py:if="not selectionData" class="topten_header">Recent Releases</th>
                    </tr>
                    <tr>
                        <td py:if="selectionData">
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
                        <td py:if="not selectionData">
                            <p py:if="not releases">No releases have been published yet.</p>
                            <ol py:if="releases">

                                <li py:for="release in releases">
                                    <?python
                                        projectName = release[0]
                                        if projectName != release[2].getName():
                                            releaseName = truncateForDisplay(release[2].getName(), maxWords=5)
                                        else:
                                            releaseName = upstream(release[2].getTroveVersion())
                                        projectName = truncateForDisplay(projectName, maxWords=5)
                                        trove = release[2].getTroveName() + "=" + release[2].getTroveVersion().trailingRevision().asString()
                                    ?>
                                    <a href="http://${cfg.projectSiteHost}${cfg.basePath}project/${release[1]}/release?id=${release[2].getId()}" title="${trove}">${projectName} <span style="font-size: smaller">${releaseName} (${release[2].getArch()} ${releasetypes.typeNamesShort[release[2].imageTypes[0]]})</span></a>
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
